from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import torch
import torchaudio
import base64
from transformers import AutoModelForCausalLM
from datetime import datetime
import tempfile
import numpy as np
import io
import wave

# Try to import YarnGPT, fall back to None if not available
try:
    from yarngpt.audiotokenizer import AudioTokenizerV2
    YARNGPT_AVAILABLE = True
    print("✅ YarnGPT imported successfully")
except ImportError as e:
    print(f"⚠️  YarnGPT not available: {e}")
    print("🧪 Running in TESTING mode")
    AudioTokenizerV2 = None
    YARNGPT_AVAILABLE = False

# Import from your other files
from app.config import settings
from app.models import TTSRequest, TTSResponse, HealthResponse, VoicesResponse, LanguagesResponse, APIInfoResponse
from app.utils import (
    AudioFileManager, 
    validate_text_input, 
    estimate_audio_duration,
    get_system_info,
    cleanup_old_files
)

# Initialize FastAPI with settings from config
app = FastAPI(
    title=settings.API_NAME,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION
)

# Add CORS middleware using config
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Global variables for model
audio_tokenizer = None
model = None

# Initialize file manager
audio_manager = AudioFileManager()

# Testing mode check - True if YarnGPT not available OR explicitly set
TESTING_MODE = not YARNGPT_AVAILABLE or os.getenv("TESTING_MODE", "false").lower() == "true"

async def download_model_if_needed():
    """Download model files if they don't exist and URLs are provided"""
    if not settings.can_download_models:
        print("No model download URLs provided")
        return False
    
    import requests
    
    # Download config file
    if not os.path.exists(settings.WAV_TOKENIZER_CONFIG_PATH):
        print("Downloading config file...")
        try:
            response = requests.get(settings.MODEL_CONFIG_URL)
            response.raise_for_status()
            with open(settings.WAV_TOKENIZER_CONFIG_PATH, 'wb') as f:
                f.write(response.content)
            print("Config file downloaded!")
        except Exception as e:
            print(f"Error downloading config: {e}")
            return False
    
    # Download model file
    if not os.path.exists(settings.WAV_TOKENIZER_MODEL_PATH):
        print("Downloading model file...")
        try:
            response = requests.get(settings.MODEL_CHECKPOINT_URL, stream=True)
            response.raise_for_status()
            with open(settings.WAV_TOKENIZER_MODEL_PATH, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("Model file downloaded!")
        except Exception as e:
            print(f"Error downloading model: {e}")
            return False
    
    return True

async def load_models():
    """Load models on startup"""
    global audio_tokenizer, model
    
    if TESTING_MODE:
        print("🧪 Running in TESTING mode - no real models loaded")
        return True
    
    try:
        print("Loading YarnGPT model and tokenizer...")
        
        # Download models if needed
        if not settings.model_files_exist:
            download_success = await download_model_if_needed()
            if not download_success:
                print("❌ Failed to download models")
                return False
        
        # Load the models
        audio_tokenizer = AudioTokenizerV2(
            settings.TOKENIZER_PATH, 
            settings.WAV_TOKENIZER_MODEL_PATH, 
            settings.WAV_TOKENIZER_CONFIG_PATH
        )
        model = AutoModelForCausalLM.from_pretrained(
            settings.TOKENIZER_PATH, 
            torch_dtype="auto"
        ).to(audio_tokenizer.device)
        
        print("✅ Models loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error loading models: {str(e)}")
        print("🧪 Falling back to TESTING mode")
        return False

def create_mock_audio() -> bytes:
    """Create mock audio for testing mode"""
    # Create a simple sine wave as mock audio
    # Generate 2 seconds of sine wave
    sample_rate = getattr(settings, 'SAMPLE_RATE', 24000)
    duration = 2.0
    frequency = 440  # A4 note
    
    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
    
    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create WAV file in memory
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    buffer.seek(0)
    return buffer.read()

@app.on_event("startup")
async def startup_event():
    """Load models when the app starts"""
    success = await load_models()
    if TESTING_MODE:
        print(f"🚀 Starting {settings.API_NAME} in TESTING mode")
        print(f"🧪 YarnGPT Available: {YARNGPT_AVAILABLE}")
    else:
        print(f"🚀 Starting {settings.API_NAME} v{settings.API_VERSION}")
        if not success:
            print("⚠️  Models failed to load, but server will continue running")

@app.get("/", response_model=APIInfoResponse)
async def root():
    """API health check and info"""
    return APIInfoResponse(
        status="ok",
        message=f"{settings.API_NAME} is running",
        version=settings.API_VERSION,
        available_languages=settings.AVAILABLE_LANGUAGES,
        available_voices=settings.AVAILABLE_VOICES,
        model_loaded=model is not None or TESTING_MODE,
        testing_mode=TESTING_MODE,
        documentation="/docs"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    system_info = get_system_info()
    return HealthResponse(
        status="healthy",
        model_loaded=model is not None or TESTING_MODE,
        timestamp=datetime.now().isoformat(),
        version=settings.API_VERSION,
        uptime=system_info.get("uptime"),
        testing_mode=TESTING_MODE
    )

@app.get("/voices", response_model=VoicesResponse)
async def get_voices():
    """Get available voices"""
    return VoicesResponse(
        female=settings.AVAILABLE_VOICES["female"],
        male=settings.AVAILABLE_VOICES["male"]
    )

@app.get("/languages", response_model=LanguagesResponse)
async def get_languages():
    """Get available languages"""
    return LanguagesResponse(languages=settings.AVAILABLE_LANGUAGES)

@app.post("/generate-audio", response_model=TTSResponse)
async def generate_audio(request: TTSRequest, background_tasks: BackgroundTasks):
    """Convert text to Nigerian-accented speech"""
    
    # Validate text input using utils
    is_valid, error_msg = validate_text_input(request.text, settings.MAX_TEXT_LENGTH)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Validate language and voice
    if request.language not in settings.AVAILABLE_LANGUAGES:
        raise HTTPException(
            status_code=400, 
            detail=f"Language must be one of {settings.AVAILABLE_LANGUAGES}"
        )
    
    if request.voice not in settings.all_voices:
        raise HTTPException(
            status_code=400, 
            detail=f"Voice must be one of {settings.all_voices}"
        )
    
    # Check if models are loaded (unless in testing mode)
    if not TESTING_MODE and (model is None or audio_tokenizer is None):
        raise HTTPException(
            status_code=503, 
            detail="Models not loaded. Please wait for initialization."
        )
    
    # Generate audio file path
    audio_id, output_path = audio_manager.create_audio_path()
    
    try:
        if TESTING_MODE:
            # Create mock audio for testing
            mock_audio = create_mock_audio()
            with open(output_path, "wb") as f:
                f.write(mock_audio)
            print(f"📝 Generated mock audio for: {request.text[:50]}...")
        else:
            # Real TTS generation
            prompt = audio_tokenizer.create_prompt(
                request.text, 
                lang=request.language, 
                speaker_name=request.voice
            )
            input_ids = audio_tokenizer.tokenize_prompt(prompt)
            
            output = model.generate(
                input_ids=input_ids,
                temperature=settings.TEMPERATURE,
                repetition_penalty=settings.REPETITION_PENALTY,
                max_length=settings.MAX_LENGTH,
            )
            
            codes = audio_tokenizer.get_codes(output)
            audio = audio_tokenizer.get_audio(codes)
            
            # Save audio file
            torchaudio.save(output_path, audio, sample_rate=settings.SAMPLE_RATE)
        
        # Read and encode audio file
        with open(output_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Estimate duration
        duration = estimate_audio_duration(request.text)
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_single_file, output_path)
        background_tasks.add_task(cleanup_old_files, audio_manager.base_dir)
        
        return TTSResponse(
            audio_base64=audio_base64,
            audio_url=f"/audio/{os.path.basename(output_path)}",
            text=request.text,
            voice=request.voice,
            language=request.language,
            duration=duration,
            generated_at=datetime.now(),
            testing_mode=TESTING_MODE
        )
        
    except Exception as e:
        # Clean up file if it was created
        if os.path.exists(output_path):
            os.remove(output_path)
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating audio: {str(e)}"
        )

# ADD THE MISSING ENDPOINT - This is what you were testing!
@app.post("/generate-tts", response_model=TTSResponse)
async def generate_tts(request: TTSRequest, background_tasks: BackgroundTasks):
    """Generate TTS - Alternative endpoint name"""
    return await generate_audio(request, background_tasks)

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve audio files"""
    file_path = os.path.join(audio_manager.base_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/wav")

@app.get("/cleanup")
async def manual_cleanup():
    """Manually trigger cleanup of old files"""
    cleaned_count = audio_manager.cleanup_old()
    return {"message": f"Cleaned up {cleaned_count} old files"}

def cleanup_single_file(file_path: str):
    """Delete a specific file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️  Cleaned up file: {os.path.basename(file_path)}")
    except Exception as e:
        print(f"❌ Error cleaning up file {file_path}: {e}")

# For backward compatibility - keeping the old endpoint
@app.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest, background_tasks: BackgroundTasks):
    """Backward compatibility endpoint"""
    return await generate_audio(request, background_tasks)

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Starting {settings.API_NAME} on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=int(os.environ.get("PORT", 10000)),
        reload=settings.DEBUG
    )