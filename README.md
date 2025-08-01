# YouTube Video Transcriber

A Python application that can transcribe YouTube videos directly from their URLs using speech recognition. Built with Tkinter for a simple GUI interface and containerized with Docker for maximum isolation and portability.

## Features

- 🎥 Direct YouTube video transcription
- 🎵 Automatic audio extraction and conversion
- 🗣️ Speech recognition using Whisper (local, no internet required)
- 💾 Save transcriptions to text files
- 🌐 Modern web interface with Server-Sent Events (SSE) streaming transcription
- 🖥️ Desktop GUI application
- 💻 Command-line interface
- ⚡ Fast processing with threading
- 🧹 Automatic cleanup of temporary files
- 🐳 Fully containerized with Docker
- 🔒 Isolated environment for security
- 🔧 Modular architecture (core functionality separate from UI)

## Prerequisites

- Docker and Docker Compose installed
- Internet connection (for downloading YouTube videos and Whisper model)
- X11 forwarding support (for GUI on Linux)

## Installation

1. Clone or download this repository
2. Build the Docker image:
```bash
docker-compose build
```

3. Set up X11 forwarding (Linux):
```bash
xhost +local:docker
```

## Usage

### Web Application (Recommended)
1. Build and start the web application:
```bash
docker-compose up --build
```

2. Open your browser and go to: http://localhost:8081
3. Enter a YouTube URL and select your preferred Whisper model
4. Click "Start Transcription" and watch the real-time progress
5. View video preview with thumbnail and details
6. Watch transcription stream line by line with timestamps
7. Copy or download the final transcription

### Desktop GUI Application
1. Build and start the application:
```bash
docker-compose up --build
```

2. Enter a YouTube URL in the input field
3. Click "Transcribe Video" to start the transcription process
4. Wait for the transcription to complete
5. Use "Save Transcription" to save the result to a text file

### Command Line Interface
```bash
# Basic usage
python transcriber_cli.py "https://www.youtube.com/watch?v=VIDEO_ID"

# With custom output file
python transcriber_cli.py "https://www.youtube.com/watch?v=VIDEO_ID" -o output.txt

# With different model size
python transcriber_cli.py "https://www.youtube.com/watch?v=VIDEO_ID" -m small

# Verbose output
python transcriber_cli.py "https://www.youtube.com/watch?v=VIDEO_ID" -v
```



## Docker Commands

- **Build and start**: `docker-compose up --build`
- **Start (if already built)**: `docker-compose up`
- **Stop**: `docker-compose down`
- **View logs**: `docker-compose logs`
- **Rebuild**: `docker-compose build --no-cache`

## How It Works

1. **Video Download**: Uses yt-dlp to download the audio from the YouTube video
2. **Audio Conversion**: Converts the audio to WAV format using pydub
3. **Speech Recognition**: Uses Whisper locally to transcribe the audio (no internet required)
4. **Cleanup**: Automatically removes temporary files after processing

## Project Structure

```
transcribe/
├── transcriber_core.py      # Core transcription functionality
├── web_app.py              # Web application (Flask + SocketIO)
├── templates/
│   └── index.html          # Modern web UI
├── transcriber_app.py       # Desktop GUI application
├── transcriber_cli.py       # Command-line interface
├── Dockerfile              # Container definition
├── docker-compose.yml      # Container orchestration
├── requirements.txt        # Python dependencies
└── README.md              # Documentation
```

### Modular Architecture

The project is designed with a modular architecture:

- **`transcriber_core.py`**: Contains the `YouTubeTranscriber` class with all core functionality
  - Can be imported and used in other projects
  - No UI dependencies
  - Handles YouTube downloading, audio conversion, and Whisper transcription
  
- **`web_app.py`**: Modern web application using FastAPI and Server-Sent Events (SSE)
  - Real-time streaming transcription with timestamps
  - Video preview with thumbnail and metadata
  - Beautiful, responsive UI
  - Live transcription display
  - High performance and modern async architecture
  - SSE for efficient real-time streaming
  
- **`transcriber_app.py`**: Desktop GUI application using Tkinter
  - Imports and uses the core transcriber
  - Provides user-friendly interface
  
- **`transcriber_cli.py`**: Command-line interface
  - Imports and uses the core transcriber
  - Suitable for automation and scripting

## Supported YouTube URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://youtube.com/watch?v=VIDEO_ID`

## Troubleshooting

### Common Issues

1. **"Speech recognition could not understand the audio"**
   - The video might have poor audio quality
   - Try videos with clear speech
   - Check your internet connection

2. **"Failed to download audio"**
   - Check if the YouTube URL is valid
   - Ensure you have a stable internet connection
   - Some videos might be restricted

3. **FFmpeg not found**
   - Run: `conda install -c conda-forge ffmpeg -y`

### Performance Tips

- Use videos with clear speech for better accuracy
- Shorter videos process faster
- Ensure stable internet connection for speech recognition

## Dependencies

- **yt-dlp**: YouTube video downloading
- **openai-whisper**: Local speech-to-text conversion
- **pydub**: Audio file processing
- **fastapi**: Modern web framework
- **uvicorn**: ASGI server
- **websockets**: WebSocket support
- **tkinter**: GUI framework
- **ffmpeg**: Audio/video processing
- **Docker**: Containerization
- **Docker Compose**: Container orchestration

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues and enhancement requests! 