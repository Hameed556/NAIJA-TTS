import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils import validate_text_length, estimate_audio_duration, cleanup_old_files
from app.config import settings

class TestTTSUtils:
    """Test utility functions for TTS"""
    
    def test_validate_text_length(self):
        """Test text length validation"""
        # Valid text
        assert validate_text_length("Hello world") == True
        assert validate_text_length("A" * 500) == True
        assert validate_text_length("A" * 1000) == True
        
        # Invalid text - too long
        assert validate_text_length("A" * 1001) == False
        
        # Invalid text - empty
        assert validate_text_length("") == False
        assert validate_text_length("   ") == False
        
        # Edge cases
        assert validate_text_length("A") == True
        assert validate_text_length(" A ") == True

    def test_estimate_audio_duration(self):
        """Test audio duration estimation"""
        # Empty text
        duration = estimate_audio_duration("")
        assert duration == 0.0
        
        # Single word
        duration = estimate_audio_duration("Hello")
        assert duration > 0
        assert duration < 1  # Should be less than 1 second
        
        # Normal sentence
        text = "Hello world, this is a test of the audio duration estimation."
        duration = estimate_audio_duration(text)
        assert duration > 0
        assert duration < 10  # Should be reasonable duration
        
        # Long text
        long_text = "word " * 150  # 150 words
        duration = estimate_audio_duration(long_text)
        assert duration >= 60  # Should be about 1 minute at 150 WPM
        
        # Custom WPM
        duration_slow = estimate_audio_duration("word " * 100, words_per_minute=100)
        duration_fast = estimate_audio_duration("word " * 100, words_per_minute=200)
        assert duration_slow > duration_fast

    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('os.path.getmtime')
    @patch('os.remove')
    def test_cleanup_old_files(self, mock_remove, mock_getmtime, mock_listdir, mock_exists):
        """Test cleanup of old audio files"""
        # Mock directory exists
        mock_exists.return_value = True
        
        # Mock files in directory
        mock_listdir.return_value = [
            'old_file.wav',
            'new_file.wav', 
            'other_file.txt',  # Should be ignored
            'old_file.mp3',
            'new_file.mp3'
        ]
        
        # Mock file modification times
        import time
        current_time = time.time()
        old_time = current_time - (2 * 3600)  # 2 hours ago
        new_time = current_time - (0.5 * 3600)  # 30 minutes ago
        
        def mock_getmtime_side_effect(path):
            if 'old_file' in path:
                return old_time
            else:
                return new_time
        
        mock_getmtime.side_effect = mock_getmtime_side_effect
        
        # Test cleanup with 1 hour max age
        deleted_count = cleanup_old_files("/fake/directory", max_age_hours=1)
        
        # Should delete 2 old files (old_file.wav and old_file.mp3)
        assert deleted_count == 2
        assert mock_remove.call_count == 2

    def test_cleanup_nonexistent_directory(self):
        """Test cleanup when directory doesn't exist"""
        deleted_count = cleanup_old_files("/nonexistent/directory")
        assert deleted_count == 0

class TestTTSConfig:
    """Test TTS configuration"""
    
    def test_settings_exist(self):
        """Test that all required settings exist"""
        assert hasattr(settings, 'TOKENIZER_PATH')
        assert hasattr(settings, 'WAV_TOKENIZER_CONFIG_PATH')
        assert hasattr(settings, 'WAV_TOKENIZER_MODEL_PATH')
        assert hasattr(settings, 'PORT')
        assert hasattr(settings, 'HOST')
        assert hasattr(settings, 'SAMPLE_RATE')
        assert hasattr(settings, 'AVAILABLE_VOICES')
        assert hasattr(settings, 'AVAILABLE_LANGUAGES')

    def test_available_voices_structure(self):
        """Test that available voices have correct structure"""
        voices = settings.AVAILABLE_VOICES
        
        assert isinstance(voices, dict)
        assert 'female' in voices
        assert 'male' in voices
        assert isinstance(voices['female'], list)
        assert isinstance(voices['male'], list)
        
        # Check that we have some voices
        assert len(voices['female']) > 0
        assert len(voices['male']) > 0
        
        # Check that voices are strings
        for voice in voices['female']:
            assert isinstance(voice, str)
            assert len(voice) > 0
        
        for voice in voices['male']:
            assert isinstance(voice, str)
            assert len(voice) > 0

    def test_available_languages(self):
        """Test available languages"""
        languages = settings.AVAILABLE_LANGUAGES
        
        assert isinstance(languages, list)
        assert len(languages) > 0
        
        # Check for expected languages
        expected_languages = ['english', 'yoruba', 'igbo', 'hausa']
        for lang in expected_languages:
            assert lang in languages
        
        # Check that all languages are strings
        for lang in languages:
            assert isinstance(lang, str)
            assert len(lang) > 0

    def test_port_and_host_settings(self):
        """Test port and host settings"""
        assert isinstance(settings.PORT, int)
        assert settings.PORT > 0
        assert settings.PORT <= 65535
        
        assert isinstance(settings.HOST, str)
        assert len(settings.HOST) > 0

    def test_sample_rate(self):
        """Test sample rate setting"""
        assert isinstance(settings.SAMPLE_RATE, int)
        assert settings.SAMPLE_RATE > 0
        # Common sample rates
        assert settings.SAMPLE_RATE in [8000, 16000, 22050, 24000, 44100, 48000]

class TestTTSValidation:
    """Test TTS input validation logic"""
    
    def test_voice_validation(self):
        """Test voice validation against settings"""
        valid_voices = []
        for gender_voices in settings.AVAILABLE_VOICES.values():
            valid_voices.extend(gender_voices)
        
        # Test some expected voices
        expected_voices = ['idera', 'zainab', 'jude', 'tayo']
        for voice in expected_voices:
            assert voice in valid_voices, f"Voice '{voice}' should be in available voices"

    def test_language_validation(self):
        """Test language validation against settings"""
        valid_languages = settings.AVAILABLE_LANGUAGES
        
        # Test expected languages
        expected_languages = ['english', 'yoruba', 'igbo', 'hausa']
        for lang in expected_languages:
            assert lang in valid_languages, f"Language '{lang}' should be available"

class TestModelPaths:
    """Test model path configurations"""
    
    def test_model_path_format(self):
        """Test that model paths are properly formatted"""
        config_path = settings.WAV_TOKENIZER_CONFIG_PATH
        model_path = settings.WAV_TOKENIZER_MODEL_PATH
        
        assert isinstance(config_path, str)
        assert isinstance(model_path, str)
        assert len(config_path) > 0
        assert len(model_path) > 0
        
        # Check file extensions
        assert config_path.endswith('.yaml') or config_path.endswith('.yml')
        assert model_path.endswith('.ckpt') or model_path.endswith('.pt') or model_path.endswith('.pth')

    def test_tokenizer_path(self):
        """Test tokenizer path configuration"""
        tokenizer_path = settings.TOKENIZER_PATH
        
        assert isinstance(tokenizer_path, str)
        assert len(tokenizer_path) > 0
        # Should be a HuggingFace model path
        assert "/" in tokenizer_path  # Format: username/model_name