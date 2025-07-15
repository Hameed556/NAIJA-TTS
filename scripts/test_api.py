#!/usr/bin/env python3
"""
Test script for the Nigerian TTS API
"""

import requests
import json
import base64
import wave
import os
import time

API_BASE_URL = "https://naija-tts.onrender.com"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the API is running.")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    print("\nTesting root endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Available languages: {data.get('available_languages', [])}")
            print(f"✅ Available voices: {data.get('available_voices', {})}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_tts_generation():
    """Test TTS generation"""
    print("\nTesting TTS generation...")
    
    payload = {
        "text": "Hello, this is a test of the Nigerian TTS system.",
        "language": "english",
        "voice": "idera"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/tts", json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Generated audio for: {data['text']}")
            print(f"✅ Voice: {data['voice']}, Language: {data['language']}")
            
            # Save audio file for testing
            if 'audio_base64' in data:
                audio_data = base64.b64decode(data['audio_base64'])
                with open("test_output.wav", "wb") as f:
                    f.write(audio_data)
                print("✅ Audio saved as test_output.wav")
                
                # Check file size
                file_size = os.path.getsize("test_output.wav")
                print(f"✅ Audio file size: {file_size} bytes")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_all_voices():
    """Test all available voices"""
    print("\nTesting available voices...")
    
    # First get available voices
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            voices = data.get('available_voices', {})
            
            all_voices = []
            if 'female' in voices:
                all_voices.extend(voices['female'][:2])  # Test first 2 female voices
            if 'male' in voices:
                all_voices.extend(voices['male'][:2])    # Test first 2 male voices
        else:
            # Fallback to default voices
            all_voices = ["idera", "zainab", "jude", "tayo"]
    except:
        all_voices = ["idera", "zainab", "jude", "tayo"]
    
    for voice in all_voices:
        payload = {
            "text": f"This is {voice} speaking from Nigeria.",
            "language": "english",
            "voice": voice
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/tts", json=payload)
            if response.status_code == 200:
                print(f"✅ {voice}: SUCCESS")
            else:
                print(f"❌ {voice}: FAILED ({response.status_code})")
        except Exception as e:
            print(f"❌ {voice}: ERROR - {e}")
        
        # Small delay between requests
        time.sleep(0.5)

def test_error_cases():
    """Test error handling"""
    print("\nTesting error cases...")
    
    # Test invalid language
    payload = {
        "text": "Hello world",
        "language": "invalid_language",
        "voice": "idera"
    }
    response = requests.post(f"{API_BASE_URL}/tts", json=payload)
    print(f"Invalid language test: {response.status_code} (should be 400)")
    
    # Test invalid voice
    payload = {
        "text": "Hello world",
        "language": "english",
        "voice": "invalid_voice"
    }
    response = requests.post(f"{API_BASE_URL}/tts", json=payload)
    print(f"Invalid voice test: {response.status_code} (should be 400)")
    
    # Test empty text
    payload = {
        "text": "",
        "language": "english",
        "voice": "idera"
    }
    response = requests.post(f"{API_BASE_URL}/tts", json=payload)
    print(f"Empty text test: {response.status_code} (should be 400)")

def cleanup_test_files():
    """Clean up test files"""
    print("\nCleaning up test files...")
    test_files = ["test_output.wav"]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"✅ Removed {file}")

if __name__ == "__main__":
    print("🚀 Nigerian TTS API Test Suite")
    print("=" * 50)
    
    # Run tests
    tests_passed = 0
    total_tests = 0
    
    # Health check
    total_tests += 1
    if test_health_check():
        tests_passed += 1
    
    # Root endpoint
    total_tests += 1
    if test_root_endpoint():
        tests_passed += 1
    
    # TTS generation
    total_tests += 1
    if test_tts_generation():
        tests_passed += 1
        
        # Only test voices if basic TTS works
        test_all_voices()
    
    # Error cases
    print("\n" + "="*30)
    test_error_cases()
    
    # Cleanup
    cleanup_test_files()
    
    # Summary
    print("\n" + "="*50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    print("="*50)