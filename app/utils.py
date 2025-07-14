import os
import uuid
import tempfile
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_temp_audio_dir() -> str:
    """Get or create temporary audio directory"""
    temp_dir = tempfile.mkdtemp(prefix="tts_audio_")
    logger.info(f"Created temporary audio directory: {temp_dir}")
    return temp_dir

def generate_audio_filename(extension: str = "wav") -> Tuple[str, str]:
    """Generate unique audio filename and full path"""
    audio_id = str(uuid.uuid4())
    filename = f"{audio_id}.{extension}"
    return audio_id, filename

def cleanup_old_files(directory: str, max_age_hours: int = 1) -> int:
    """Clean up old files and return count of deleted files"""
    deleted_count = 0
    
    if not os.path.exists(directory):
        logger.warning(f"Directory does not exist: {directory}")
        return deleted_count
    
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    
    try:
        for filename in os.listdir(directory):
            if not filename.endswith(('.wav', '.mp3', '.flac')):
                continue
                
            file_path = os.path.join(directory, filename)
            
            try:
                file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_mod_time < cutoff_time:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"Deleted old audio file: {filename}")
                    
            except (OSError, IOError) as e:
                logger.error(f"Error processing file {filename}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error during cleanup in {directory}: {e}")
    
    if deleted_count > 0:
        logger.info(f"Cleanup complete: deleted {deleted_count} files from {directory}")
    
    return deleted_count

def cleanup_single_file(file_path: str) -> bool:
    """Delete a specific file safely"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {e}")
        return False

def validate_text_input(text: str, max_length: int = 1000) -> Tuple[bool, str]:
    """Validate text input for TTS generation"""
    if not text or not text.strip():
        return False, "Text cannot be empty"
    
    if len(text.strip()) > max_length:
        return False, f"Text too long. Maximum length is {max_length} characters"
    
    # Check for potentially problematic characters
    if any(char in text for char in ['<', '>', '{', '}']):
        return False, "Text contains invalid characters"
    
    return True, "Valid"

def estimate_audio_duration(text: str, words_per_minute: int = 150) -> float:
    """Estimate audio duration in seconds based on text length"""
    word_count = len(text.split())
    if word_count == 0:
        return 0.0
    
    duration_minutes = word_count / words_per_minute
    return round(duration_minutes * 60, 2)

def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes"""
    try:
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    except OSError:
        return 0.0

def ensure_directory_exists(directory: str) -> bool:
    """Ensure directory exists, create if it doesn't"""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {e}")
        return False

def get_system_info() -> dict:
    """Get basic system information for health checks"""
    import psutil
    import platform
    
    try:
        return {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {"error": str(e)}

def format_timestamp(dt: datetime = None) -> str:
    """Format timestamp for API responses"""
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove or replace unsafe characters
    unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:95] + ext
    
    return filename

class AudioFileManager:
    """Manage temporary audio files"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or tempfile.mkdtemp(prefix="tts_")
        ensure_directory_exists(self.base_dir)
        
    def create_audio_path(self, extension: str = "wav") -> Tuple[str, str]:
        """Create a new audio file path"""
        audio_id, filename = generate_audio_filename(extension)
        file_path = os.path.join(self.base_dir, filename)
        return audio_id, file_path
    
    def cleanup_all(self) -> int:
        """Clean up all files in the managed directory"""
        return cleanup_old_files(self.base_dir, max_age_hours=0)
    
    def cleanup_old(self, max_age_hours: int = 1) -> int:
        """Clean up old files"""
        return cleanup_old_files(self.base_dir, max_age_hours)
    
    def get_file_count(self) -> int:
        """Get count of files in managed directory"""
        try:
            return len([f for f in os.listdir(self.base_dir) 
                       if f.endswith(('.wav', '.mp3', '.flac'))])
        except:
            return 0