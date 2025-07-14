# Nigerian TTS API Documentation

## Overview

The Nigerian TTS (Text-to-Speech) API provides high-quality speech synthesis for Nigerian languages and accents. It supports multiple voices and languages including English, Yoruba, Igbo, and Hausa.

## Base URL

```
Production: https://your-app-name.railway.app
Development: http://localhost:8000
```

## Authentication

Currently, no authentication is required. Rate limiting may be implemented in future versions.

## Endpoints

### GET /

Get API information and available options.

**Response:**
```json
{
  "status": "ok",
  "message": "Nigerian TTS API is running",
  "available_languages": ["english", "yoruba", "igbo", "hausa"],
  "available_voices": {
    "female": ["zainab", "idera", "regina", "chinenye", "joke", "remi"],
    "male": ["jude", "tayo", "umar", "osagie", "onye", "emma"]
  },
  "documentation": "/docs"
}
```

### POST /tts

Generate speech from text.

**Request Body:**
```json
{
  "text": "Your text here",
  "language": "english",
  "voice": "idera"
}
```

**Parameters:**
- `text` (string, required): Text to convert to speech (max 1000 characters)
- `language` (string, optional): Language for synthesis. Default: "english"
  - Available: "english", "yoruba", "igbo", "hausa"
- `voice` (string, optional): Voice to use for synthesis. Default: "idera"
  - Female voices: "zainab", "idera", "regina", "chinenye", "joke", "remi"
  - Male voices: "jude", "tayo", "umar", "osagie", "onye", "emma"

**Response (200 OK):**
```json
{
  "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=",
  "audio_url": "/audio/uuid-generated-filename.wav",
  "text": "Your text here",
  "voice": "idera",
  "language": "english",
  "duration": 2.5
}
```

**Error Responses:**

400 Bad Request:
```json
{
  "detail": "Text is required and cannot be empty"
}
```

```json
{
  "detail": "Invalid language: xyz. Available languages: english, yoruba, igbo, hausa"
}
```

```json
{
  "detail": "Invalid voice: xyz. Available voices: {female: [...], male: [...]}"
}
```

```json
{
  "detail": "Text too long. Maximum length is 1000 characters"
}
```

503 Service Unavailable:
```json
{
  "detail": "TTS model is not loaded. Please try again later."
}
```

### GET /health

Health check endpoint.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2025-07-02T10:30:00Z",
  "version": "1.0.0"
}
```

### GET /audio/{filename}

Serve generated audio files.

**Parameters:**
- `filename` (string): Audio filename returned from `/tts` endpoint

**Response:**
- 200: Audio file (WAV format)
- 404: File not found

## Usage Examples

### Python

```python
import requests
import base64

# Basic TTS request
response = requests.post('http://localhost:8000/tts', json={
    'text': 'Hello, welcome to Nigeria!',
    'language': 'english',
    'voice': 'idera'
})

if response.status_code == 200:
    data = response.json()
    
    # Save audio file
    audio_data = base64.b64decode(data['audio_base64'])
    with open('output.wav', 'wb') as f:
        f.write(audio_data)
    
    print(f"Audio generated successfully!")
    print(f"Duration: {data['duration']} seconds")
else:
    print(f"Error: {response.json()}")
```

### JavaScript

```javascript
// Basic TTS request
fetch('http://localhost:8000/tts', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        text: 'Sannu da zuwa Najeriya!',
        language: 'hausa',
        voice: 'umar'
    })
})
.then(response => response.json())
.then(data => {
    if (data.audio_base64) {
        // Create audio element
        const audio = new Audio();
        audio.src = `data:audio/wav;base64,${data.audio_base64}`;
        audio.play();
        
        console.log(`Audio generated for: ${data.text}`);
        console.log(`Voice: ${data.voice}, Language: ${data.language}`);
    }
})
.catch(error => console.error('Error:', error));
```

### cURL

```bash
# Basic TTS request
curl -X POST "http://localhost:8000/tts" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Ndewo, nno na Nigeria!",
       "language": "igbo",
       "voice": "chinenye"
     }'

# Health check
curl -X GET "http://localhost:8000/health"
```

## Rate Limits

Currently no rate limits are enforced, but this may change in production. Recommended usage:

- Maximum 60 requests per minute per IP
- Maximum text length: 1000 characters
- Avoid concurrent requests from the same client

## Error Handling

The API uses standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found (audio file not found)
- `422` - Validation Error (malformed request)
- `500` - Internal Server Error
- `503` - Service Unavailable (model not loaded)

All error responses include a `detail` field with a human-readable error message.

## Audio Format

- **Format**: WAV (PCM)
- **Sample Rate**: 24kHz
- **Channels**: Mono
- **Bit Depth**: 16-bit

## Supported Languages & Voices

### English
- **Female