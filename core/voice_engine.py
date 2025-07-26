import speech_recognition as sr
import pyttsx3
import asyncio
import numpy as np
import queue
import threading
import time
import os
import requests
import json
import re
import subprocess
import tempfile
from typing import Optional, Callable
# Import edge-tts for better quality free voice
import edge_tts

class VoiceEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_speaking = False
        self.silence_threshold = 1.5  # Increased from 0.8 to 1.5 seconds of silence to consider speech ended
        self.last_speech_time = 0
        self.tts_lock = threading.Lock()
        
        # Flag to request stopping current speech
        self.stop_current_speech = False
        
        # Initialize offline TTS engine (primary for reliability)
        try:
            self.offline_engine = pyttsx3.init()
            
            # Enhance voice settings for more premium sound quality
            self.offline_engine.setProperty('rate', 175)  # Faster rate for natural speech
            self.offline_engine.setProperty('volume', 1.0)  # Maximum volume
            
            # Get available voices and find the best quality ones
            voices = self.offline_engine.getProperty('voices')
            print(f"Found {len(voices)} available voices")
            
            # Premium voices to look for (in order of preference)
            premium_voices = [
                "DAVID",      # Premium US male voice (best quality)
                "MARK",       # Another good US male voice
                "JAMES",      # British male voice with excellent quality
                "RICHARD",    # Good male voice
                "GEORGE"      # Another good male voice
            ]
            
            # Try to find premium voices first
            voice_found = False
            for premium in premium_voices:
                for voice in voices:
                    name = voice.name.upper()
                    if premium in name and "EN" in name.upper():
                        self.offline_engine.setProperty('voice', voice.id)
                        print(f"Using premium voice: {voice.name} (high quality)")
                        voice_found = True
                        break
                if voice_found:
                    break
            
            # If no premium voice found, use any English male voice
            if not voice_found:
                for voice in voices:
                    if "MALE" in voice.name.upper() and "EN" in voice.name.upper():
                        self.offline_engine.setProperty('voice', voice.id)
                        print(f"Using voice: {voice.name}")
                        voice_found = True
                        break
            
            # Last resort - use any voice
            if not voice_found and voices:
                self.offline_engine.setProperty('voice', voices[0].id)
                print(f"Using default voice: {voices[0].name}")
                
            print("Offline TTS engine initialized with premium voice settings")
        except Exception as e:
            print(f"Error initializing pyttsx3: {e}")
            self.offline_engine = None
        
        # Edge TTS as backup (requires internet)
        self.use_edge_tts = True  # Set to True to use Edge TTS
        
        # Edge TTS voice options (if enabled)
        edge_voices = {
            "jason": "en-US-JasonNeural", # Premium male voice with excellent pitch and tone (best)
            "guy": "en-US-GuyNeural",     # Clear male voice with good pitch
            "tony": "en-US-TonyNeural",   # New premium male voice with deep tone
            "davis": "en-US-DavisNeural", # Professional male voice
            "ryan": "en-GB-RyanNeural",   # British male voice with excellent pitch
            "aria": "en-US-AriaNeural",   # Premium female voice
            "jenny": "en-US-JennyNeural", # Natural female voice
            "sara": "en-US-SaraNeural"    # Professional female voice
        }
        
        # Get from environment variable or use default premium voice
        voice_key = os.getenv("EDGE_VOICE", "jason").lower()
        self.edge_voice = edge_voices.get(voice_key, "en-US-JasonNeural")
        
        # ElevenLabs settings - premium option if API key available
        self.use_elevenlabs = False
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.elevenlabs_voice_id = "pNInz6obpgDQGcFmaJgB"  # Josh (highly realistic)
        
        # Adjust for ambient noise
        try:
            with self.microphone as source:
                print("Adjusting for ambient noise... (please be quiet)")
                self.recognizer.adjust_for_ambient_noise(source, duration=2.0)
                print("Microphone adjusted for ambient noise")
        except Exception as e:
            print(f"Warning: Could not adjust for ambient noise: {e}")
            
        # Speech recognition settings - Modified for less sensitivity
        self.recognizer.energy_threshold = 3500  # Increased from 3000 to require louder speech
        self.recognizer.dynamic_energy_threshold = True  # Adjust threshold automatically
        self.recognizer.dynamic_energy_adjustment_damping = 0.25  # Increased from 0.15 - slower adjustment to environment
        self.recognizer.dynamic_energy_adjustment_ratio = 1.2  # Reduced from 1.5 - less sensitive
        self.recognizer.pause_threshold = 0.8  # Reduced from 1.2 to improve responsiveness

    def stop_speaking(self):
        """Stop current speech immediately."""
        self.stop_current_speech = True
        print("Stopping current speech")

    async def speak(self, text: str) -> None:
        """Convert text to speech using available TTS engine."""
        if not text:
            return

        # Clear any previous stop flag
        self.stop_current_speech = False
        self.is_speaking = True
        try:
            # Clean the text to make speech more natural
            cleaned_text = self._clean_text_for_speech(text)
            print(f"Speaking text (length: {len(cleaned_text.split())} words)")
            
            if self.use_elevenlabs and self.elevenlabs_api_key:
                # Use ElevenLabs for premium voice
                await self._speak_with_elevenlabs(cleaned_text)
            elif self.use_edge_tts:
                # Use Edge TTS for better free voice quality
                await self._speak_with_edge_tts(cleaned_text)
            else:
                # Use offline pyttsx3
                await self._speak_with_pyttsx3_async(cleaned_text)
        except Exception as e:
            print(f"TTS error: {e}")
            print(f"Fallback: Text that would have been spoken: {text}")
        finally:
            self.is_speaking = False
            self.stop_current_speech = False
            print("Finished speaking")
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text to make speech sound more natural."""
        # Make sure text ends with a period to ensure proper completion
        if text and not text.rstrip().endswith(('.', '!', '?')):
            text = text.rstrip() + '.'
            
        # Remove special characters that may make speech sound unnatural
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Replace **text** with text
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # Replace *text* with text
        text = re.sub(r'\_(.+?)\_', r'\1', text)      # Replace _text_ with text
        text = re.sub(r'\`(.+?)\`', r'\1', text)      # Replace `text` with text
        text = re.sub(r'\~\~(.+?)\~\~', r'\1', text)  # Replace ~~text~~ with text
        
        # Remove Markdown code blocks which are hard to read aloud
        text = re.sub(r'```[a-zA-Z]*\n(.*?)\n```', r'code example', text, flags=re.DOTALL)
        
        # Replace URLs with something more speakable
        text = re.sub(r'https?://[^\s]+', 'a link', text)
        
        # Fix ellipsis for better pause handling
        text = re.sub(r'\.\.\.+', ', ', text)  # Replace ellipsis with comma for cleaner pauses
        
        # Fix spacing after periods for better flow - ensure sentence boundaries are clear
        text = re.sub(r'\.([A-Z])', r'. \1', text)  # Ensure space after period before capital
        text = re.sub(r'\!([A-Z])', r'! \1', text)
        text = re.sub(r'\?([A-Z])', r'? \1', text)
        
        # Ensure proper spacing around punctuation
        text = re.sub(r'\s*\.\s*', '. ', text)  # Normalize period spacing
        text = re.sub(r'\s*\!\s*', '! ', text)  # Normalize exclamation spacing
        text = re.sub(r'\s*\?\s*', '? ', text)  # Normalize question mark spacing
        text = re.sub(r'\s*\,\s*', ', ', text)  # Normalize comma spacing
        
        # Make sure sentence boundaries are respected
        sentences = re.split(r'(?<=[.!?])\s+', text)
        for i, sentence in enumerate(sentences):
            if i < len(sentences)-1 and not sentence.rstrip().endswith(('.', '!', '?')):
                sentences[i] = sentence.rstrip() + '.'
        
        # Rejoin with proper spacing
        return ' '.join(sentences).strip()
    
    async def _speak_with_pyttsx3_async(self, text: str) -> None:
        """Use pyttsx3 for offline TTS in an async-friendly way."""
        # Create a new engine instance each time to avoid run loop issues
        try:
            # Run the TTS in a separate thread to not block the event loop
            await asyncio.get_event_loop().run_in_executor(
                None, 
                self._speak_with_pyttsx3_sync, 
                text
            )
        except Exception as e:
            print(f"Async TTS error: {e}")
    
    def _speak_with_pyttsx3_sync(self, text: str) -> None:
        """Synchronous TTS function to be run in a thread."""
        with self.tts_lock:  # Use a lock to prevent multiple simultaneous TTS operations
            try:
                # Create a new engine each time for better pitch control
                engine = pyttsx3.init()
                
                # Use enhanced voice settings for premium quality
                engine.setProperty('rate', 180)  # Slightly faster for more natural speech
                engine.setProperty('volume', 1.0)  # Full volume
                
                # Copy voice from main engine
                if self.offline_engine:
                    if self.offline_engine.getProperty('voice'):
                        engine.setProperty('voice', self.offline_engine.getProperty('voice'))
                
                # Clean up text for better speech synthesis
                text = self._preprocess_text_for_speech(text)
                
                # Check if the text is very short
                if len(text.split()) <= 15:
                    print(f"Speaking short text directly: {text}")
                    engine.say(text)
                    engine.runAndWait()
                    return
                
                # For longer text, use a sentence-by-sentence approach for more natural pauses
                print(f"Speaking text (length: {len(text.split())} words)")
                
                # Split text into sentences for better control
                sentences = re.split(r'(?<=[.!?])\s+', text)
                
                for i, sentence in enumerate(sentences):
                    if self.stop_current_speech:
                        print("Speech interrupted")
                        break
                        
                    if not sentence.strip():
                        continue
                        
                    # Enhanced sentence-specific rate/pitch for more natural-sounding speech
                    # Questions slightly higher pitch, exclamations more emphasis
                    if sentence.strip().endswith('?'):
                        engine.setProperty('rate', 175)  # Slightly slower for questions
                    elif sentence.strip().endswith('!'):
                        engine.setProperty('rate', 185)  # Slightly faster for exclamations
                    else:
                        engine.setProperty('rate', 180)  # Normal rate for statements
                    
                    # Speak this sentence
                    engine.say(sentence.strip())
                    engine.runAndWait()
                    
                    # Add natural pauses between sentences
                    if i < len(sentences) - 1:  # Not the last sentence
                        if sentence.endswith('!'):
                            time.sleep(0.2)  # Exclamation
                        elif sentence.endswith('?'):
                            time.sleep(0.15)  # Question
                        else:
                            time.sleep(0.1)  # Normal pause
                    
                    # Check again for stop signal
                    if self.stop_current_speech:
                        print("Speech interrupted")
                        break
                        
                print("Finished speaking")
            except Exception as e:
                print(f"TTS error: {e}")
            finally:
                self.is_speaking = False
                self.stop_current_speech = False

    def _preprocess_text_for_speech(self, text: str) -> str:
        """Preprocess text for better speech quality."""
        # Fix common TTS pronunciation issues
        text = text.replace("AI", "A.I.")
        text = text.replace("API", "A.P.I.")
        text = text.replace("UI", "U.I.")
        text = text.replace("JSON", "Jason")
        text = text.replace("vs.", "versus")
        text = text.replace("etc.", "etcetera")
        text = text.replace("i.e.", "that is")
        text = text.replace("e.g.", "for example")
        
        # Fix numbers and special characters for better speech
        text = re.sub(r'(\d+)%', r'\1 percent', text)
        text = re.sub(r'(\d+)\+', r'\1 plus', text)
        text = re.sub(r'(\d+)x(\d+)', r'\1 by \2', text)
        
        # Improve pronunciation of technical terms
        tech_terms = {
            r'\bML\b': 'machine learning',
            r'\bDL\b': 'deep learning',
            r'\bNLP\b': 'natural language processing',
            r'\bCV\b': 'computer vision',
            r'\bDB\b': 'database',
            r'\bOS\b': 'operating system',
            r'\bIDE\b': 'integrated development environment',
            r'\bVM\b': 'virtual machine',
            r'\bOOP\b': 'object oriented programming',
            r'\bHTTP\b': 'H.T.T.P.',
            r'\bHTML\b': 'H.T.M.L.',
            r'\bCSS\b': 'C.S.S.',
            r'\bURL\b': 'U.R.L.',
            r'\bSEO\b': 'S.E.O.',
            r'\bCPU\b': 'C.P.U.',
            r'\bGPU\b': 'G.P.U.',
            r'\bRAM\b': 'ram',
            r'\bSSD\b': 'S.S.D.',
            r'\bHDD\b': 'H.D.D.',
            r'\bUSB\b': 'U.S.B.',
            r'\bWiFi\b': 'Wi-Fi',
            r'\bIP\b': 'I.P.',
            r'\bGUI\b': 'G.U.I.',
            r'\bCLI\b': 'C.L.I.',
            r'\bSDK\b': 'S.D.K.',
            r'\bAPI\b': 'A.P.I.',
            r'\bJDK\b': 'J.D.K.',
            r'\bJVM\b': 'J.V.M.',
            r'\bJIT\b': 'J.I.T.',
            r'\bJAR\b': 'jar',
            r'\bWAR\b': 'war',
            r'\bEAR\b': 'ear',
            r'\bJSP\b': 'J.S.P.',
            r'\bJSF\b': 'J.S.F.',
            r'\bJPA\b': 'J.P.A.',
            r'\bJMS\b': 'J.M.S.',
            r'\bJNDI\b': 'J.N.D.I.',
            r'\bJMX\b': 'J.M.X.',
            r'\bJNI\b': 'J.N.I.',
            r'\bJAAS\b': 'J.A.A.S.',
            r'\bJAWS\b': 'jaws',
        }
        
        # Apply technical term replacements
        for pattern, replacement in tech_terms.items():
            text = re.sub(pattern, replacement, text)
        
        # Add slight pauses with commas where beneficial
        text = re.sub(r'(\w+)\s+(however|therefore|moreover|furthermore|nevertheless|consequently)', r'\1, \2', text)
        
        # Ensure proper spacing after punctuation
        text = re.sub(r'([.!?;:])\s*([A-Za-z])', r'\1 \2', text)
        
        return text
    
    async def _speak_with_elevenlabs(self, text: str) -> None:
        """Use ElevenLabs API for premium quality voice."""
        try:
            # For very long text, break it into chunks to ensure complete delivery
            max_chunk_length = 300  # Characters per chunk
            
            if len(text) > max_chunk_length:
                print(f"Text is long ({len(text)} chars), breaking into chunks for better delivery")
                # Split into sentences first
                sentences = re.split(r'(?<=[.!?])\s+', text)
                chunks = []
                current_chunk = ""
                
                for sentence in sentences:
                    # If adding this sentence would exceed chunk size, finalize current chunk
                    if len(current_chunk) + len(sentence) > max_chunk_length:
                        if current_chunk:  # Only add non-empty chunks
                            chunks.append(current_chunk)
                        current_chunk = sentence
                    else:
                        # Add to current chunk
                        if current_chunk:
                            current_chunk += " " + sentence
                        else:
                            current_chunk = sentence
                
                # Add the last chunk if it's not empty
                if current_chunk:
                    chunks.append(current_chunk)
                
                print(f"Broken into {len(chunks)} chunks for ElevenLabs delivery")
                
                # Process each chunk
                for i, chunk in enumerate(chunks):
                    if self.stop_current_speech:
                        print("Speech interrupted")
                        break
                    
                    print(f"Speaking chunk {i+1}/{len(chunks)}")
                    await self._process_elevenlabs_chunk(chunk)
                    
                    # Brief pause between chunks for natural flow
                    if i < len(chunks) - 1 and not self.stop_current_speech:
                        await asyncio.sleep(0.5)
            else:
                # Short text, process directly
                await self._process_elevenlabs_chunk(text)
        except Exception as e:
            print(f"ElevenLabs error: {e}")
            # Fallback to offline TTS
            await self._speak_with_pyttsx3_async(text)
            
    async def _process_elevenlabs_chunk(self, text: str) -> None:
        """Process a single chunk of text with ElevenLabs."""
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice_id}/stream"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.75,  # Increased stability for more consistent, authoritative tone
                    "similarity_boost": 0.5   # Lower similarity to allow for more expressive delivery
                }
            }
            
            # Make the API call asynchronously
            response_content = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._make_elevenlabs_request(url, headers, data)
            )
            
            if response_content and not self.stop_current_speech:
                # Save the audio to a file
                with open("temp_audio.mp3", "wb") as f:
                    f.write(response_content)
                
                # Play using a system command
                if os.name == "nt":  # Windows
                    os.system("start temp_audio.mp3")
                    # More accurate wait calculation - allow more time for longer text
                    word_count = len(text.split())
                    # Calculate time in seconds (approx 0.3s per word, with minimum 2s)
                    wait_time = max(2, int(word_count * 0.3))
                    print(f"Waiting approximately {wait_time} seconds for {word_count} words")
                    
                    for i in range(wait_time):
                        if i > 0 and i % 5 == 0:
                            print(f"Still playing... ({i}/{wait_time}s)")
                        await asyncio.sleep(1)
                        if self.stop_current_speech:
                            # Try to stop audio playback on Windows
                            os.system("taskkill /F /IM wmplayer.exe >nul 2>&1")
                            break
                else:  # macOS or Linux
                    os.system("mpg123 temp_audio.mp3")
            else:
                # Fallback to offline TTS
                await self._speak_with_pyttsx3_async(text)
        except Exception as e:
            print(f"ElevenLabs chunk processing error: {e}")
            # Fallback to offline TTS
            await self._speak_with_pyttsx3_async(text)
    
    def _make_elevenlabs_request(self, url, headers, data):
        """Make the HTTP request to ElevenLabs API synchronously."""
        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.content
            else:
                print(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"ElevenLabs request error: {e}")
            return None

    async def _speak_with_edge_tts(self, text: str) -> None:
        """Use Edge TTS for high-quality free voice output."""
        try:
            print(f"Using Edge TTS with voice: {self.edge_voice}")
            
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_filename = temp_file.name
            
            # Direct approach with simpler Edge TTS usage
            # Instead of SSML, use direct voice-text method which is more reliable
            if len(text.split()) > 15:
                sentences = re.split(r'(?<=[.!?])\s+', text)
                
                for i, sentence in enumerate(sentences):
                    if self.stop_current_speech:
                        print("Speech interrupted")
                        break
                    
                    if not sentence.strip():
                        continue
                    
                    print(f"Speaking sentence {i+1}/{len(sentences)}")
                    
                    # Use direct text method (more reliable than SSML)
                    try:
                        # Use async with better error handling
                        tts = edge_tts.Communicate(text=sentence.strip(), voice=self.edge_voice, rate="+2%", volume="+10%", pitch="+2Hz")
                        await tts.save(temp_filename)
                        
                        # Play the audio
                        if os.name == "nt":  # Windows
                            # Use a simpler method for Windows that is more reliable
                            os.system(f'powershell -c "(New-Object Media.SoundPlayer \'{temp_filename}\').PlaySync()"')
                        else:
                            os.system(f"mpg123 {temp_filename}")
                        
                        # Add natural pauses between sentences
                        if i < len(sentences) - 1 and not self.stop_current_speech:
                            if sentence.endswith('!'):
                                await asyncio.sleep(0.2)  # Exclamation
                            elif sentence.endswith('?'):
                                await asyncio.sleep(0.15)  # Question
                            else:
                                await asyncio.sleep(0.1)  # Normal pause
                    except Exception as inner_e:
                        print(f"Error with Edge TTS for sentence: {inner_e}")
                        continue
            else:
                # For shorter text, use direct approach
                try:
                    tts = edge_tts.Communicate(text=text.strip(), voice=self.edge_voice, rate="+2%", volume="+10%", pitch="+2Hz")
                    await tts.save(temp_filename)
                    
                    # Play the audio
                    if os.name == "nt":  # Windows
                        os.system(f'powershell -c "(New-Object Media.SoundPlayer \'{temp_filename}\').PlaySync()"')
                    else:
                        os.system(f"mpg123 {temp_filename}")
                except Exception as inner_e:
                    print(f"Error with Edge TTS for short text: {inner_e}")
                    raise  # Re-raise to fall back to pyttsx3
            
            # Clean up temporary file
            try:
                os.unlink(temp_filename)
            except:
                pass
                
        except Exception as e:
            print(f"Edge TTS error, falling back to offline voice: {e}")
            # Fall back to offline TTS
            await self._speak_with_pyttsx3_async(text)

    def listen(self, callback: Callable[[str], None]) -> None:
        """Continuously listen to microphone input."""
        self.is_listening = True
        
        def audio_callback(recognizer, audio):
            try:
                # If we're currently speaking, stop talking to listen to the user
                if self.is_speaking:
                    self.stop_speaking()
                    time.sleep(0.2)  # Small pause to let speech stop
                
                # Try using Google's speech recognition (more accurate but requires internet)
                text = recognizer.recognize_google(audio)
                if text:
                    self.last_speech_time = time.time()
                    # Only process if the text seems complete (has proper ending or is long enough)
                    # This helps prevent processing incomplete sentences
                    if len(text.split()) > 3 or text.rstrip().endswith(('.', '!', '?')):
                        callback(text)
                    else:
                        print(f"Short phrase detected, waiting for more: '{text}'")
            except sr.UnknownValueError:
                # Nothing recognized
                pass
            except sr.RequestError as e:
                print(f"Speech service error: {e}")
                # Try using offline Sphinx recognition as fallback
                try:
                    from speech_recognition import Recognizer, AudioFile
                    text = recognizer.recognize_sphinx(audio)
                    if text:
                        self.last_speech_time = time.time()
                        callback(text)
                except:
                    # Only use simulated input for significant errors, not for UnknownValueError
                    print("Speech recognition services failed")
                    if time.time() - self.last_speech_time > 5:  # Only simulate if it's been a while
                        callback("I didn't catch that. Could you please repeat?")

        def listen_in_background():
            try:
                with self.microphone as source:
                    print("Listening for voice input...")
                    
                    # More dynamic energy threshold for better recognition in various environments
                    self.recognizer.dynamic_energy_threshold = True
                    
                    while self.is_listening:
                        try:
                            # Listen with longer timeout and phrase_time_limit for more complete sentences
                            audio = self.recognizer.listen(
                                source, 
                                timeout=1.5,  # Increased from 1.0
                                phrase_time_limit=10.0  # Increased from 7.5 to allow longer phrases
                            )
                            self.audio_queue.put(audio)
                        except sr.WaitTimeoutError:
                            # Check if we've been silent for a while - use silence_threshold
                            if time.time() - self.last_speech_time > self.silence_threshold:
                                continue
                        except Exception as e:
                            print(f"Error in background listening: {e}")
                            time.sleep(0.1)  # Small sleep to prevent CPU spin
            except Exception as e:
                print(f"Critical error in microphone listening: {e}")
                # Use a simulated input if real microphone fails
                callback("I'm having trouble with the microphone. Please check your audio settings.")

        # Start background listening
        listening_thread = threading.Thread(target=listen_in_background, daemon=True)
        listening_thread.start()
        
        # Process audio queue
        while self.is_listening:
            try:
                # Get audio with a shorter timeout for more responsive experience
                audio = self.audio_queue.get(timeout=0.5)
                audio_callback(self.recognizer, audio)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing audio: {e}")

    def stop_listening(self) -> None:
        """Stop the continuous listening process."""
        self.is_listening = False

    def is_speaking_now(self) -> bool:
        """Check if the assistant is currently speaking."""
        return self.is_speaking
        
    def enable_elevenlabs(self, api_key: str = None, voice_id: str = None) -> None:
        """Enable ElevenLabs TTS with an API key."""
        if api_key:
            self.elevenlabs_api_key = api_key
        if voice_id:
            self.elevenlabs_voice_id = voice_id
        self.use_elevenlabs = True
        print("ElevenLabs premium voice enabled")
        
    def disable_elevenlabs(self) -> None:
        """Disable ElevenLabs TTS and use offline voice."""
        self.use_elevenlabs = False
        print("Switched to offline voice") 