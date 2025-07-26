# Jarvis AI Assistant

A desktop AI assistant with voice interaction capabilities, similar to ChatGPT, but with a local interface and voice controls.

## Features

- **Voice Interaction**: Talk to Jarvis and hear spoken responses
- **Modern GUI**: Clean, responsive interface with visual feedback
- **AI-Powered Responses**: Natural conversations powered by OpenAI or local simulation
- **Premium Voice Option**: Integration with ElevenLabs for ultra-realistic TTS
- **Command Processing**: Execute system tasks and web searches
- **Social Media Integration**: Connect with Instagram and WhatsApp (simulation)

## Getting Started

### Prerequisites

- Python 3.8+ installed
- An OpenAI API key (optional, but recommended for better responses)
- An ElevenLabs API key (optional, for premium voice)

### Installation

1. Clone the repository
2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Set up environment variables (optional):
   - Create a `.env` file in the project root
   - Add your API keys:

```
OPENAI_API_KEY=your_openai_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

### Running Jarvis

Start the assistant by running:

```bash
python main.py
```

## Usage

- **Text Input**: Type in the text field and press Enter
- **Voice Input**: Click "Start Listening" and speak
- **Test Input**: Use the "Test Input" button to simulate voice commands
- **Clear Chat**: Clear the conversation history with "Clear Chat"

## Enhanced Features

This improved version of Jarvis includes:

1. **Better Voice Output**:
   - Local voice via pyttsx3 for offline operation
   - Premium ElevenLabs voice for realistic speech (requires API key)

2. **Modern Interface**:
   - Dark theme with visual polish
   - Animated voice visualization
   - Text chat panel with formatting
   - Status indicators and better feedback

3. **Enhanced Responses**:
   - Improved conversational abilities
   - Code snippet formatting
   - Random variation in responses
   - Context-aware replies

4. **Stability Improvements**:
   - Better error handling
   - Graceful fallbacks when services are unavailable
   - Thread management for non-blocking operation

## Troubleshooting

- **No voice output**: Make sure your speakers are on and working
- **Voice recognition issues**: Try using the text input as a backup
- **API errors**: Check your internet connection and API keys

## Enhancement Options

To make Jarvis even better:

1. Get an OpenAI API key for more intelligent responses
2. Get an ElevenLabs API key for premium voice quality
3. Customize voices and personalities in config.py

## License

This project is for educational purposes.

## Credits

Created by Aditya Gupta with assistance from AI 