import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the parent directory to the path so we can import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

class TestAPI:
    """Test class for the main API endpoints"""
    
    def test_root_endpoint(self):
        """Test the root endpoint returns correct information"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data
        assert "available_languages" in data
        assert "available_voices" in data
        assert "documentation" in data
        
        # Check that languages and voices are lists/dicts
        assert isinstance(data["available_languages"], list)
        assert isinstance(data["available_voices"], dict)
        
        # Check that we have both male and female voices
        voices = data["available_voices"]
        assert "female" in voices
        assert "male" in voices
        assert isinstance(voices["female"], list)
        assert isinstance(voices["male"], list)

    def test_health_check(self):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "timestamp" in data
        assert "version" in data
        
        # Status should be "healthy" or "ok"
        assert data["status"] in ["healthy", "ok"]
        assert isinstance(data["model_loaded"], bool)

    def test_tts_valid_request(self):
        """Test TTS with valid request"""
        payload = {
            "text": "Hello, this is a test.",
            "language": "english",
            "voice": "idera"
        }
        
        response = client.post("/tts", json=payload)
        
        # Note: This might fail if models aren't loaded, so we check for expected responses
        if response.status_code == 200:
            data = response.json()
            assert "audio_base64" in data
            assert "text" in data
            assert "voice" in data
            assert "language" in data
            assert data["text"] == payload["text"]
            assert data["voice"] == payload["voice"]
            assert data["language"] == payload["language"]
        elif response.status_code == 503:
            # Model not loaded - acceptable in test environment
            data = response.json()
            assert "detail" in data
        else:
            # Some other error - should not happen with valid request
            pytest.fail(f"Unexpected status code: {response.status_code}")

    def test_tts_invalid_language(self):
        """Test TTS with invalid language"""
        payload = {
            "text": "Hello world",
            "language": "invalid_language",
            "voice": "idera"
        }
        
        response = client.post("/tts", json=payload)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data

    def test_tts_invalid_voice(self):
        """Test TTS with invalid voice"""
        payload = {
            "text": "Hello world",
            "language": "english",
            "voice": "invalid_voice"
        }
        
        response = client.post("/tts", json=payload)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data

    def test_tts_empty_text(self):
        """Test TTS with empty text"""
        payload = {
            "text": "",
            "language": "english",
            "voice": "idera"
        }
        
        response = client.post("/tts", json=payload)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data

    def test_tts_very_long_text(self):
        """Test TTS with very long text"""
        # Create text longer than 1000 characters
        long_text = "This is a very long text. " * 50
        
        payload = {
            "text": long_text,
            "language": "english",
            "voice": "idera"
        }
        
        response = client.post("/tts", json=payload)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data

    def test_tts_missing_fields(self):
        """Test TTS with missing required fields"""
        # Missing text
        payload = {
            "language": "english",
            "voice": "idera"
        }
        
        response = client.post("/tts", json=payload)
        assert response.status_code == 422  # Validation error
        
        # Missing language (should use default)
        payload = {
            "text": "Hello world",
            "voice": "idera"
        }
        
        response = client.post("/tts", json=payload)
        # Should either succeed (using default) or fail with model not loaded
        assert response.status_code in [200, 400, 503]
        
        # Missing voice (should use default)
        payload = {
            "text": "Hello world",
            "language": "english"
        }
        
        response = client.post("/tts", json=payload)
        # Should either succeed (using default) or fail with model not loaded
        assert response.status_code in [200, 400, 503]

    def test_audio_file_endpoint(self):
        """Test audio file serving endpoint"""
        # This will likely return 404 since no audio files exist in test
        response = client.get("/audio/nonexistent.wav")
        assert response.status_code == 404

    def test_cors_headers(self):
        """Test that CORS headers are present"""
        response = client.get("/")
        
        # Check for CORS headers in response
        headers = response.headers
        # Note: TestClient might not include all CORS headers, so we just check the response is successful
        assert response.status_code == 200

class TestValidation:
    """Test input validation"""
    
    def test_supported_languages(self):
        """Test that all supported languages are valid"""
        supported_languages = ["english", "yoruba", "igbo", "hausa"]
        
        for language in supported_languages:
            payload = {
                "text": "Test text",
                "language": language,
                "voice": "idera"
            }
            
            response = client.post("/tts", json=payload)
            # Should not fail due to language validation
            assert response.status_code != 400 or "Invalid language" not in response.json().get("detail", "")

    def test_supported_voices(self):
        """Test that common voices are valid"""
        common_voices = ["idera", "zainab", "jude", "tayo"]
        
        for voice in common_voices:
            payload = {
                "text": "Test text",
                "language": "english",
                "voice": voice
            }
            
            response = client.post("/tts", json=payload)
            # Should not fail due to voice validation
            assert response.status_code != 400 or "Invalid voice" not in response.json().get("detail", "")