import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
from datetime import datetime
from transcriber_core import YouTubeTranscriber

class TranscriberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Transcriber")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize core transcriber
        self.transcriber = YouTubeTranscriber()
        self.is_transcribing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="YouTube Video Transcriber", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # URL input
        ttk.Label(main_frame, text="YouTube URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(main_frame, width=60)
        self.url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.transcribe_btn = ttk.Button(button_frame, text="Transcribe Video", 
                                        command=self.start_transcription)
        self.transcribe_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(button_frame, text="Save Transcription", 
                                  command=self.save_transcription, state='disabled')
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(button_frame, text="Clear", 
                                   command=self.clear_text)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to transcribe")
        self.status_label.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        # Text area for transcription
        ttk.Label(main_frame, text="Transcription:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.text_area = scrolledtext.ScrolledText(main_frame, width=80, height=20, 
                                                  wrap=tk.WORD, font=('Arial', 10))
        self.text_area.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
    def start_transcription(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
            
        self.is_transcribing = True
        self.transcribe_btn.config(state='disabled')
        self.progress.start()
        self.status_label.config(text="Starting transcription...")
        
        # Start transcription in a separate thread
        thread = threading.Thread(target=self.transcribe_video, args=(url,))
        thread.daemon = True
        thread.start()
        
    def transcribe_video(self, url):
        try:
            # Progress callback function
            def progress_callback(message):
                self.root.after(0, lambda: self.status_label.config(text=message))
            
            # Use the core transcriber
            result = self.transcriber.transcribe_youtube_url(url, progress_callback)
            
            # Update UI based on result
            if result['success']:
                self.root.after(0, lambda: self.update_transcription_result(result['transcription']))
            else:
                self.root.after(0, lambda: self.handle_transcription_error(result['error']))
                
        except Exception as e:
            self.root.after(0, lambda: self.handle_transcription_error(str(e)))
            
    
                
    def update_transcription_result(self, transcription):
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, transcription)
        
        self.progress.stop()
        self.status_label.config(text="Transcription completed!")
        self.transcribe_btn.config(state='normal')
        self.save_btn.config(state='normal')
        self.is_transcribing = False
        
    def handle_transcription_error(self, error_msg):
        self.progress.stop()
        self.status_label.config(text=f"Error: {error_msg}")
        self.transcribe_btn.config(state='normal')
        self.is_transcribing = False
        messagebox.showerror("Transcription Error", error_msg)
        
    def save_transcription(self):
        transcription = self.text_area.get(1.0, tk.END).strip()
        if not transcription:
            messagebox.showwarning("Warning", "No transcription to save")
            return
        
        # Create transcriptions directory if it doesn't exist
        transcriptions_dir = os.path.join(os.getcwd(), "transcriptions")
        os.makedirs(transcriptions_dir, exist_ok=True)
        
        # Generate default filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"transcription_{timestamp}.txt"
        default_path = os.path.join(transcriptions_dir, default_filename)
        
        # Try to use file dialog, fallback to default path if it fails
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialdir=transcriptions_dir,
                initialfile=default_filename
            )
            
            if not file_path:  # User cancelled
                return
                
        except Exception:
            # Fallback for Docker environment
            file_path = default_path
            
        # Use the core transcriber's save method
        if self.transcriber.save_transcription(transcription, file_path):
            messagebox.showinfo("Success", f"Transcription saved to {file_path}")
        else:
            messagebox.showerror("Error", "Failed to save transcription")
                
    def clear_text(self):
        self.text_area.delete(1.0, tk.END)
        self.url_entry.delete(0, tk.END)
        self.status_label.config(text="Ready to transcribe")
        self.save_btn.config(state='disabled')

def main():
    root = tk.Tk()
    app = TranscriberApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 