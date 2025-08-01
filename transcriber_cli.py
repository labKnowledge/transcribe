#!/usr/bin/env python3
"""
Command-line interface for YouTube video transcription.
Uses the core YouTubeTranscriber class.
"""

import argparse
import sys
from transcriber_core import YouTubeTranscriber


def main():
    parser = argparse.ArgumentParser(description='Transcribe YouTube videos using Whisper')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('-o', '--output', help='Output file path (optional)')
    parser.add_argument('-m', '--model', default='base', 
                       choices=['tiny', 'base', 'small', 'medium', 'large'],
                       help='Whisper model size (default: base)')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Initialize transcriber
    transcriber = YouTubeTranscriber(model_size=args.model)
    
    def progress_callback(message):
        if args.verbose:
            print(f"[INFO] {message}")
    
    print(f"Starting transcription of: {args.url}")
    print(f"Using Whisper model: {args.model}")
    print("-" * 50)
    
    # Transcribe
    result = transcriber.transcribe_youtube_url(args.url, progress_callback)
    
    if result['success']:
        print("\n✅ Transcription completed successfully!")
        print("-" * 50)
        print(result['transcription'])
        print("-" * 50)
        
        # Save to file if specified
        if args.output:
            if transcriber.save_transcription(result['transcription'], args.output):
                print(f"✅ Transcription saved to: {args.output}")
            else:
                print(f"❌ Failed to save transcription to: {args.output}")
                sys.exit(1)
        else:
            # Save with default name
            default_filename = f"transcription_{args.url.split('v=')[-1]}.txt"
            if transcriber.save_transcription(result['transcription'], default_filename):
                print(f"✅ Transcription saved to: {default_filename}")
            else:
                print(f"❌ Failed to save transcription to: {default_filename}")
                sys.exit(1)
    else:
        print(f"\n❌ Transcription failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main() 