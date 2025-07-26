import os
from typing import Dict, Any

class Config:
    # API Keys - try to load from environment or use placeholder
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-placeholder-key")  # Replace with your actual key in environment
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyD4Dn3h6EBoVHBgnxB9QRzbzk_Y4qxMTSY")  # Updated Gemini API key
    SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID", "your_search_engine_id")  # Google Custom Search Engine ID
    
    # Instagram Credentials
    INSTAGRAM_USERNAME = "bossofengineering"
    INSTAGRAM_SESSION_ID = "59971323477%3AWHjBgu9V5gRLnB%3A6%3AAYe0f0_t-dP1hZxLYL7LwCMZLqlNZIbRAAvU"

    # Assistant Settings
    VOICE = "en-US-ChristopherNeural"
    SILENCE_THRESHOLD = 0.5
    MAX_HISTORY_LENGTH = 10
    
    # API Settings
    USE_GEMINI_FOR_CHAT = True  # Use Gemini instead of OpenAI when available
    USE_REAL_SEARCH = True  # Use real search APIs instead of simulations
    ENABLE_VOICE = True  # Enable voice output

    # Feature Flags - disabled for now to simplify
    ENABLE_FACE_RECOGNITION = False  # Set to False since we're not using this now
    ENABLE_EMOTION_DETECTION = False  # Set to False since we're not using this now
    ENABLE_SOCIAL_MEDIA = True
    ENABLE_EMAIL = True
    ENABLE_SYSTEM_CONTROL = True

    @classmethod
    def load_from_env(cls) -> None:
        """Load configuration from environment variables."""
        for key in dir(cls):
            if key.isupper():
                env_value = os.getenv(key)
                if env_value is not None:
                    # Convert string values to appropriate types
                    if env_value.lower() in ('true', 'false'):
                        setattr(cls, key, env_value.lower() == 'true')
                    elif env_value.isdigit():
                        setattr(cls, key, int(env_value))
                    elif env_value.replace('.', '').isdigit():
                        setattr(cls, key, float(env_value))
                    else:
                        setattr(cls, key, env_value)

    @classmethod
    def get_all_settings(cls) -> Dict[str, Any]:
        """Get all configuration settings as a dictionary."""
        return {key: getattr(cls, key) 
                for key in dir(cls) 
                if key.isupper() and not key.startswith('_')}

    @classmethod
    def update_setting(cls, key: str, value: Any) -> None:
        """Update a configuration setting."""
        if key.isupper() and hasattr(cls, key):
            setattr(cls, key, value)
        else:
            raise ValueError(f"Invalid configuration key: {key}") 