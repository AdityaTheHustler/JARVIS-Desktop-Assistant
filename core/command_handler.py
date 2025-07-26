from typing import Dict, List, Optional, Callable
import re
from datetime import datetime
import json
import os
from features.social_media import SocialMediaManager
from features.system_control import SystemController
# Comment out the face recognition import
# from features.face_recognition import FaceRecognitionManager
from features.task_scheduler import TaskScheduler, Task, TaskType
from features.web_search import WebSearch
from features.email_manager import EmailManager
from utils.config import Config

class CommandHandler:
    def __init__(self):
        self.social_media = SocialMediaManager()
        self.system_control = SystemController()
        # Comment out the face recognition initialization
        # self.face_recognition = FaceRecognitionManager()
        self.task_scheduler = TaskScheduler()
        self.web_search = WebSearch()
        self.email_manager = EmailManager()
        
        # Load command patterns
        self.command_patterns = self._load_command_patterns()
        
        # Start task scheduler
        self.task_scheduler.start()
        
        # Flag to enable or disable real search
        self.use_real_search = Config.USE_REAL_SEARCH
        
        # Last processed command and its response for context
        self.last_command = None
        self.last_response = None

    def _load_command_patterns(self) -> Dict[str, List[str]]:
        """Load command patterns from a JSON file."""
        try:
            with open('command_patterns.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default command patterns
            return {
                'greeting': [
                    r'hello',
                    r'hi( there)?',
                    r'hey',
                    r'good (morning|afternoon|evening)'
                ],
                'time': [
                    r'what time is it',
                    r'current time',
                    r'tell me the time'
                ],
                'date': [
                    r'what day is it',
                    r'what\'s the date',
                    r'current date',
                    r'what is today'
                ],
                'weather': [
                    r'weather (in|at) (.+)',
                    r'how\'s the weather (in|at) (.+)',
                    r'temperature (in|at) (.+)',
                    r'is it (hot|cold|raining|sunny) (in|at) (.+)'
                ],
                'news': [
                    r'latest news',
                    r'what\'s happening',
                    r'current events',
                    r'news about (.+)'
                ],
                'system': [
                    r'(shutdown|restart|sleep|lock) (computer|system)',
                    r'turn (off|on) (computer|system)',
                    r'(system|computer) (status|performance|stats|info)',
                    r'(monitor|check) (system|computer) (performance|resources|usage)',
                    r'how\'s my (system|computer) (doing|performing)',
                    r'(cpu|memory|disk|ram) usage'
                ],
                'social_media': [
                    r'like posts from (.+)',
                    r'upload post (.+)',
                    r'follow (.+)',
                    r'unfollow (.+)'
                ],
                'task': [
                    r'remind me to (.+)',
                    r'set alarm for (.+)',
                    r'schedule (.+)',
                    r'remind me (at|in) (.+) to (.+)',
                    r'set (a|an) (alarm|reminder) (for|at) (.+)',
                    r'wake me up at (.+)'
                ],
                'search': [
                    r'search for (.+)',
                    r'look up (.+)',
                    r'find information about (.+)',
                    r'what is (.+)',
                    r'tell me about (.+)',
                    r'who is (.+)',
                    r'where is (.+)'
                ],
                'youtube': [
                    r'play (.+) on youtube',
                    r'search youtube for (.+)',
                    r'find videos (about|on) (.+)'
                ],
                'translate': [
                    r'translate (.+) to (.+)',
                    r'how do you say (.+) in (.+)'
                ],
                'email': [
                    r'check (my )?(email|emails|inbox)',
                    r'any new (email|emails|messages)',
                    r'send (an )?email to (.+)',
                    r'read (my )?(email|emails|messages)',
                    r'search (my )?(email|emails) for (.+)'
                ]
            }

    def process_command(self, command: str) -> str:
        """Process a voice command and return a response."""
        command = command.lower().strip()
        self.last_command = command
        
        # Check each command pattern
        for category, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command)
                if match:
                    response = self._execute_command(category, match)
                    self.last_response = response
                    return response
        
        # If no pattern matches, use web search for questions
        if self._is_question(command):
            response = self._handle_search(command)
            self.last_response = response
            return response
            
        # For other inputs, return None to let the main AI handle it
        return None
    
    def _is_question(self, text: str) -> bool:
        """Check if the text is a question that should be handled by search."""
        question_words = ['what', 'who', 'where', 'when', 'why', 'how', 'is', 'are', 'can', 'could', 'would', 'should', 'do', 'does']
        text_words = text.split()
        
        # Check if it starts with a question word
        if text_words and text_words[0] in question_words:
            return True
            
        # Check if it contains keywords indicating a search or information request
        search_terms = ['search', 'find', 'look up', 'tell me about', 'information on', 'data about']
        for term in search_terms:
            if term in text:
                return True
                
        return False

    def _execute_command(self, category: str, match: re.Match) -> str:
        """Execute the appropriate command based on category."""
        try:
            if category == 'greeting':
                return self._handle_greeting()
            elif category == 'time':
                return self._handle_time()
            elif category == 'date':
                return self._handle_date()
            elif category == 'weather':
                # Get the city from the match groups
                if len(match.groups()) >= 2:  # New pattern with (in|at) and city
                    return self._handle_weather(match.groups()[-1])  # Last group is city
                else:
                    return "Please specify a city for weather information."
            elif category == 'news':
                # Check if we have a topic in the match groups
                if len(match.groups()) >= 1 and match.groups()[0]:
                    return self._handle_news(match.groups()[0])
                return self._handle_news()
            elif category == 'system':
                return self._handle_system_command(match.group(1) if match.groups() else "")
            elif category == 'social_media':
                return self._handle_social_media(match.group(1) if match.groups() else "")
            elif category == 'task':
                return self._handle_task(match.group(1) if match.groups() else "")
            elif category == 'search':
                return self._handle_search(match.group(1) if match.groups() else "")
            elif category == 'youtube':
                # Check if we have a topic in the match groups
                if len(match.groups()) >= 2:  # New pattern with (about|on) and topic
                    return self._handle_youtube(match.groups()[-1])  # Last group is topic
                elif len(match.groups()) >= 1:
                    return self._handle_youtube(match.groups()[0])
                return "Please specify what to search on YouTube."
            elif category == 'translate':
                if len(match.groups()) >= 2:
                    return self._handle_translate(match.group(1), match.group(2))
                return "I need both text and target language to translate."
            elif category == 'email':
                return self._handle_email(match.group(1) if match.groups() else "")
            elif category == 'gemini':
                return self._handle_gemini_query(match.group(1) if match.groups() else "")
            else:
                return "I'm not sure how to handle that command."
        except Exception as e:
            print(f"Error executing command: {e}")
            return f"I encountered an error while processing your command: {str(e)}"

    def _handle_greeting(self) -> str:
        """Handle greeting commands."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning! How can I help you today?"
        elif 12 <= hour < 17:
            return "Good afternoon! What can I do for you?"
        else:
            return "Good evening! How may I assist you?"

    def _handle_time(self) -> str:
        """Handle time-related commands."""
        current_time = datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}"

    def _handle_date(self) -> str:
        """Handle date-related commands."""
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {current_date}"

    def _handle_weather(self, city: str) -> str:
        """Handle weather-related commands."""
        if not city:
            return "Please specify a city for weather information."
            
        weather_info = self.web_search.get_weather(city)
        if weather_info:
            return (f"The temperature in {city} is {weather_info['temperature']}°C, "
                   f"with {weather_info['description']}. "
                   f"Humidity is {weather_info['humidity']}% and "
                   f"wind speed is {weather_info['wind_speed']} m/s.")
        return f"Sorry, I couldn't get the weather information for {city}"

    def _handle_news(self, topic: str = None) -> str:
        """Handle news-related commands."""
        if topic:
            # Search for news on a specific topic
            results = self.web_search.search_google(f"latest news about {topic}")
            if results:
                response = f"Here are some recent news articles about {topic}:\n"
                for result in results[:3]:
                    response += f"- {result['title']}\n"
                return response
            return f"Sorry, I couldn't find any recent news about {topic}"
        
        # General news
        news = self.web_search.get_news()
        if news:
            response = "Here are the latest headlines:\n"
            for article in news[:3]:
                response += f"- {article['title']}\n"
            return response
        return "Sorry, I couldn't fetch the latest news"

    def _handle_system_command(self, command: str) -> str:
        """Handle system control commands."""
        if not command:
            return "Please specify a system command."
            
        if 'status' in command or 'performance' in command or 'stats' in command or 'info' in command or ('usage' in command and any(x in command for x in ['cpu', 'memory', 'disk', 'ram'])):
            return self._handle_system_monitoring()
        elif 'shutdown' in command or 'off' in command:
            self.system_control.shutdown_system()
            return "Shutting down the system"
        elif 'restart' in command:
            self.system_control.restart_system()
            return "Restarting the system"
        elif 'sleep' in command:
            self.system_control.sleep_system()
            return "Putting the system to sleep"
        elif 'lock' in command:
            self.system_control.lock_system()
            return "Locking the system"
        return "I'm not sure what system action you want to perform"
        
    def _handle_system_monitoring(self) -> str:
        """Handle system monitoring commands."""
        metrics = self.system_control.get_performance_metrics()
        
        if 'error' in metrics:
            return f"Sorry, I couldn't get the system metrics: {metrics['error']}"
            
        # Format the response
        response = "Current system status:\n"
        response += f"CPU: {metrics['cpu_percent']}% usage across {metrics['cpu_cores']} cores ({metrics['cpu_threads']} threads)\n"
        response += f"Memory: {metrics['memory_used']} used of {metrics['memory_total']} ({metrics['memory_percent']}%)\n"
        response += f"Disk: {metrics['disk_used']} used of {metrics['disk_total']} ({metrics['disk_percent']}%)\n"
        
        # Add battery info if available
        if metrics['battery_percent'] is not None:
            response += f"Battery: {metrics['battery_percent']}%"
            if metrics['battery_time_left']:
                response += f" ({metrics['battery_time_left']} remaining)"
            response += "\n"
            
        # Add top processes
        if 'top_processes' in metrics and metrics['top_processes']:
            response += "\nTop CPU-consuming processes:\n"
            for proc in metrics['top_processes'][:3]:  # Show only top 3 to keep response shorter
                response += f"- {proc['name']}: {proc['cpu_percent']:.1f}% CPU, {proc['memory_percent']:.1f}% Memory\n"
                
        return response

    def _handle_social_media(self, command: str) -> str:
        """Handle social media commands."""
        if not command:
            return "Please specify a social media action."
            
        if command.startswith('like'):
            username = command.split('from ')[1]
            liked_posts = self.social_media.like_recent_posts(username)
            return f"Liked {len(liked_posts)} recent posts from {username}"
        elif command.startswith('upload'):
            # Handle post upload
            return "Post upload functionality not implemented yet"
        elif command.startswith('follow'):
            username = command.split('follow ')[1]
            if self.social_media.follow_user(username):
                return f"Now following {username}"
            return f"Could not follow {username}"
        elif command.startswith('unfollow'):
            username = command.split('unfollow ')[1]
            if self.social_media.unfollow_user(username):
                return f"Unfollowed {username}"
            return f"Could not unfollow {username}"
        return "I'm not sure what social media action you want to perform"

    def _handle_task(self, command: str) -> str:
        """Handle task scheduling commands."""
        if not command:
            return "Please specify a task to schedule."
        
        # Check if it's an alarm
        if command.lower().startswith(('wake me', 'alarm')):
            # Extract time information
            time_info = re.search(r'(at|in|for)\s+(.+)', command)
            if time_info:
                time_str = time_info.group(2)
                alarm = self.task_scheduler.create_alarm(time_str)
                if alarm:
                    return f"I've set an alarm for {alarm.scheduled_time.strftime('%I:%M %p on %A, %B %d')}"
                return "I couldn't understand when to set the alarm. Please specify a time like '7:30 AM' or 'tomorrow at 9'."
        
        # Check if it's a reminder at a specific time
        time_match = re.search(r'(at|in|on|tomorrow|next)\s+(.+?)\s+to\s+(.+)', command)
        if time_match:
            time_str = time_match.group(2)
            task_desc = time_match.group(3)
            reminder = self.task_scheduler.create_reminder(task_desc, time_str)
            if reminder:
                return f"I'll remind you to {task_desc} at {reminder.scheduled_time.strftime('%I:%M %p on %A, %B %d')}"
            return "I couldn't understand when to set the reminder. Please specify a time like '7:30 PM' or 'tomorrow at 9'."
        
        # Check if it's a timer
        if 'timer' in command.lower():
            duration_match = re.search(r'(\d+)\s+(minute|hour|second)s?', command)
            if duration_match:
                duration_str = f"{duration_match.group(1)} {duration_match.group(2)}s"
                timer = self.task_scheduler.create_timer(duration_str)
                if timer:
                    return f"I've set a timer for {duration_str}"
                return "I couldn't understand the timer duration. Please specify like '5 minutes' or '1 hour'."
        
        # Default: create a basic reminder for the near future (30 minutes)
        reminder = self.task_scheduler.create_reminder(command, "in 30 minutes")
        if reminder:
            return f"I've scheduled a reminder for: {command} in 30 minutes"
        return "Sorry, I couldn't schedule that task"

    def _handle_search(self, query: str) -> str:
        """Handle web search commands."""
        if not query:
            return "Please specify a search query."
            
        # Try to get Wikipedia summary first
        wiki_results = self.web_search.get_wikipedia_summary(query)
        if wiki_results and wiki_results.get('extract') and len(wiki_results['extract']) > 10:
            return f"Here's what I found about {query}:\n{wiki_results['extract']}"
        
        # If no Wikipedia results, try Google search
        results = self.web_search.search_google(query)
        if results:
            response = f"Here's what I found about {query}:\n"
            for result in results[:2]:
                response += f"- {result['title']}: {result['snippet']}\n"
            return response
        
        # If all else fails, try Gemini response
        return self._handle_gemini_query(query)

    def _handle_youtube(self, query: str) -> str:
        """Handle YouTube search commands."""
        if not query:
            return "Please specify what to search on YouTube."
            
        videos = self.web_search.search_youtube(query)
        if videos:
            response = f"I found videos about {query}. Here are the top results:\n"
            for i, video in enumerate(videos[:2]):
                response += f"{i+1}. {video['title']}\n"
            return response
        return f"Sorry, I couldn't find any videos about {query}"

    def _handle_translate(self, text: str, target_lang: str) -> str:
        """Handle translation commands."""
        if not text or not target_lang:
            return "I need both text and target language to translate."
            
        translated = self.web_search.translate_text(text, target_lang)
        return f"The translation of '{text}' to {target_lang} is: {translated}"
        
    def _handle_gemini_query(self, query: str) -> str:
        """Handle direct Gemini AI queries."""
        if not query:
            return "Please specify what to ask Gemini."
            
        response = self.web_search.get_gemini_response(query)
        return response

    def _handle_email(self, command: str) -> str:
        """Handle email-related commands."""
        if not command:
            return "Please specify an email action."
            
        if command.startswith('check'):
            return self._handle_check_email()
        elif command.startswith('send'):
            return self._handle_send_email(command)
        elif command.startswith('read'):
            return self._handle_read_email(command)
        elif command.startswith('search'):
            return self._handle_search_email(command)
        return "I'm not sure what email action you want to perform"

    def _handle_check_email(self) -> str:
        """Handle email checking commands."""
        email_count = self.email_manager.check_email()
        return f"You have {email_count} new email(s) in your inbox."

    def _handle_send_email(self, command: str) -> str:
        """Handle email sending commands."""
        parts = command.split(maxsplit=2)
        if len(parts) < 3:
            return "Please specify the recipient, subject, and message."
            
        recipient = parts[1]
        subject = parts[2]
        message = " ".join(parts[3:])
        
        if self.email_manager.send_email(recipient, subject, message):
            return f"Email sent to {recipient} with subject '{subject}'"
        return "Sorry, I couldn't send the email"

    def _handle_read_email(self, command: str) -> str:
        """Handle email reading commands."""
        if not command:
            return "Please specify an email to read."
            
        email = self.email_manager.read_email(command)
        if email:
            return f"Here's the content of the email:\n{email}"
        return "Sorry, I couldn't find that email"

    def _handle_search_email(self, query: str) -> str:
        """Handle email searching commands."""
        if not query:
            return "Please specify a search query."
            
        emails = self.email_manager.search_email(query)
        if emails:
            response = f"Here are the emails matching your search:\n"
            for email in emails[:3]:
                response += f"- {email['subject']} - {email['sender']}\n"
            return response
        return "Sorry, I couldn't find any emails matching your search"

    def _handle_unknown_command(self, command: str) -> str:
        """Handle commands that don't match any pattern."""
        # First try to see if it's a question or search query
        if self._is_question(command):
            return self._handle_search(command)
            
        # Try AI for a conversational response
        try:
            # Include context of last command if available
            context = ""
            if self.last_command and self.last_response:
                context = f"Based on the previous discussion where I asked '{self.last_command}' and you responded with information about {self.last_response[:30]}..., "
                
            contextual_query = f"{context}{command}"
            return self.web_search.get_gemini_response(contextual_query)
        except Exception as e:
            # Return generic response if all else fails
            return "I'm not sure how to respond to that. Can you try rephrasing or asking a specific question?" 