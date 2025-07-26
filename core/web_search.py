    def __init__(self):
        # Try to initialize with Gemini API for enhanced responses
        try:
            from google.generativeai import GenerativeModel, configure
            api_key = Config.GEMINI_API_KEY
            if api_key and not api_key.startswith("your_"):
                configure(api_key=api_key)
                
                # Setup model with appropriate generation settings
                generation_config = {
                    "temperature": 0.3,  # Lower for more factual/consistent responses
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 500,
                }
                
                # Try different available models
                try:
                    # Try gemini-2.0-flash as first choice
                    self.genai_model = GenerativeModel(
                        model_name='gemini-2.0-flash', 
                        generation_config=generation_config
                    )
                except:
                    try:
                        # Fallback to gemini-1.5-flash
                        self.genai_model = GenerativeModel(
                            model_name='gemini-1.5-flash', 
                            generation_config=generation_config
                        )
                    except:
                        # Last resort: fall back to gemini-1.0
                        self.genai_model = GenerativeModel(
                            model_name='models/gemini-1.0-pro',
                            generation_config=generation_config
                        )
                        
                # Test with simple query
                test_response = self.get_gemini_response("Hello")
                self.genai_available = True
            else:
                self.genai_available = False
                self.genai_model = None
        except Exception as e:
            self.genai_available = False
            self.genai_model = None 