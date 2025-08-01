#!/usr/bin/env python3
"""
Test script to verify that all dependencies are properly installed
"""

def test_imports():
    """Test if all required packages can be imported"""
    print("Testing package imports...")
    
    try:
        import yt_dlp
        print("✓ yt-dlp imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import yt-dlp: {e}")
        return False
    
    try:
        import speech_recognition as sr
        print("✓ SpeechRecognition imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import SpeechRecognition: {e}")
        return False
    
    try:
        from pydub import AudioSegment
        print("✓ pydub imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import pydub: {e}")
        return False
    
    try:
        import tkinter as tk
        print("✓ tkinter imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import tkinter: {e}")
        return False
    
    try:
        import requests
        print("✓ requests imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import requests: {e}")
        return False
    
    return True

def test_ffmpeg():
    """Test if ffmpeg is available"""
    print("\nTesting FFmpeg availability...")
    
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ FFmpeg is available")
            return True
        else:
            print("✗ FFmpeg is not working properly")
            return False
    except FileNotFoundError:
        print("✗ FFmpeg not found. Please install it using: conda install -c conda-forge ffmpeg")
        return False
    except Exception as e:
        print(f"✗ Error testing FFmpeg: {e}")
        return False

def test_speech_recognition():
    """Test if speech recognition is working"""
    print("\nTesting speech recognition...")
    
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        print("✓ Speech recognition initialized successfully")
        print("Note: Internet connection required for actual transcription")
        return True
    except Exception as e:
        print(f"✗ Error initializing speech recognition: {e}")
        return False

def main():
    print("YouTube Transcriber - Setup Test")
    print("=" * 40)
    
    all_tests_passed = True
    
    # Test imports
    if not test_imports():
        all_tests_passed = False
    
    # Test FFmpeg
    if not test_ffmpeg():
        all_tests_passed = False
    
    # Test speech recognition
    if not test_speech_recognition():
        all_tests_passed = False
    
    print("\n" + "=" * 40)
    if all_tests_passed:
        print("✓ All tests passed! The transcriber app should work correctly.")
        print("\nTo run the app:")
        print("docker-compose up")
    else:
        print("✗ Some tests failed. Please check the installation.")
        print("\nTry rebuilding the Docker image: docker-compose build --no-cache")

if __name__ == "__main__":
    main() 