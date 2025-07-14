#!/usr/bin/env python3
"""
Data models for Nigerian TTS API
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class TTSRequest(BaseModel):
    """Request model for TTS generation"""
    text: str = Field(..., description="Text to convert to speech", min_length=1, max_length=1000)
    voice: str = Field(..., description="Voice to use (idera, adunni, kemi, seun, emeka, chidi)")
    language: str = Field("english", description="Language (english, yoruba, igbo, hausa, pidgin)")
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Welcome to Nigerian TTS API",
                "voice": "idera",
                "language": "english"
            }
        }

class TTSResponse(BaseModel):
    """Response model for TTS generation"""
    audio_base64: str = Field(..., description="Base64 encoded audio data")
    audio_url: str = Field(..., description="URL to download the audio file")
    text: str = Field(..., description="Original text that was converted")
    voice: str = Field(..., description="Voice used for generation")
    language: str = Field(..., description="Language used for generation")
    duration: float = Field(..., description="Estimated duration in seconds")
    generated_at: datetime = Field(..., description="When the audio was generated")
    testing_mode: bool = Field(default=False, description="Whether this was generated in testing mode")
    
    class Config:
        schema_extra = {
            "example": {
                "audio_base64": "UklGRiQAAABXQVZFZm10IBAA...",
                "audio_url": "/audio/audio_123456.wav",
                "text": "Welcome to Nigerian TTS API",
                "voice": "idera",
                "language": "english",
                "duration": 2.5,
                "generated_at": "2024-01-01T12:00:00",
                "testing_mode": False
            }
        }

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Health status")
    model_loaded: bool = Field(..., description="Whether models are loaded")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    uptime: Optional[str] = Field(None, description="Server uptime")
    testing_mode: bool = Field(default=False, description="Whether running in testing mode")

class VoicesResponse(BaseModel):
    """Available voices response"""
    female: List[str] = Field(..., description="Available female voices")
    male: List[str] = Field(..., description="Available male voices")

class LanguagesResponse(BaseModel):
    """Available languages response"""
    languages: List[str] = Field(..., description="Available languages")

class APIInfoResponse(BaseModel):
    """API information response"""
    status: str = Field(..., description="API status")
    message: str = Field(..., description="Status message")
    version: str = Field(..., description="API version")
    available_languages: List[str] = Field(..., description="Available languages")
    available_voices: Dict[str, List[str]] = Field(..., description="Available voices by gender")
    model_loaded: bool = Field(..., description="Whether models are loaded")
    testing_mode: bool = Field(default=False, description="Whether running in testing mode")

class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(..., description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Text is too long. Maximum length is 1000 characters",
                "status_code": 400,
                "timestamp": "2024-01-01T12:00:00"
            }
        }