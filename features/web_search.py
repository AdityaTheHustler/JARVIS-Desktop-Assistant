import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Optional
from datetime import datetime
import os
from utils.config import Config

# Try to import Google AI library, but don't fail if not available
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("Advanced AI functionality not available for web search.")

class WebSearch:
    def __init__(self):
        self.google_api_key = Config.GOOGLE_API_KEY
        self.gemini_api_key = Config.GEMINI_API_KEY
        self.search_engine_id = Config.SEARCH_ENGINE_ID  # Custom Search Engine ID
        self.use_gemini = False
        self.gemini_model = None
        self.genai_available = False  # Initialize the flag
        
        # Try to initialize with AI for enhanced responses
        try:
            self.api_key = Config.GEMINI_API_KEY
            if self.api_key and not self.api_key.startswith("your_"):
                genai.configure(api_key=self.api_key)
                
                # Setup model with appropriate generation settings
                generation_config = {
                    "temperature": 0.3,  # Lower for more factual/consistent responses
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 500,
                }
                
                # Try different available models
                try:
                    self.model = genai.GenerativeModel(
                        model_name='gemini-2.0-flash', 
                        generation_config=generation_config
                    )
                except Exception as e:
                    try:
                        self.model = genai.GenerativeModel(
                            model_name='gemini-1.5-flash', 
                            generation_config=generation_config
                        )
                    except Exception as e:
                        try:
                            self.model = genai.GenerativeModel(
                                model_name='models/gemini-1.0-pro',
                                generation_config=generation_config
                            )
                        except Exception as e:
                            # No models available
                            self.model = None
                            self.genai_available = False
                
                # Test with simple query
                if self.model:
                    try:
                        test_response = self.get_ai_response("Hello")
                        print(f"Web search test response: {test_response}")
                        self.genai_available = True
                    except Exception as e:
                        self.genai_available = False
                        print("Error initializing advanced search capabilities")
                else:
                    self.genai_available = False
            else:
                self.genai_available = False
        except Exception as e:
            self.genai_available = False
            print("Error initializing advanced search")

    def search_google(self, query: str, num_results: int = 5) -> List[Dict]:
        """Search Google using the Custom Search API."""
        if not self.google_api_key or self.google_api_key.startswith("your_") or not self.search_engine_id or self.search_engine_id.startswith("your_"):
            # Fall back to simulation if API key is not configured
            return self._simulate_search(query)
            
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': min(num_results, 10)  # API limits to 10 results max
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', 'No title'),
                    'link': item.get('link', '#'),
                    'snippet': item.get('snippet', 'No description')
                })
                
            return results
        except Exception as e:
            print(f"Error searching Google: {e}")
            # Fall back to simulation
            return self._simulate_search(query)

    def _simulate_search(self, query: str) -> List[Dict]:
        """Provide simulated search results when API is not available."""
        print(f"Simulating Google search for: {query}")
        results = [
            {
                'title': f'Example result 1 for {query}',
                'link': f'https://example.com/result1?q={query}',
                'snippet': f'This is an example snippet for {query}...'
            },
            {
                'title': f'Example result 2 for {query}',
                'link': f'https://example.com/result2?q={query}',
                'snippet': f'Another example snippet for {query}...'
            }
        ]
        return results

    def get_gemini_response(self, query: str) -> str:
        """Get a response from the Gemini model for a simple query."""
        try:
            if not self.genai_available or not self.model:
                return self._get_simulated_response(query)
                
            response = self.model.generate_content(query)
            if hasattr(response, 'text'):
                return response.text
            return self._get_simulated_response(query)
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return self._get_simulated_response(query)
    
    def get_ai_response(self, query: str) -> str:
        """Alias for get_gemini_response for cleaner naming."""
        return self.get_gemini_response(query)

    def get_news(self, category: Optional[str] = None) -> List[Dict]:
        """Get news articles using NewsAPI."""
        news_api_key = os.getenv("NEWS_API_KEY")
        if not news_api_key:
            return self._simulate_news(category)
            
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'apiKey': news_api_key,
                'country': 'us',  # Default to US news
            }
            
            if category:
                params['category'] = category
                
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for item in data.get('articles', []):
                articles.append({
                    'title': item.get('title', 'No title'),
                    'description': item.get('description', 'No description'),
                    'url': item.get('url', '#'),
                    'published_at': item.get('publishedAt', datetime.now().isoformat()),
                    'source': item.get('source', {}).get('name', 'Unknown source')
                })
                
            return articles
        except Exception as e:
            print(f"Error getting news: {e}")
            return self._simulate_news(category)
    
    def _simulate_news(self, category: Optional[str] = None) -> List[Dict]:
        """Simulate news results when API is not available."""
        print(f"Simulating news fetch for category: {category or 'general'}")
        articles = [
            {
                'title': 'Example News Headline 1',
                'description': 'This is an example news article description.',
                'url': 'https://example.com/news/1',
                'published_at': datetime.now().isoformat(),
                'source': 'Example News Source'
            },
            {
                'title': 'Example News Headline 2',
                'description': 'This is another example news article description.',
                'url': 'https://example.com/news/2',
                'published_at': datetime.now().isoformat(),
                'source': 'Example News Source'
            }
        ]
        return articles

    def get_weather(self, city: str) -> Dict:
        """Get weather information using OpenWeatherMap API."""
        weather_api_key = os.getenv("WEATHER_API_KEY")
        if not weather_api_key:
            return self._simulate_weather(city)
            
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': city,
                'appid': weather_api_key,
                'units': 'metric'  # Use metric units
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'temperature': data.get('main', {}).get('temp', 0),
                'description': data.get('weather', [{}])[0].get('description', 'unknown'),
                'humidity': data.get('main', {}).get('humidity', 0),
                'wind_speed': data.get('wind', {}).get('speed', 0),
                'city': city
            }
        except Exception as e:
            print(f"Error getting weather: {e}")
            return self._simulate_weather(city)
    
    def _simulate_weather(self, city: str) -> Dict:
        """Simulate weather data when API is not available."""
        print(f"Simulating weather fetch for city: {city}")
        return {
            'temperature': 22.5,
            'description': 'partly cloudy',
            'humidity': 65,
            'wind_speed': 5.2,
            'city': city
        }

    def search_youtube(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search YouTube using YouTube Data API."""
        youtube_api_key = self.google_api_key
        if not youtube_api_key or youtube_api_key.startswith("your_"):
            return self._simulate_youtube_search(query)
            
        try:
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'key': youtube_api_key,
                'q': query,
                'part': 'snippet',
                'type': 'video',
                'maxResults': max_results
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = []
            
            for item in data.get('items', []):
                video_id = item.get('id', {}).get('videoId', '')
                snippet = item.get('snippet', {})
                
                videos.append({
                    'title': snippet.get('title', 'No title'),
                    'description': snippet.get('description', 'No description'),
                    'video_id': video_id,
                    'thumbnail': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                    'published_at': snippet.get('publishedAt', datetime.now().isoformat())
                })
                
            return videos
        except Exception as e:
            print(f"Error searching YouTube: {e}")
            return self._simulate_youtube_search(query)
    
    def _simulate_youtube_search(self, query: str) -> List[Dict]:
        """Simulate YouTube search results when API is not available."""
        print(f"Simulating YouTube search for: {query}")
        videos = [
            {
                'title': f'Example YouTube video 1 for {query}',
                'description': f'This is an example YouTube video about {query}',
                'video_id': 'dQw4w9WgXcQ',
                'thumbnail': 'https://example.com/thumbnail1.jpg',
                'published_at': datetime.now().isoformat()
            },
            {
                'title': f'Example YouTube video 2 for {query}',
                'description': f'Another example YouTube video about {query}',
                'video_id': '9bZkp7q19f0',
                'thumbnail': 'https://example.com/thumbnail2.jpg',
                'published_at': datetime.now().isoformat()
            }
        ]
        return videos

    def get_wikipedia_summary(self, query: str) -> Dict:
        """Get a summary about a topic from Wikipedia."""
        try:
            # First try to use the Wikipedia API
            import wikipedia
            try:
                page = wikipedia.page(query)
                summary = wikipedia.summary(query, sentences=3)
                return {
                    'title': page.title,
                    'summary': summary,
                    'url': page.url
                }
            except Exception as e:
                print(f"Error getting Wikipedia summary: {e}")
                
                # Try using AI if Wikipedia fails
                if GENAI_AVAILABLE and self.genai_available:
                    try:
                        ai_response = self.model.generate_content(
                            f"Provide a concise summary of '{query}' in about 100 words."
                        )
                        
                        if hasattr(ai_response, 'text'):
                            return {
                                'title': query,
                                'summary': ai_response.text,
                                'url': f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
                            }
                    except Exception as e:
                        print(f"Error getting AI summary: {e}")
                
                # Fall back to simulation if both fail
                return self._simulate_wikipedia_summary(query)
        except ImportError:
            print("Wikipedia package not installed")
            return self._simulate_wikipedia_summary(query)
    
    def _simulate_wikipedia_summary(self, query: str) -> Dict:
        """Simulate Wikipedia summary when API is not available."""
        print(f"Simulating Wikipedia summary for: {query}")
        
        # Provide better simulated responses for common topics
        query_lower = query.lower()
        
        if "india" in query_lower:
            extract = "India is a country in South Asia. It is the seventh-largest country by area, the second-most populous country, and the most populous democracy in the world. India has a rich cultural history spanning over 4,500 years. It's known for its diverse geography, languages, religions, and cuisine."
        elif "python" in query_lower:
            extract = "Python is a high-level, interpreted programming language known for its readability and versatility. Created by Guido van Rossum and first released in 1991, Python emphasizes code readability with its notable use of significant whitespace. Its language constructs and object-oriented approach aim to help programmers write clear, logical code."
        elif "artificial intelligence" in query_lower or "ai" == query_lower:
            extract = "Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to natural intelligence displayed by humans or animals. Leading AI textbooks define the field as the study of 'intelligent agents': any system that perceives its environment and takes actions that maximize its chance of achieving its goals."
        else:
            extract = f"This is a simulated Wikipedia extract about {query}. In a real implementation, this would contain factual information about the topic from Wikipedia or another knowledge source."
        
        return {
            'title': query.title(),
            'extract': extract,
            'url': f'https://en.wikipedia.org/wiki/{query.replace(" ", "_")}'
        }

    def translate_text(self, text: str, target_language: str) -> str:
        """Translate text using Google Translate API."""
        if not self.google_api_key or self.google_api_key.startswith("your_"):
            return self._simulate_translation(text, target_language)
            
        try:
            url = "https://translation.googleapis.com/language/translate/v2"
            params = {
                'key': self.google_api_key,
                'q': text,
                'target': target_language
            }
            
            response = requests.post(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            translations = data.get('data', {}).get('translations', [])
            
            if translations:
                return translations[0].get('translatedText', '')
            return self._simulate_translation(text, target_language)
        except Exception as e:
            print(f"Error translating text: {e}")
            return self._simulate_translation(text, target_language)
    
    def _simulate_translation(self, text: str, target_language: str) -> str:
        """Simulate translation when API is not available."""
        print(f"Simulating translation of '{text}' to {target_language}")
        return f"[This would be '{text}' translated to {target_language}]"

    def get_stock_info(self, symbol: str) -> Dict:
        """Get stock market information."""
        try:
            # Using Alpha Vantage API (you'll need to sign up for an API key)
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': 'your_alphavantage_api_key'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            quote = data.get('Global Quote', {})
            return {
                'symbol': symbol,
                'price': quote.get('05. price'),
                'change': quote.get('09. change'),
                'change_percent': quote.get('10. change percent'),
                'volume': quote.get('06. volume')
            }
        except Exception as e:
            print(f"Error getting stock info: {e}")
            return {}

    def _get_simulated_response(self, query: str) -> str:
        """Provide a simulated AI response when the model is not available."""
        # Add some basic knowledge for common queries
        query_lower = query.lower()
        
        if "india" in query_lower:
            return "India is a diverse country in South Asia with a rich history, vibrant culture, and the world's largest democracy. It's known for its ancient civilizations, religious diversity, cuisine, arts, and rapidly growing economy."
        
        elif "weather" in query_lower:
            return "I don't have access to real-time weather data. To get accurate weather information, I recommend checking a weather app or website for current conditions."
        
        elif "python" in query_lower:
            return "Python is a high-level, interpreted programming language known for its readability and versatility. It's widely used in web development, data analysis, artificial intelligence, and automation."
        
        elif "jarvis" in query_lower or "assistant" in query_lower:
            return "I'm Jarvis, an AI assistant designed to help with information, tasks, and conversations. I aim to be helpful, informative, and responsive to your needs."
            
        elif "developer" in query_lower or "created" in query_lower or "made" in query_lower or "built" in query_lower or "who made you" in query_lower or "who created you" in query_lower or "who developed you" in query_lower:
            return "I was developed by Aditya the Hustler. He created me as an advanced AI assistant."
        
        # Generic response for other queries
        return f"I can provide information about '{query}' but I'm currently running in reduced capability mode. For better results, ensure API access is properly configured." 