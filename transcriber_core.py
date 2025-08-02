import os
import tempfile
import yt_dlp
import whisper
from pydub import AudioSegment
import re
from typing import Optional, Dict, Any


class YouTubeTranscriber:
    """
    Core transcriber class that handles YouTube video transcription.
    Can be used independently of any UI framework.
    """
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize the transcriber.
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
        """
        self.whisper_model = None
        self.model_size = model_size
        self.temp_files = []
        
    def transcribe_youtube_url(self, url: str, progress_callback=None) -> Dict[str, Any]:
        """
        Transcribe a YouTube video from its URL.
        
        Args:
            url: YouTube video URL
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary containing transcription result and metadata
        """
        try:
            # Validate URL
            if not self._is_valid_youtube_url(url):
                return {
                    'success': False,
                    'error': 'Invalid YouTube URL',
                    'transcription': None
                }
            
            # Download audio
            if progress_callback:
                progress_callback("Downloading audio...")
            
            audio_path = self._download_audio(url)
            if not audio_path:
                return {
                    'success': False,
                    'error': 'Failed to download audio',
                    'transcription': None
                }
            
            # Convert to WAV (or use original if too large)
            if progress_callback:
                progress_callback("Processing audio...")
            
            processed_audio_path = self._convert_to_wav(audio_path)
            if not processed_audio_path:
                return {
                    'success': False,
                    'error': 'Failed to process audio',
                    'transcription': None
                }
            
            # Transcribe with Whisper
            if progress_callback:
                progress_callback("Transcribing with Whisper...")
            
            transcription = self._transcribe_audio(processed_audio_path, progress_callback)
            
            # Clean up temporary files
            files_to_clean = [audio_path]
            if processed_audio_path != audio_path:
                files_to_clean.append(processed_audio_path)
            self._cleanup_temp_files(files_to_clean)
            
            if transcription and transcription.strip():
                return {
                    'success': True,
                    'transcription': transcription.strip(),
                    'url': url,
                    'model_used': self.model_size,
                    'video_info': getattr(self, 'video_info', {})
                }
            else:
                return {
                    'success': False,
                    'error': 'No speech detected in the audio',
                    'transcription': None
                }
                
        except Exception as e:
            # Clean up any temporary files
            self._cleanup_temp_files()
            return {
                'success': False,
                'error': str(e),
                'transcription': None
            }
    
    def _is_valid_youtube_url(self, url: str) -> bool:
        """Check if the URL is a valid YouTube URL."""
        youtube_regex = (
            r'(https?://)?(www\.)?'
            '(youtube|youtu|youtube-nocookie)\.(com|be)/'
            '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
        return bool(re.match(youtube_regex, url))
    
    def _download_audio(self, url: str) -> Optional[str]:
        """Download audio from YouTube video."""
        # Store video info for later use
        self.video_info = {}
        
        # Try multiple approaches to download the audio
        approaches = [
            # Approach 1: Standard with headers
            {
                'format': 'bestaudio/best',
                'outtmpl': '%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate',
                },
                'retries': 5,
                'fragment_retries': 5,
                'skip_unavailable_fragments': True,
            },
            # Approach 2: Different format and no postprocessing
            {
                'format': 'worstaudio/worst',
                'outtmpl': '%(title)s.%(ext)s',
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                },
                'retries': 3,
            },
            # Approach 3: Minimal options
            {
                'format': 'bestaudio',
                'outtmpl': '%(title)s.%(ext)s',
                'retries': 2,
            }
        ]
        
        for i, ydl_opts in enumerate(approaches, 1):
            try:
                print(f"Trying download approach {i}...")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    audio_path = ydl.prepare_filename(info)
                    
                    # Store video info
                    self.video_info = {
                        'title': info.get('title', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'thumbnail': info.get('thumbnail', ''),
                        'uploader': info.get('uploader', 'Unknown'),
                        'view_count': info.get('view_count', 0),
                        'upload_date': info.get('upload_date', ''),
                        'description': info.get('description', '')[:200] + '...' if info.get('description') else ''
                    }
                    
                    # If we used postprocessors, the file will be mp3
                    if 'postprocessors' in ydl_opts:
                        audio_path = os.path.splitext(audio_path)[0] + '.mp3'
                    
                    # Check if file exists
                    if os.path.exists(audio_path):
                        print(f"Successfully downloaded with approach {i}")
                        self.temp_files.append(audio_path)
                        return audio_path
                    else:
                        print(f"File not found after approach {i}")
                        
            except Exception as e:
                print(f"Approach {i} failed: {e}")
                continue
        
        print("All download approaches failed")
        return None
    
    def _convert_to_wav(self, audio_path: str) -> Optional[str]:
        """Convert audio file to WAV format."""
        try:
            # Check file size first
            file_size = os.path.getsize(audio_path)
            max_size = 4 * 1024 * 1024 * 1024  # 4GB
            
            if file_size > max_size:
                print(f"File too large ({file_size / (1024**3):.2f}GB). Using direct transcription.")
                # For large files, try to transcribe directly without conversion
                return audio_path
            
            # Determine file format from extension
            file_ext = os.path.splitext(audio_path)[1].lower()
            
            # Load audio file based on format
            if file_ext == '.mp3':
                audio = AudioSegment.from_mp3(audio_path)
            elif file_ext == '.m4a':
                audio = AudioSegment.from_file(audio_path, format='m4a')
            elif file_ext == '.webm':
                audio = AudioSegment.from_file(audio_path, format='webm')
            elif file_ext == '.ogg':
                audio = AudioSegment.from_file(audio_path, format='ogg')
            else:
                # Try to auto-detect format
                audio = AudioSegment.from_file(audio_path)
            
            # Create temporary WAV file
            wav_path = tempfile.mktemp(suffix='.wav')
            audio.export(wav_path, format='wav')
            
            self.temp_files.append(wav_path)
            return wav_path
            
        except Exception as e:
            print(f"Error converting audio: {e}")
            # If conversion fails, try to use the original file
            print("Attempting to transcribe original file directly...")
            return audio_path
    
    def _transcribe_audio(self, audio_path: str, progress_callback=None) -> Optional[str]:
        """Transcribe audio using Whisper locally with streaming support."""
        try:
            # Load Whisper model only if not already loaded or model size changed
            if self.whisper_model is None:
                print(f"Loading Whisper model '{self.model_size}'...")
                if progress_callback:
                    progress_callback(f"Loading Whisper model '{self.model_size}'...")
                self.whisper_model = whisper.load_model(self.model_size)
                print(f"Whisper model '{self.model_size}' loaded successfully")
            else:
                print(f"Using cached Whisper model '{self.model_size}'")
            
            print("Starting transcription with Whisper...")
            
            # Send initial progress
            if progress_callback:
                progress_callback("Processing audio with Whisper...")
            
            # Transcribe the audio with timestamps for streaming
            result = self.whisper_model.transcribe(
                audio_path,
                language="en",  # Specify language for better accuracy
                fp16=False,     # Use CPU for compatibility
                verbose=True,   # Show progress
                word_timestamps=True  # Get word-level timestamps for streaming
            )
            
            # Process segments for streaming
            if "segments" in result and result["segments"]:
                full_transcription = ""
                total_segments = len(result["segments"])
                
                # Send progress update
                if progress_callback:
                    progress_callback(f"Found {total_segments} segments, streaming...")
                
                # Send segments immediately as they're available
                for i, segment in enumerate(result["segments"]):
                    segment_text = segment["text"].strip()
                    if segment_text:
                        full_transcription += segment_text + " "
                        
                        # Send segment immediately via progress callback
                        if progress_callback:
                            segment_message = {
                                "type": "transcription_segment",
                                "text": segment_text,
                                "start": segment["start"],
                                "end": segment["end"],
                                "segment_number": i + 1,
                                "total_segments": total_segments
                            }
                            print(f"[DEBUG] Sending transcription segment: {segment_message}")
                            progress_callback(segment_message)
                
                transcription = full_transcription.strip()
                
                if transcription:
                    print("Transcription completed successfully")
                    return transcription
                else:
                    print("Whisper returned empty transcription")
                    return None
            else:
                # Fallback to simple transcription
                transcription = result["text"].strip()
                if transcription:
                    print("Transcription completed successfully")
                    return transcription
                else:
                    print("Whisper returned empty transcription")
                    return None
                
        except Exception as e:
            print(f"Whisper transcription error: {e}")
            return None
    
    def _cleanup_temp_files(self, files: Optional[list] = None):
        """Clean up temporary files."""
        files_to_clean = files if files is not None else self.temp_files
        
        for file_path in files_to_clean:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Cleaned up: {file_path}")
            except Exception as e:
                print(f"Error cleaning up {file_path}: {e}")
        
        # Clear the temp files list
        if files is None:
            self.temp_files.clear()
    
    def save_transcription(self, transcription: str, file_path: str) -> bool:
        """
        Save transcription to a file.
        
        Args:
            transcription: The transcription text
            file_path: Path where to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(transcription)
            
            print(f"Transcription saved to: {file_path}")
            return True
            
        except Exception as e:
            print(f"Error saving transcription: {e}")
            return False
    
    def get_available_models(self) -> list:
        """Get list of available Whisper model sizes."""
        return ['tiny', 'base', 'small', 'medium', 'large']
    
    def change_model(self, model_size: str):
        """Change the Whisper model size."""
        if model_size in self.get_available_models():
            self.model_size = model_size
            self.whisper_model = None  # Will be reloaded on next use
            print(f"Model changed to: {model_size}")
        else:
            raise ValueError(f"Invalid model size. Available: {self.get_available_models()}")


# Example usage (for testing)
if __name__ == "__main__":
    transcriber = YouTubeTranscriber()
    
    # Example URL
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    def progress_callback(message):
        print(f"Progress: {message}")
    
    result = transcriber.transcribe_youtube_url(url, progress_callback)
    
    if result['success']:
        print("Transcription successful!")
        print(result['transcription'])
        
        # Save to file
        transcriber.save_transcription(result['transcription'], 'output.txt')
    else:
        print(f"Transcription failed: {result['error']}") 