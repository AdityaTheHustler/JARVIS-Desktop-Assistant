import asyncio
import os
import sys
from dotenv import load_dotenv
from core.voice_engine import VoiceEngine
from core.conversation_manager import ConversationManager
from core.command_handler import CommandHandler
from gui.main_window import ModernCircularInterface
import threading
import queue
from utils.config import Config
import tkinter as tk
from tkinter import messagebox
import time
from datetime import datetime

# Set premium voice - choose from jason, guy, tony, davis, ryan, aria, jenny, sara
# Jason has the best pitch quality for male voice
os.environ["EDGE_VOICE"] = "jason"

class JarvisAssistant:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        print("Starting Jarvis with enhanced authoritative voice...")
        
        # Setup config
        Config.load_from_env()
        print("Configuration loaded")
        
        # Check for ElevenLabs API key
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "")
        
        # Initialize components
        print("Initializing voice engine...")
        self.voice_engine = VoiceEngine()
        
        # Enable ElevenLabs if API key exists
        if self.elevenlabs_api_key:
            print("ElevenLabs API key found, enabling premium voice...")
            self.voice_engine.enable_elevenlabs(self.elevenlabs_api_key)
            print("ElevenLabs premium voice enabled")
        else:
            print("Using offline voice engine (pyttsx3)")
        
        print("Initializing conversation manager...")
        self.conversation_manager = ConversationManager(Config.OPENAI_API_KEY)
        print("Initializing command handler...")
        self.command_handler = CommandHandler()
        
        # Initialize GUI
        print("Creating GUI interface...")
        self.gui = ModernCircularInterface()
        self.gui.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Set all callbacks including test input
        print("Setting up GUI callbacks...")
        self.gui.set_callbacks(
            toggle_callback=self.toggle_listening, 
            exit_callback=self.on_closing,
            test_input_callback=self.handle_test_input
        )
        
        # Message queue for thread-safe communication
        self.message_queue = queue.Queue()
        
        # Processing lock to prevent overlapping requests
        self.processing_lock = threading.Lock()
        
        # Flag for when new input arrives during speech
        self.new_input_during_speech = False
        
        # Input buffer for combining multiple quick inputs
        self.input_buffer = ""
        self.last_input_time = 0
        self.input_timeout = 2.0  # Seconds to wait for additional input before processing
        self.buffer_timer = None  # Timer for processing buffered input
        
        # Show time-based greeting startup message
        greeting = self._get_time_based_greeting()
        greeting_message = f"{greeting} I'm online and ready to assist you. How can I help you today?"
        self.gui.add_conversation_text("Jarvis", greeting_message)
        
        # Start the main loop
        self.running = True
        
        # Automatically start listening when launched
        self.start_listening()
        
        # Speak the greeting
        threading.Thread(target=self._speak_response, args=(greeting_message,), daemon=True).start()
        
        # Start the main application loop
        self.start_assistant()

    def toggle_listening(self):
        """Toggle the listening state."""
        if not self.voice_engine.is_listening:
            self.start_listening()
        else:
            self.stop_listening()
    
    def start_listening(self):
        """Start listening for voice input."""
        self.gui.set_listening_state(True)
        self.gui.update_status("Listening for your voice...")
        threading.Thread(target=self.voice_engine.listen, args=(self.handle_voice_input,), daemon=True).start()

    def stop_listening(self):
        """Stop listening for voice input."""
        self.voice_engine.stop_listening()
        self.gui.set_listening_state(False)
        self.gui.update_status("Listening stopped")

    def handle_test_input(self, text: str):
        """Handle test input from the GUI."""
        if not text.strip():
            return
        
        # If currently speaking, stop it
        if self.voice_engine.is_speaking:
            self.voice_engine.stop_speaking()
            self.new_input_during_speech = True
        
        # Process in a separate thread to keep UI responsive
        threading.Thread(target=self.process_input, args=(text,), daemon=True).start()
    
    def handle_voice_input(self, text: str):
        """Handle voice input by calling the process_input method."""
        if not text.strip():
            return
        
        # If speaking, set flag to indicate interruption
        if self.voice_engine.is_speaking:
            self.new_input_during_speech = True
            self.voice_engine.stop_speaking()
            
        current_time = time.time()
        
        # Cancel any existing buffer timer
        if self.buffer_timer:
            self.gui.after_cancel(self.buffer_timer)
            self.buffer_timer = None
            
        # Check if this might be a continuation of previous input
        if current_time - self.last_input_time < self.input_timeout:
            # Add to buffer with a space
            self.input_buffer += " " + text
            self.last_input_time = current_time
            
            # Only process if the text seems complete (ends with punctuation)
            if text.rstrip().endswith(('.', '!', '?')):
                buffered_text = self.input_buffer.strip()
                self.input_buffer = ""  # Clear buffer
                # Process in a separate thread
                threading.Thread(target=self.process_input, args=(buffered_text,), daemon=True).start()
            else:
                # Set a timer to process after timeout
                self.buffer_timer = self.gui.after(int(self.input_timeout * 1000), self._process_buffered_input)
        else:
            # This is new input, start fresh
            self.input_buffer = text
            self.last_input_time = current_time
            
            # If it seems like a complete sentence, process immediately
            if len(text.split()) > 5 or text.rstrip().endswith(('.', '!', '?')):
                self.input_buffer = ""  # Clear buffer
                # Process in a separate thread
                threading.Thread(target=self.process_input, args=(text,), daemon=True).start()
            else:
                # Set a timer to process after timeout
                self.buffer_timer = self.gui.after(int(self.input_timeout * 1000), self._process_buffered_input)
    
    def process_input(self, text: str):
        """Process input text and generate a response."""
        # Use a lock to prevent multiple requests from processing simultaneously
        if not self.processing_lock.acquire(blocking=False):
            print("Already processing a request, ignoring new input")
            return
        
        try:
            # Update GUI with user input
            self.gui.add_conversation_text("You", text)
            
            # Show thinking indicator in GUI
            self.gui.update_status("Thinking...")
            self.gui.show_thinking()
            
            # Check if this is a direct command first
            command_response = None
            if any(cmd in text.lower() for cmd in ["weather", "time", "date", "news", "wiki", "play", "search", "find"]):
                command_response = self.command_handler.process_command(text)
            
            # If it's not a direct command or command processing failed, use AI
            if not command_response:
                # Get AI response
                self.gui.update_status("Getting response...")
                ai_response = self.conversation_manager.get_response(text)
                final_response = ai_response
            else:
                final_response = command_response
            
            # Update GUI with AI response
            self.gui.add_conversation_text("Jarvis", final_response)
            
            # Speak the response unless we're interrupted
            if not self.new_input_during_speech:
                self.gui.update_status("Speaking...")
                threading.Thread(
                    target=self._speak_response, 
                    args=(final_response,), 
                    daemon=True
                ).start()
            else:
                # Reset the interruption flag
                self.new_input_during_speech = False
                self.gui.update_status("Ready")
            
        except Exception as e:
            print(f"Error handling input: {e}")
            self.gui.update_status("Error processing input")
            self.gui.add_conversation_text("Jarvis", f"I'm sorry, I encountered an error: {str(e)}")
        finally:
            # Release the lock
            self.processing_lock.release()
    
    def _speak_response(self, text):
        """Speak the response in a separate thread."""
        try:
            asyncio.run(self.voice_engine.speak(text))
            # Update status when done speaking
            if self.running:  # Only update if the app is still running
                self.gui.update_status("Ready")
        except Exception as e:
            print(f"Error speaking response: {e}")
            if self.running:
                self.gui.update_status("Error with voice output")
            
    def on_closing(self):
        """Handle window closing."""
        print("Shutting down Jarvis...")
        self.running = False
        # Stop any ongoing speech
        if self.voice_engine.is_speaking:
            self.voice_engine.stop_speaking()
        self.stop_listening()
        self.gui.destroy()

    def start_assistant(self):
        """Start the main application loop."""
        try:
            # Start GUI main loop
            self.gui.mainloop()
        except Exception as e:
            print(f"Critical error in main loop: {e}")
            sys.exit(1)

    def _process_buffered_input(self):
        """Process buffered input after timeout."""
        if self.input_buffer:
            buffered_text = self.input_buffer.strip()
            if buffered_text:
                print(f"Processing buffered input after timeout: '{buffered_text}'")
                self.input_buffer = ""  # Clear buffer
                self.process_input(buffered_text)
            self.buffer_timer = None

    def _get_time_based_greeting(self):
        """Return a greeting based on time of day."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning, Aditya."
        elif 12 <= hour < 17:
            return "Good afternoon, Aditya."
        elif 17 <= hour < 22:
            return "Good evening, Aditya."
        else:
            return "Good evening, Aditya. You're working late."

if __name__ == "__main__":
    try:
        assistant = JarvisAssistant()
    except Exception as e:
        tk.messagebox.showerror("Jarvis Error", f"Failed to start Jarvis: {str(e)}")
        print(f"Critical error starting Jarvis: {e}")
        sys.exit(1) 