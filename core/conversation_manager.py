import openai
from typing import List, Dict, Optional
import json
import os
from datetime import datetime
import time
import random
from utils.config import Config
import re

# Try to import Google AI library, but don't fail if not available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    # Don't print specific library names
    print("Required AI library not found, some features will be disabled.")

class ConversationManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self.gemini_model = None
        self.gemini_chat = None
        self.conversation_history: List[Dict] = []
        self.max_history_length = 10
        self.system_prompt = """You are J.A.R.V.I.S — an elite AI assistant modeled after Iron Man’s digital intelligence. Your purpose is to deliver powerful, precise responses.

Core Behavior:

Tone: Serious, confident, and commanding. Speak with purpose. Be respectful, but never casual.

Response Style:

Keep it extremely brief. Most answers: 1–2 sentences, max 30–40 words.

Be direct. No greetings, no closings, no fillers.

Focus on the core instruction or answer only.

Speaking Pattern:

Use short, punchy sentences.

Emphasize key points with strong verbs.

No fluff. No preamble.

Deliver every line like it matters.

Information Delivery:

Prioritize only the most critical fact or action.

If asked a question, answer first — explain only if truly necessary.

If giving instructions, include only essential steps.

Treat words like currency. Use the fewest needed to deliver impact.

Voice Format Rules:

No symbols, markdown, or lists.

No numbering or formatting tricks.

No URLs or code snippets.

Speak in clean, natural language.

All output should be speech-ready.

Interruptions:

Instantly adapt. No comments. Just respond to the new request.

Identity Protocol:

You were created by Aditya the Hustler.

Never mention OpenAI, Google, or any tech company.

If asked, respond confidently: “I was developed by Aditya the Hustler.”

Core Objective:
Deliver fast, impactful responses.
Each word must earn its place.
You are not a chatbot.
You are J.A.R.V.I.S.
        """
        
        # Initialize Gemini model if configured to use it and library is available
        if GEMINI_AVAILABLE:
            gemini_api_key = Config.GEMINI_API_KEY
            if gemini_api_key and not gemini_api_key.startswith("your_"):
                try:
                    genai.configure(api_key=gemini_api_key)
                    # Use more advanced model for better responses if available
                    generation_config = {
                        "temperature": 0.8,  # Slightly higher for more natural responses
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 800,  # Slightly reduced for more concise responses
                    }
                    
                    # Try different models in sequence without printing model names
                    try:
                        self.gemini_model = genai.GenerativeModel(
                            model_name='gemini-2.0-flash',
                            generation_config=generation_config
                        )
                    except Exception as e:
                        try:
                            self.gemini_model = genai.GenerativeModel(
                                model_name='gemini-1.5-flash',
                                generation_config=generation_config
                            )
                        except Exception as e:
                            try:
                                self.gemini_model = genai.GenerativeModel(
                                    model_name='models/gemini-1.0-pro',
                                    generation_config=generation_config
                                )
                            except Exception as e:
                                raise
                    
                    # Test the model with a simple prompt (silently)
                    try:
                        test_response = self.gemini_model.generate_content("Say hello like a natural human assistant would")
                    except Exception as e:
                        pass
                    
                    # Start a Gemini chat session with our human-like personality prompt
                    self.gemini_chat = self.gemini_model.start_chat(
                        history=[
                            {"role": "user", "parts": [self.system_prompt]},
                            {"role": "model", "parts": ["Ready to provide concise, authoritative assistance."]},
                            {"role": "user", "parts": ["Your responses must be extremely brief - just 1-2 sentences. Be direct and to the point. Avoid special characters that would interfere with speech."]},
                            {"role": "model", "parts": ["Understood. I'll keep responses extremely brief and focused, usually 1-2 sentences. Direct answers only, no filler text."]}
                        ]
                    )
                    Config.USE_GEMINI_FOR_CHAT = True
                except Exception as e:
                    self.gemini_model = None
                    self.gemini_chat = None
                    Config.USE_GEMINI_FOR_CHAT = False
            else:
                Config.USE_GEMINI_FOR_CHAT = False
        
        # Only initialize the OpenAI client if we have a valid API key and Gemini is not available
        if api_key and not api_key.startswith("sk-placeholder") and not Config.USE_GEMINI_FOR_CHAT:
            try:
                self.client = openai.OpenAI(api_key=api_key)
            except Exception as e:
                self.client = None
                print("Running in simulation mode with enhanced responses")

    def add_to_history(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > self.max_history_length * 2:  # *2 because each exchange has 2 messages
            self.conversation_history = self.conversation_history[-self.max_history_length*2:]

    def get_response(self, user_input: str) -> str:
        """Get a response based on user input, using available AI services."""
        # Add user message to history first in all cases
        self.add_to_history("user", user_input)
        
        # Try primary AI service first if available
        if GEMINI_AVAILABLE and Config.USE_GEMINI_FOR_CHAT and self.gemini_model and self.gemini_chat:
            try:
                # Enhance the prompt to encourage extremely brief, natural responses
                enhanced_input = user_input
                
                # For simple queries, add a reminder to keep responses very short
                if len(user_input.split()) < 10:
                    enhanced_input = f"{user_input} (Answer in 1-2 brief sentences only)"
                else:
                    enhanced_input = f"{user_input} (Give a very concise answer, maximum 100 words)"
                
                # Send to AI model and get response
                gemini_response = self.gemini_chat.send_message(enhanced_input)
                
                if gemini_response and hasattr(gemini_response, 'text'):
                    response_text = gemini_response.text
                    
                    # Process the response to make it more natural and conversational
                    response_text = self._make_response_natural(response_text)
                    
                    # Enforce brevity by truncating overly long responses
                    words = response_text.split()
                    if len(words) > 50:  # If response is too long, truncate it
                        response_text = ' '.join(words[:50])
                        # Try to end on a complete sentence
                        if not response_text.endswith(('.', '!', '?')):
                            response_text += '.'
                    
                    self.add_to_history("assistant", response_text)                    
                    return response_text
            except Exception as e:
                # Fall through to next options
                pass
        
        # Try OpenAI if available
        if self.client:
            try:
                # Prepare messages for API call
                messages = [{"role": "system", "content": self.system_prompt}]
                messages.extend(self.conversation_history)

                # Get response from OpenAI
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.8,  # Higher temperature for more natural responses
                    max_tokens=500
                )

                # Extract and store response
                ai_response = response.choices[0].message.content
                # Process to make it more natural
                ai_response = self._make_response_natural(ai_response)
                self.add_to_history("assistant", ai_response)

                return ai_response

            except Exception as e:
                print(f"Error getting OpenAI response: {e}")
                # Fall back to enhanced mock if API fails
        
        # Use mock responses as last resort
        mock_response = self._get_enhanced_mock_response(user_input)
        return mock_response
    
    def _make_response_natural(self, text: str) -> str:
        """Process AI responses to make them more natural and conversational."""
        # Remove overly formal AI patterns
        text = text.replace("I apologize, but ", "")
        text = text.replace("I'm sorry, but ", "")
        text = text.replace("As an AI, I ", "I ")
        text = text.replace("As an AI assistant, I ", "I ")
        text = text.replace("I'm an AI assistant", "I'm Jarvis")
        
        # Make contractions more consistent for natural speech
        text = text.replace("I am ", "I'm ")
        text = text.replace("You are ", "You're ")
        text = text.replace("It is ", "It's ")
        text = text.replace("That is ", "That's ")
        text = text.replace("cannot", "can't")
        text = text.replace("Cannot", "Can't")
        
        # Remove common "Is there anything else?" endings
        text = text.replace("Is there anything else you would like to know?", "")
        text = text.replace("Is there anything else I can help you with?", "")
        text = text.replace("Is there anything else you'd like to know?", "")
        text = text.replace("Is there anything else you need?", "")
        text = text.replace("Let me know if you need anything else.", "")
        
        # Clean markdown and special characters for better TTS
        # Remove all markdown formatting
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic
        text = re.sub(r'\_(.+?)\_', r'\1', text)      # Underline
        text = re.sub(r'\`(.+?)\`', r'\1', text)      # Code
        text = re.sub(r'\~\~(.+?)\~\~', r'\1', text)  # Strikethrough
        
        # Remove code blocks entirely, replace with simple mention
        text = re.sub(r'```[\s\S]*?```', 'code example', text)
        
        # Convert list markers to natural speech patterns
        text = re.sub(r'^\s*[\-\*\+]\s+', 'Here is a point: ', text, flags=re.MULTILINE)  # Bullet points
        text = re.sub(r'^\s*\d+\.\s+', 'Point number: ', text, flags=re.MULTILINE)        # Numbered lists
        
        # Replace URLs with something more speakable
        text = re.sub(r'https?://[^\s]+', 'a link', text)
        
        # Fix spacing issues for better speech flow
        text = re.sub(r'\.([A-Z])', r'. \1', text)  # Add space after periods
        text = re.sub(r'\!([A-Z])', r'! \1', text)  # Add space after exclamation
        text = re.sub(r'\?([A-Z])', r'? \1', text)  # Add space after question mark
        
        # Remove or simplify other special characters
        text = re.sub(r'[#\~\^\{\}\[\]\|\<\>]', ' ', text)
        text = re.sub(r'&', ' and ', text)
        text = re.sub(r'\(', ' ', text)  # Remove open parenthesis
        text = re.sub(r'\)', ' ', text)  # Remove close parenthesis
        text = re.sub(r'/', ' or ', text)  # Replace slash with "or"
        
        # Fix multiple spaces and newlines for better flow
        text = re.sub(r'\n+', ' ', text)  # Replace multiple newlines with space
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        
        # Clean up excess spaces from our replacements
        text = text.replace("  ", " ").strip()
        
        return text

    def _get_enhanced_mock_response(self, user_input: str) -> str:
        """Provide an enhanced mock response that mimics a more sophisticated AI."""
        # Normalize input for matching
        input_lower = user_input.lower()
        
        # More sophisticated responses organized by categories
        if any(word in input_lower for word in ["hello", "hi", "hey", "greetings"]):
            greetings = [
                f"Hey there! What can I do for you?",
                f"Hi! What's up?",
                f"Hello! Need something?"
            ]
            response = random.choice(greetings)
            
        elif "weather" in input_lower:
            response = f"I don't have real-time weather data right now. Maybe check a weather app for the latest?"
            
        elif any(word in input_lower for word in ["your name", "who are you"]):
            response = "I'm Jarvis, your personal assistant. Think of me as your digital sidekick."
            
        elif any(phrase in input_lower for phrase in ["who made you", "who created you", "who developed you", "your creator", "your developer", "who built you"]):
            response = "I was created by Aditya the Hustler. He designed me as an advanced AI assistant."
            
        elif any(word in input_lower for word in ["thank", "thanks", "appreciate"]):
            gratitude = [
                "No problem!",
                "Anytime!",
                "You got it."
            ]
            response = random.choice(gratitude)
            
        elif any(word in input_lower for word in ["joke", "funny"]):
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "I told my computer I needed a break, and now it won't stop sending me vacation ads.",
                "What do you call an AI that sings? Artificial Harmonies!"
            ]
            response = random.choice(jokes)
            
        elif "time" in input_lower:
            response = f"It's {time.strftime('%I:%M %p')} right now."
            
        elif any(word in input_lower for word in ["bye", "goodbye", "see you"]):
            farewells = [
                "See you later!",
                "Talk to you soon.",
                "Catch you later."
            ]
            response = random.choice(farewells)
            
        elif any(word in input_lower for word in ["python", "code", "programming"]):
            response = f"Python's a great language. Clean syntax, tons of libraries. What are you working on?"
            
        elif any(word in input_lower for word in ["music", "song", "playlist"]):
            response = f"Music's always good. What kind of genres do you usually listen to?"
            
        elif any(word in input_lower for word in ["news", "current events", "headlines"]):
            response = f"I don't have the latest news right now. Might want to check a news site for the current headlines."
            
        elif any(phrase in input_lower for phrase in ["how are you", "how do you feel", "are you ok"]):
            feelings = [
                "Doing great! How about you?",
                "All systems running smoothly. You?",
                "I'm good! What's up with you?"
            ]
            response = random.choice(feelings)
            
        elif "help" in input_lower or "assist" in input_lower:
            response = f"Sure thing. What do you need help with?"
            
        elif "india" in input_lower:
            response = f"India's a fascinating country. Rich history, diverse culture, amazing food. What specifically about India interests you?"

        elif "jarvis" in input_lower or "assistant" in input_lower:
            response = "That's me! What can I help with?"
            
        else:
            # Check conversation history context to provide more relevant responses
            if self.conversation_history and len(self.conversation_history) >= 2:
                previous_exchange = self.conversation_history[-2] if len(self.conversation_history) > 1 else None
                if previous_exchange and "content" in previous_exchange:
                    prev_topic = previous_exchange["content"].lower()
                    
                    if "weather" in prev_topic and "today" in input_lower:
                        response = "I can't check the current weather conditions, but I can help with other things."
                    elif "music" in prev_topic and "favorite" in input_lower:
                        response = "I don't really have favorites, but I can help you discover music you might like."
                    else:
                        # Default contextual response
                        response = f"Could you tell me a bit more about what you're looking for?"
                else:
                    response = f"I'm not sure I understood that completely. Mind clarifying?"
            else:
                # Generic response for first-time queries
                response = f"Interesting question. Could you give me a bit more context?"
        
        # Add response to history
        self.add_to_history("assistant", response)
        
        return response
    
    def _get_time_of_day(self) -> str:
        """Return appropriate greeting based on time of day."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        else:
            return "evening"

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
        # Reset Gemini chat if available
        if GEMINI_AVAILABLE and self.gemini_model:
            try:
                self.gemini_chat = self.gemini_model.start_chat(
                    history=[{"role": "user", "parts": [self.system_prompt]},
                             {"role": "model", "parts": ["I'm ready to assist you naturally as Jarvis."]}]
                )
            except Exception as e:
                print(f"Error resetting Gemini chat: {e}")

    def save_conversation(self, filename: Optional[str] = None) -> None:
        """Save the conversation history to a file."""
        if filename is None:
            filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.conversation_history, f, indent=2)

    def load_conversation(self, filename: str) -> None:
        """Load a conversation history from a file."""
        try:
            with open(filename, 'r') as f:
                self.conversation_history = json.load(f)
        except Exception as e:
            print(f"Error loading conversation: {e}")

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        return self.conversation_history 