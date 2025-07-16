import os
from typing import Dict, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables at startup
load_dotenv()

class Settings:
    # API Information
    API_NAME: str = "Nigerian TTS API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "FastAPI-based Text-to-Speech API for Nigerian languages and accents"
    
    # Model configuration
    TOKENIZER_PATH: str = os.getenv("TOKENIZER_PATH", "saheedniyi/YarnGPT")
    WAV_TOKENIZER_CONFIG_PATH: str = os.getenv(
        "WAV_TOKENIZER_CONFIG_PATH", 
        "wavtokenizer_mediumdata_frame75_3s_nq1_code4096_dim512_kmeans200_attn.yaml"
    )
    WAV_TOKENIZER_MODEL_PATH: str = os.getenv(
        "WAV_TOKENIZER_MODEL_PATH", 
        "wavtokenizer_large_speech_320_24k.ckpt"
    )
    
    # Model information
    MODEL_SIZE: str = "366M"
    MODEL_TENSOR_TYPE: str = "BF16"
    BASE_MODEL: str = "HuggingFaceTB/SmolLM2-360M"
    
    # Download URLs for model files
    MODEL_CONFIG_URL: str = os.getenv(
        "MODEL_CONFIG_URL", 
        "https://huggingface.co/novateur/WavTokenizer-medium-speech-75token/resolve/main/wavtokenizer_mediumdata_frame75_3s_nq1_code4096_dim512_kmeans200_attn.yaml"
    )
    MODEL_CHECKPOINT_URL: str = os.getenv(
        "MODEL_CHECKPOINT_URL", 
        "https://huggingface.co/Hameed13/nigerian-tts-model/resolve/main/wavtokenizer_large_speech_320_24k.ckpt"
    )

    # CORS settings
    CORS_ORIGINS: list = ["*"]  # Allow all origins by default
    CORS_METHODS: list = ["GET", "POST", "OPTIONS"]
    CORS_HEADERS: list = ["*"]
    
    # Server configuration
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Audio settings
    SAMPLE_RATE: int = int(os.getenv("SAMPLE_RATE", "24000"))  # Documentation specifies 24Khz
    SILENCE_TOKEN: int = 453  # Token used for silence in audio generation
    SILENCE_DURATION: int = 20  # Number of tokens for 0.25s silence
    CHUNK_WORD_LIMIT: int = int(os.getenv("CHUNK_WORD_LIMIT", "25"))
    MAX_TEXT_LENGTH: int = int(os.getenv("MAX_TEXT_LENGTH", "1000"))
    
    # TTS Generation settings
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
    REPETITION_PENALTY: float = float(os.getenv("REPETITION_PENALTY", "1.1"))
    MAX_LENGTH: int = int(os.getenv("MAX_LENGTH", "4000"))
    DEFAULT_VOICE: str = "idera"  # Documentation mentions idera as default and best voice
    
    # Available voices and languages
    AVAILABLE_VOICES: Dict[str, List[str]] = {
        "female": ["zainab", "idera", "regina", "chinenye", "joke", "remi"],
        "male": ["jude", "tayo", "umar", "osagie", "onye", "emma"]
    }
    # To support the documented languages:
    AVAILABLE_LANGUAGES: List[str] = ["english", "yoruba", "igbo", "hausa"]
    
    # PyTorch settings
    TORCH_HOME: str = os.getenv("TORCH_HOME", "/tmp/torch_cache")
    TORCH_DTYPE: str = "auto"  # As used in documentation
    
    # File paths
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def all_voices(self) -> List[str]:
        """Get all available voices as a flat list"""
        return self.AVAILABLE_VOICES["female"] + self.AVAILABLE_VOICES["male"]
    
    @property
    def model_files_exist(self) -> bool:
        """Check if required model files exist"""
        return (
            Path(self.WAV_TOKENIZER_CONFIG_PATH).exists() and 
            Path(self.WAV_TOKENIZER_MODEL_PATH).exists()
        )
    
    @property
    def can_download_models(self) -> bool:
        """Check if model download URLs are available"""
        return bool(self.MODEL_CONFIG_URL and self.MODEL_CHECKPOINT_URL)
    
    def get_model_info(self) -> Dict[str, str]:
        """Get model file information"""
        return {
            "config_path": self.WAV_TOKENIZER_CONFIG_PATH,
            "model_path": self.WAV_TOKENIZER_MODEL_PATH,
            "config_exists": Path(self.WAV_TOKENIZER_CONFIG_PATH).exists(),
            "model_exists": Path(self.WAV_TOKENIZER_MODEL_PATH).exists(),
            "config_url": self.MODEL_CONFIG_URL,
            "model_url": self.MODEL_CHECKPOINT_URL,
            "model_size": self.MODEL_SIZE,
            "tensor_type": self.MODEL_TENSOR_TYPE,
            "base_model": self.BASE_MODEL
        }

# Create global settings instance
settings = Settings()

# Ensure required directories exist
Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.TORCH_HOME).mkdir(parents=True, exist_ok=True)