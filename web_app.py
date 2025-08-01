from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import os
import json
import asyncio
import threading
from datetime import datetime
from typing import Dict, List
from transcriber_core import YouTubeTranscriber

app = FastAPI(title="YouTube Transcriber", version="1.0.0")

# Templates
templates = Jinja2Templates(directory="templates")

# Global transcriber instance
transcriber = YouTubeTranscriber()

# Store active SSE streams
active_sse_streams: Dict[str, asyncio.Queue] = {}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/stream/{client_id}")
async def stream_transcription(client_id: str):
    """Server-Sent Events endpoint for streaming transcription"""
    async def event_generator():
        print(f"[DEBUG] SSE stream started for client {client_id}")
        if client_id not in active_sse_streams:
            print(f"[DEBUG] Creating new SSE queue for client {client_id} (should not happen)")
            active_sse_streams[client_id] = asyncio.Queue()
        else:
            print(f"[DEBUG] Using existing SSE queue for client {client_id}")
        
        queue = active_sse_streams[client_id]
        
        try:
            while True:
                try:
                    # Wait for message with timeout
                    print(f"[DEBUG] Waiting for message from queue for client {client_id}")
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    print(f"[DEBUG] Received message for client {client_id}: {message}")
                    
                    # Format SSE message
                    sse_message = f"data: {json.dumps(message)}\n\n"
                    print(f"[DEBUG] Sending SSE message to client {client_id}: {sse_message.strip()}")
                    yield sse_message
                    
                    # If it's a completion message, break
                    if message.get("type") == "transcription_complete":
                        print(f"[DEBUG] Transcription complete, ending stream for client {client_id}")
                        break
                        
                except asyncio.TimeoutError:
                    # Send keepalive
                    keepalive_message = {'type': 'keepalive', 'timestamp': datetime.now().isoformat()}
                    sse_message = f"data: {json.dumps(keepalive_message)}\n\n"
                    print(f"[DEBUG] Sending keepalive to client {client_id}")
                    yield sse_message
                    
        except Exception as e:
            print(f"[DEBUG] Error in SSE stream for client {client_id}: {e}")
            error_message = {'type': 'error', 'message': str(e)}
            yield f"data: {json.dumps(error_message)}\n\n"
        finally:
            # Clean up
            if client_id in active_sse_streams:
                del active_sse_streams[client_id]
                print(f"[DEBUG] Cleaned up SSE queue for client {client_id}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.post("/api/start-transcription")
async def start_transcription(request: Request):
    """Start transcription and return SSE stream URL"""
    try:
        data = await request.json()
        url = data.get("url")
        model_size = data.get("model_size", "base")
        client_id = data.get("client_id", str(datetime.now().timestamp()))
        
        if not url:
            raise HTTPException(status_code=400, detail="No URL provided")
        
        # Create SSE queue BEFORE starting transcription
        if client_id not in active_sse_streams:
            active_sse_streams[client_id] = asyncio.Queue()
            print(f"[DEBUG] Created SSE queue for client {client_id} before starting transcription")
        
        # Start transcription in background thread
        thread = threading.Thread(
            target=run_transcription, 
            args=(client_id, url, model_size)
        )
        thread.daemon = True
        thread.start()
        
        return {
            "success": True,
            "client_id": client_id,
            "stream_url": f"/stream/{client_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_transcription(client_id: str, url: str, model_size: str):
    """Run transcription in background thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        print(f"[DEBUG] Starting transcription for client {client_id}")
        
        # Update transcriber model if needed
        if transcriber.model_size != model_size:
            transcriber.change_model(model_size)
        
        # Progress callback for real-time updates
        def progress_callback(message):
            try:
                print(f"[DEBUG] Progress callback called: {type(message)} - {message}")
                if client_id in active_sse_streams:
                    queue = active_sse_streams[client_id]
                    asyncio.run_coroutine_threadsafe(
                        queue.put(message),
                        loop
                    )
                    print(f"[DEBUG] Message sent to SSE queue for client {client_id}")
                else:
                    print(f"[DEBUG] Client {client_id} not found in active_sse_streams")
            except Exception as e:
                print(f"[DEBUG] Error sending progress message: {e}")
        
        # Send start message
        try:
            if client_id in active_sse_streams:
                queue = active_sse_streams[client_id]
                start_message = {"type": "status", "message": "Starting transcription..."}
                asyncio.run_coroutine_threadsafe(
                    queue.put(start_message),
                    loop
                )
                print(f"[DEBUG] Start message sent to client {client_id}")
        except Exception as e:
            print(f"[DEBUG] Error sending start message: {e}")
        
        # Download audio first to get video info
        print(f"[DEBUG] Starting audio download...")
        if progress_callback:
            progress_callback("Downloading audio...")
        
        audio_path = transcriber._download_audio(url)
        if not audio_path:
            print(f"[DEBUG] Audio download failed")
            try:
                if client_id in active_sse_streams:
                    queue = active_sse_streams[client_id]
                    asyncio.run_coroutine_threadsafe(
                        queue.put({"type": "error", "message": "Failed to download audio"}),
                        loop
                    )
            except Exception as e:
                print(f"[DEBUG] Error sending download error: {e}")
            return
        
        print(f"[DEBUG] Audio downloaded successfully: {audio_path}")
        
        # Send video info immediately after download
        if hasattr(transcriber, 'video_info') and transcriber.video_info:
            print(f"[DEBUG] Sending video info: {transcriber.video_info}")
            try:
                if client_id in active_sse_streams:
                    queue = active_sse_streams[client_id]
                    video_message = {"type": "video_info", "data": transcriber.video_info}
                    asyncio.run_coroutine_threadsafe(
                        queue.put(video_message),
                        loop
                    )
                    print(f"[DEBUG] Video info sent to client {client_id}")
                else:
                    print(f"[DEBUG] Client {client_id} not found when trying to send video info")
            except Exception as e:
                print(f"[DEBUG] Error sending video info: {e}")
        else:
            print(f"[DEBUG] No video info available")
        
        # Process audio
        print(f"[DEBUG] Starting audio processing...")
        if progress_callback:
            progress_callback("Processing audio...")
        
        processed_audio_path = transcriber._convert_to_wav(audio_path)
        if not processed_audio_path:
            print(f"[DEBUG] Audio processing failed")
            try:
                if client_id in active_sse_streams:
                    queue = active_sse_streams[client_id]
                    asyncio.run_coroutine_threadsafe(
                        queue.put({"type": "error", "message": "Failed to process audio"}),
                        loop
                    )
            except Exception as e:
                print(f"[DEBUG] Error sending processing error: {e}")
            return
        
        print(f"[DEBUG] Audio processed successfully: {processed_audio_path}")
        
        # Run transcription
        print(f"[DEBUG] Starting transcription...")
        result = transcriber._transcribe_audio(processed_audio_path, progress_callback)
        
        if result:
            print(f"[DEBUG] Transcription completed successfully")
            # Send final result
            try:
                if client_id in active_sse_streams:
                    queue = active_sse_streams[client_id]
                    completion_message = {"type": "transcription_complete", "data": {
                        "success": True,
                        "transcription": result,
                        "url": url,
                        "model_used": model_size,
                        "video_info": getattr(transcriber, 'video_info', {})
                    }}
                    asyncio.run_coroutine_threadsafe(
                        queue.put(completion_message),
                        loop
                    )
                    print(f"[DEBUG] Completion message sent to client {client_id}")
            except Exception as e:
                print(f"[DEBUG] Error sending completion message: {e}")
        else:
            print(f"[DEBUG] Transcription failed - no result")
            # Send error
            try:
                if client_id in active_sse_streams:
                    queue = active_sse_streams[client_id]
                    asyncio.run_coroutine_threadsafe(
                        queue.put({"type": "error", "message": "No speech detected in the audio"}),
                        loop
                    )
            except Exception as e:
                print(f"[DEBUG] Error sending error message: {e}")
                
    except Exception as e:
        print(f"[DEBUG] Exception in transcription: {e}")
        try:
            if client_id in active_sse_streams:
                queue = active_sse_streams[client_id]
                asyncio.run_coroutine_threadsafe(
                    queue.put({"type": "error", "message": str(e)}),
                    loop
                )
        except Exception as e2:
            print(f"[DEBUG] Error sending error message: {e2}")
    
    finally:
        print(f"[DEBUG] Transcription thread ending for client {client_id}")
        loop.close()

@app.post("/api/save-transcription")
async def save_transcription(request: Request):
    """Save transcription to file"""
    try:
        data = await request.json()
        transcription = data.get("transcription")
        filename = data.get("filename", f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        if not transcription:
            raise HTTPException(status_code=400, detail="No transcription to save")
        
        filepath = os.path.join('transcriptions', filename)
        
        if transcriber.save_transcription(transcription, filepath):
            return {
                "success": True,
                "filename": filename,
                "filepath": filepath
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save transcription")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
async def get_models():
    """Get available Whisper models"""
    return {
        "models": transcriber.get_available_models(),
        "current_model": transcriber.model_size
    }

@app.get("/api/transcriptions")
async def get_transcriptions():
    """Get list of saved transcriptions"""
    transcriptions_dir = 'transcriptions'
    if not os.path.exists(transcriptions_dir):
        return []
    
    files = []
    for filename in os.listdir(transcriptions_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(transcriptions_dir, filename)
            stat = os.stat(filepath)
            files.append({
                'filename': filename,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    
    return sorted(files, key=lambda x: x['modified'], reverse=True)

@app.get("/api/transcriptions/{filename}")
async def get_transcription(filename: str):
    """Get content of a specific transcription file"""
    filepath = os.path.join('transcriptions', filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Create necessary directories
    os.makedirs('transcriptions', exist_ok=True)
    
    print("Starting YouTube Transcriber Web App...")
    print("Available at: http://localhost:8081")
    
    uvicorn.run(app, host="0.0.0.0", port=8081) 