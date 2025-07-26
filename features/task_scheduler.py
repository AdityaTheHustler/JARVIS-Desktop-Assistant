import threading
import time
from typing import Dict, List, Callable, Optional
from datetime import datetime, timedelta
import json
import os
from dataclasses import dataclass
from enum import Enum
import uuid
import re

class TaskType(Enum):
    REMINDER = "reminder"
    ALARM = "alarm"
    TASK = "task"
    TIMER = "timer"

@dataclass
class Task:
    id: str
    title: str
    description: str
    task_type: TaskType
    scheduled_time: datetime
    completed: bool = False
    recurrence: str = None
    notification_callback: Optional[Callable] = None
    next_run_time: datetime = None

    def to_dict(self) -> Dict:
        """Convert task to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type.value,
            "scheduled_time": self.scheduled_time.isoformat(),
            "completed": self.completed,
            "recurrence": self.recurrence
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """Create task from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            task_type=TaskType(data["task_type"]),
            scheduled_time=datetime.fromisoformat(data["scheduled_time"]),
            recurrence=data.get("recurrence"),
        )
        
    def update_next_run_time(self):
        """Update the next run time based on recurrence."""
        if not self.recurrence:
            return
            
        now = datetime.now()
        
        if self.recurrence == "daily":
            self.next_run_time = datetime(
                now.year, now.month, now.day,
                self.scheduled_time.hour, self.scheduled_time.minute, 0
            ) + timedelta(days=1)
        elif self.recurrence == "weekly":
            # Schedule for next week, same day of week
            days_ahead = 7
            self.next_run_time = datetime(
                now.year, now.month, now.day,
                self.scheduled_time.hour, self.scheduled_time.minute, 0
            ) + timedelta(days=days_ahead)
        elif self.recurrence == "monthly":
            # Schedule for next month, same day of month
            month = now.month + 1
            year = now.year
            if month > 12:
                month = 1
                year += 1
            # Handle day overflow (e.g., Feb 30 -> Feb 28/29)
            day = min(self.scheduled_time.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
            self.next_run_time = datetime(
                year, month, day,
                self.scheduled_time.hour, self.scheduled_time.minute, 0
            )
        
        
class TaskScheduler:
    def __init__(self):
        self.tasks: List[Task] = []
        self.running = False
        self.thread = None
        self.check_interval = 10  # seconds
        self.task_file = "tasks.json"
        self.notification_callback = None
        self.load_tasks()

    def start(self) -> None:
        """Start the task scheduler thread."""
        if self.thread is not None and self.thread.is_alive():
            return  # Already running
            
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        print("Task scheduler started")
        
    def stop(self) -> None:
        """Stop the task scheduler thread."""
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        print("Task scheduler stopped")
        
    def _scheduler_loop(self):
        """Main scheduler loop to check for due tasks."""
        while self.running:
            now = datetime.now()
            
            for task in self.tasks:
                if not task.completed and task.next_run_time <= now:
                    self._trigger_task(task)
                    
                    # Handle recurrence
                    if task.recurrence:
                        task.completed = False
                        task.update_next_run_time()
                    else:
                        task.completed = True
                        
            # Save tasks after processing
            self.save_tasks()
                    
            # Sleep until next check
            time.sleep(self.check_interval)
            
    def _trigger_task(self, task: Task):
        """Trigger a task notification."""
        message = f"{task.task_type.value.capitalize()}: {task.title}"
        
        # Use notification callback if available
        if task.notification_callback:
            task.notification_callback(task)
        elif self.notification_callback:
            self.notification_callback(message, task.description)
        else:
            print(f"NOTIFICATION: {message} - {task.description}")
            
    def set_notification_callback(self, callback: Callable):
        """Set a notification callback function."""
        self.notification_callback = callback
            
    def add_task(self, task: Task) -> bool:
        """Add a new task to the scheduler."""
        self.tasks.append(task)
        self.save_tasks()
        return True
        
    def remove_task(self, task_id: str) -> bool:
        """Remove a task by ID."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                self.tasks.pop(i)
                self.save_tasks()
                return True
        return False
        
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
        
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return self.tasks
        
    def get_upcoming_tasks(self, limit: int = 5) -> List[Task]:
        """Get upcoming tasks sorted by scheduled time."""
        now = datetime.now()
        upcoming = [t for t in self.tasks if not t.completed and t.scheduled_time > now]
        upcoming.sort(key=lambda x: x.scheduled_time)
        return upcoming[:limit]
        
    def save_tasks(self):
        """Save tasks to JSON file."""
        try:
            with open(self.task_file, "w") as f:
                json.dump([t.to_dict() for t in self.tasks], f, indent=2)
        except Exception as e:
            print(f"Error saving tasks: {e}")
            
    def load_tasks(self):
        """Load tasks from JSON file."""
        try:
            if os.path.exists(self.task_file):
                with open(self.task_file, "r") as f:
                    data = json.load(f)
                    self.tasks = [Task.from_dict(t) for t in data]
        except Exception as e:
            print(f"Error loading tasks: {e}")
            
    def parse_natural_time(self, time_str: str) -> Optional[datetime]:
        """Parse natural language time strings into datetime objects."""
        now = datetime.now()
        time_str = time_str.lower().strip()
        
        # Check for specific time formats
        try:
            # Try exact time (HH:MM)
            time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', time_str)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or 0)
                am_pm = time_match.group(3)
                
                # Adjust for AM/PM
                if am_pm == 'pm' and hour < 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
                
                # Create datetime for today with specified time
                result = datetime(now.year, now.month, now.day, hour, minute)
                
                # If the time is in the past, schedule for tomorrow
                if result < now:
                    result += timedelta(days=1)
                    
                return result
        except ValueError:
            pass
            
        # Common time expressions
        if 'tomorrow' in time_str:
            result = now + timedelta(days=1)
            # Check if a specific time is mentioned
            time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', time_str)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or 0)
                am_pm = time_match.group(3)
                
                # Adjust for AM/PM
                if am_pm == 'pm' and hour < 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
                    
                result = datetime(result.year, result.month, result.day, hour, minute)
            else:
                # Default to 9 AM if no specific time
                result = datetime(result.year, result.month, result.day, 9, 0)
                
            return result
            
        # Check for "in X minutes/hours"
        time_offset_match = re.search(r'in\s+(\d+)\s+(minute|hour|day)s?', time_str)
        if time_offset_match:
            value = int(time_offset_match.group(1))
            unit = time_offset_match.group(2)
            
            if unit == 'minute':
                return now + timedelta(minutes=value)
            elif unit == 'hour':
                return now + timedelta(hours=value)
            elif unit == 'day':
                return now + timedelta(days=value)
                
        # Check for weekdays
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        for day, day_num in weekdays.items():
            if day in time_str:
                days_ahead = (day_num - now.weekday()) % 7
                if days_ahead == 0:  # Same day, schedule for next week
                    days_ahead = 7
                    
                result = now + timedelta(days=days_ahead)
                
                # Check if a specific time is mentioned
                time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', time_str)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2) or 0)
                    am_pm = time_match.group(3)
                    
                    # Adjust for AM/PM
                    if am_pm == 'pm' and hour < 12:
                        hour += 12
                    elif am_pm == 'am' and hour == 12:
                        hour = 0
                        
                    result = datetime(result.year, result.month, result.day, hour, minute)
                else:
                    # Default to 9 AM if no specific time
                    result = datetime(result.year, result.month, result.day, 9, 0)
                    
                return result
                
        # Failed to parse
        return None
        
    def create_reminder(self, title: str, time_str: str, description: str = None, recurrence: str = None) -> Optional[Task]:
        """Create a new reminder task from natural language time description."""
        scheduled_time = self.parse_natural_time(time_str)
        
        if not scheduled_time:
            return None
            
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description or title,
            task_type=TaskType.REMINDER,
            scheduled_time=scheduled_time,
            recurrence=recurrence,
            notification_callback=self.notification_callback
        )
        
        self.add_task(task)
        return task
        
    def create_alarm(self, time_str: str, title: str = "Alarm", recurrence: str = None) -> Optional[Task]:
        """Create a new alarm task from natural language time description."""
        scheduled_time = self.parse_natural_time(time_str)
        
        if not scheduled_time:
            return None
            
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=f"Alarm for {scheduled_time.strftime('%I:%M %p')}",
            task_type=TaskType.ALARM,
            scheduled_time=scheduled_time,
            recurrence=recurrence,
            notification_callback=self.notification_callback
        )
        
        self.add_task(task)
        return task
        
    def create_timer(self, duration_str: str, title: str = "Timer") -> Optional[Task]:
        """Create a timer for a specific duration (e.g., '5 minutes')."""
        now = datetime.now()
        duration_match = re.search(r'(\d+)\s+(minute|hour|second)s?', duration_str.lower())
        
        if not duration_match:
            return None
            
        value = int(duration_match.group(1))
        unit = duration_match.group(2)
        
        if unit == 'second':
            scheduled_time = now + timedelta(seconds=value)
        elif unit == 'minute':
            scheduled_time = now + timedelta(minutes=value)
        elif unit == 'hour':
            scheduled_time = now + timedelta(hours=value)
        else:
            return None
            
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=f"Timer for {value} {unit}{'s' if value > 1 else ''}",
            task_type=TaskType.TIMER,
            scheduled_time=scheduled_time,
            notification_callback=self.notification_callback
        )
        
        self.add_task(task)
        return task 