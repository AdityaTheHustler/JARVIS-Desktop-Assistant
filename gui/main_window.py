import tkinter as tk
from tkinter import ttk, simpledialog, scrolledtext
import threading
import time
import math
import random
from typing import Optional, Callable
import os
from PIL import Image, ImageTk, ImageDraw, ImageFilter

class IronManJarvisInterface(tk.Tk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("J.A.R.V.I.S.")
        self.geometry("1000x800")  # Larger window for immersive experience
        self.configure(bg="#0A0F18")  # Dark blue-black like Iron Man's screens
        self.minsize(900, 700)
        self.attributes('-alpha', 0.98)  # Slight transparency for modern look
        
        # Try to make window borderless on Windows
        try:
            self.attributes("-transparentcolor", "#0A0F18")
        except:
            pass
            
        # Create custom theme
        self._create_custom_theme()

        # Status variables
        self.is_listening = False
        self.is_processing = False
        self.toggle_listening_callback = None
        self.exit_callback = None
        self.test_input_callback = None
        
        # Animation variables
        self.angle = 0
        self.particles = []
        self.max_particles = 20
        self.pulse_size = 30
        self.energy_level = 0
        
        # Audio visualization variables
        self.frequency_data = [random.randint(2, 10) for _ in range(32)]  # Simulated frequency data
        self.spectrum_history = [[0] * 32 for _ in range(10)]  # Store last 10 frames of spectrum data
        self.voice_intensity = 0  # Overall voice intensity
        self.last_update = time.time()
        self.wave_offset = 0
        
        # Create main container
        self.container = tk.Frame(self, bg="#0A0F18")
        self.container.pack(fill="both", expand=True)
        
        # Create left panel for visualization
        self.left_panel = tk.Frame(self.container, bg="#0A0F18", width=350)
        self.left_panel.pack(side="left", fill="y", padx=10, pady=10)
        self.left_panel.pack_propagate(False)  # Don't shrink to fit contents
        
        # Create header with Jarvis logo
        self.header = tk.Frame(self.left_panel, bg="#0A0F18", height=150)
        self.header.pack(fill="x", pady=(20, 10))
        
        # Jarvis Logo
        self.logo_label = tk.Label(
            self.header,
            text="J.A.R.V.I.S.",
            font=("Arial", 28, "bold"),
            fg="#3D7EFF",
            bg="#0A0F18"
        )
        self.logo_label.pack(pady=10)
        
        self.subtitle_label = tk.Label(
            self.header,
            text="JUST A RATHER VERY INTELLIGENT SYSTEM",
            font=("Arial", 8),
            fg="#5D9CFF",
            bg="#0A0F18"
        )
        self.subtitle_label.pack()
        
        # Main circular animation canvas
        self.viz_frame = tk.Frame(self.left_panel, bg="#0A0F18")
        self.viz_frame.pack(fill="both", expand=True, pady=20)
        
        self.main_canvas = tk.Canvas(
            self.viz_frame,
            width=300,
            height=300,
            bg="#0A0F18",
            highlightthickness=0
        )
        self.main_canvas.pack(pady=10)
        
        # Status indicators below main animation
        self.status_frame = tk.Frame(self.left_panel, bg="#0A0F18", height=100)
        self.status_frame.pack(fill="x", pady=10)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="SYSTEM READY",
            font=("Arial", 12),
            fg="#3D7EFF",
            bg="#0A0F18"
        )
        self.status_label.pack(pady=(0, 10))
        
        # Voice activity visualization
        self.voice_canvas = tk.Canvas(
            self.status_frame,
            width=200,
            height=40,
            bg="#0A0F18",
            highlightthickness=0
        )
        self.voice_canvas.pack(pady=5)
        self.create_voice_bars()
        
        # Right panel for interaction
        self.right_panel = tk.Frame(self.container, bg="#0D131F")
        self.right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Top bar with system indicators
        self.top_bar = tk.Frame(self.right_panel, bg="#0D131F", height=40)
        self.top_bar.pack(fill="x", pady=(0, 10))
        
        self.system_indicators = []
        indicator_texts = ["CPU", "MEM", "NET", "SYS"]
        for i, text in enumerate(indicator_texts):
            indicator = tk.Label(
                self.top_bar,
                text=f"{text}: OPTIMAL",
                font=("Consolas", 9),
                fg="#3498db",
                bg="#0D131F",
                padx=10
            )
            indicator.pack(side="left")
            self.system_indicators.append(indicator)
        
        self.time_label = tk.Label(
            self.top_bar,
            text=time.strftime("%H:%M:%S"),
            font=("Consolas", 9),
            fg="#3498db",
            bg="#0D131F"
        )
        self.time_label.pack(side="right", padx=10)
        
        # Conversation area
        self.conversation_frame = tk.Frame(self.right_panel, bg="#0D131F")
        self.conversation_frame.pack(fill="both", expand=True, pady=10)
        
        # Conversation header
        self.conversation_header = tk.Frame(self.conversation_frame, bg="#0D131F", height=30)
        self.conversation_header.pack(fill="x")
        
        self.conversation_title = tk.Label(
            self.conversation_header,
            text="INTERACTIVE SESSION",
            font=("Arial", 12),
            fg="#3498db",
            bg="#0D131F"
        )
        self.conversation_title.pack(side="left", padx=10)
        
        self.typing_indicator = tk.Label(
            self.conversation_header,
            text="",
            font=("Arial", 10),
            fg="#F5C2E7",
            bg="#0D131F"
        )
        self.typing_indicator.pack(side="right", padx=10)
        self.typing_animation_active = False
        
        # Futuristic scrollbar style
        self.conversation_text = scrolledtext.ScrolledText(
            self.conversation_frame,
            font=("Consolas", 11),
            bg="#0F1723",
            fg="#7FDBFF",
            insertbackground="#3498db",
            selectbackground="#2C3E50",
            selectforeground="#ECF0F1",
            wrap=tk.WORD,
            padx=15,
            pady=15,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#1B3045",
            highlightcolor="#3498db"
        )
        self.conversation_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.conversation_text.tag_configure("user", foreground="#ECF0F1", font=("Consolas", 11, "bold"))
        self.conversation_text.tag_configure("assistant", foreground="#3498db", font=("Consolas", 11))
        self.conversation_text.tag_configure("timestamp", foreground="#34495E", font=("Consolas", 9))
        self.conversation_text.tag_configure("thinking", foreground="#F39C12", font=("Consolas", 11, "italic"))
        self.conversation_text.tag_configure("system", foreground="#E74C3C", font=("Consolas", 10))
        self.conversation_text.config(state=tk.DISABLED)  # Make it read-only
        
        # Add some futuristic elements to the text area
        self.add_conversation_text("SYSTEM", "J.A.R.V.I.S. initialization complete. All systems nominal.")
        self.add_conversation_text("SYSTEM", "Voice recognition active. Enhanced UI activated. Awaiting input.")
        
        # Control panel
        self.control_panel = tk.Frame(self.right_panel, bg="#0D131F", height=100)
        self.control_panel.pack(fill="x", pady=10)
        
        # Input field with futuristic design
        self.input_frame = tk.Frame(self.control_panel, bg="#0D131F")
        self.input_frame.pack(fill="x", pady=10)
        
        self.text_input = tk.Entry(
            self.input_frame,
            font=("Consolas", 12),
            bg="#0F1723",
            fg="#ECF0F1",
            insertbackground="#3498db",
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#1B3045",
            highlightcolor="#3498db"
        )
        self.text_input.pack(side="left", fill="x", expand=True, padx=(5, 10))
        self.text_input.bind("<Return>", self._on_input_enter)
        
        # Control buttons in a grid layout
        self.button_frame = tk.Frame(self.control_panel, bg="#0D131F")
        self.button_frame.pack(fill="x", pady=5)
        
        # Create futuristic buttons
        self.buttons = []
        button_data = [
            {"text": "ACTIVATE", "command": self._toggle_listening, "color": "#3498db", "width": 10},
            {"text": "SEND", "command": self._on_send_click, "color": "#2ECC71", "width": 8},
            {"text": "CLEAR", "command": self._clear_conversation, "color": "#E74C3C", "width": 8},
            {"text": "EXIT", "command": self._dummy_callback, "color": "#9B59B6", "width": 8}
        ]
        
        for i, data in enumerate(button_data):
            button = tk.Button(
                self.button_frame,
                text=data["text"],
                command=data["command"],
                font=("Arial", 10, "bold"),
                bg="#0F1723",
                fg=data["color"],
                activebackground="#1B3045",
                activeforeground=data["color"],
                relief=tk.FLAT,
                borderwidth=0,
                highlightthickness=1,
                highlightbackground=data["color"],
                width=data["width"],
                pady=5,
                cursor="hand2"
            )
            button.pack(side="left", padx=5)
            self.buttons.append(button)
        
        # Initialize main circle with pulse effect
        self.create_main_circle()
        
        # Start animations
        self.after(50, self.update_animations)
        self.after(1000, self.update_time)
        self.after(100, self.update_system_indicators)
        
        # Bind focus to input field
        self.bind("<FocusIn>", lambda e: self.text_input.focus_set())
        
    def _toggle_listening(self):
        """Toggle listening state (internal function)."""
        if self.toggle_listening_callback:
            self.toggle_listening_callback()
        else:
            self._dummy_callback()
    
    def create_main_circle(self):
        """Create the main animated circular interface with audio visualization."""
        # Clear canvas
        self.main_canvas.delete("all")
        
        # Update audio frequency data
        self.update_frequency_data()
        
        # Create base dark circle with gradient effect - without using alpha values
        base_colors = ["#1a5fb4", "#1c71d8", "#2481ea", "#3584e4", "#3d8ff5"]
        for i in range(5):
            size = 5 - i
            self.main_canvas.create_oval(
                50 - i*5, 50 - i*5, 250 + i*5, 250 + i*5,
                fill="",
                outline=base_colors[i],
                width=size,
                tags=f"base{i}"
            )
        
        # Add circular audio spectrum
        self.draw_circular_spectrum(self.main_canvas, 150, 150, 120)
        
        # Create inner rotating ring with length based on frequency
        for i in range(0, 360, 15):
            angle = math.radians(i + self.angle)
            # Get frequency magnitude for this angle
            freq_index = int((i / 360) * len(self.frequency_data)) % len(self.frequency_data)
            freq_magnitude = self.frequency_data[freq_index] / 20.0  # Normalize to 0-1
            
            # Use frequency to determine line length
            line_length = 5 + 15 * freq_magnitude
            
            x1 = 150 + 80 * math.cos(angle)
            y1 = 150 + 80 * math.sin(angle)
            x2 = 150 + (80 + line_length) * math.cos(angle)
            y2 = 150 + (80 + line_length) * math.sin(angle)
            
            # Color intensity based on frequency - ensure valid hex format
            intensity = int(150 + 105 * freq_magnitude)
            color = f"#{min(255, intensity):02x}{min(255, intensity+40):02x}ff"
            self.main_canvas.create_line(
                x1, y1, x2, y2,
                fill=color,
                width=2,
                tags="ring"
            )
        
        # Add second ring rotating opposite direction
        for i in range(0, 360, 30):
            angle = math.radians(i - self.angle * 0.7)
            freq_index = int((i / 360) * len(self.frequency_data)) % len(self.frequency_data)
            freq_magnitude = self.frequency_data[freq_index] / 20.0
            
            line_length = 5 + 10 * freq_magnitude
            
            x1 = 150 + 95 * math.cos(angle)
            y1 = 150 + 95 * math.sin(angle)
            x2 = 150 + (95 + line_length) * math.cos(angle)
            y2 = 150 + (95 + line_length) * math.sin(angle)
            
            # Different color for second ring - ensure valid hex format
            intensity = int(130 + 125 * freq_magnitude)
            color = f"#{min(180, intensity):02x}{min(255, intensity+50):02x}ff"
            self.main_canvas.create_line(
                x1, y1, x2, y2,
                fill=color,
                width=2,
                tags="ring2"
            )
        
        # Create arc segments around the main circle - respond to voice
        arc_intensity = int(self.voice_intensity * 2.55)
        # Ensure a valid color is always used by setting minimum values
        arc_color = f"#{max(0, min(255, arc_intensity)):02x}{max(0, min(255, arc_intensity+40)):02x}ff"
        
        for i in range(0, 360, 45):
            start_angle = i + self.angle % 60
            # Arc length based on voice intensity
            arc_extent = 15 + int(self.voice_intensity / 10)
            
            self.main_canvas.create_arc(
                35, 35, 265, 265,
                start=start_angle,
                extent=arc_extent,
                outline=arc_color,
                style=tk.ARC,
                width=2,
                tags="arc"
            )
        
        # Add animated scanning lines (like radar)
        scan_angle = (self.angle * 2) % 360
        scan_rad = math.radians(scan_angle)
        
        # Fix semi-transparent colors - remove alpha values as Tkinter might not support them
        self.main_canvas.create_line(
            150, 150,
            150 + 130 * math.cos(scan_rad),
            150 + 130 * math.sin(scan_rad),
            fill="#62a0ea",  # Change from #62a0ea80 to full opacity
            width=2,
            tags="scan",
            dash=(3, 3)  # Dashed line
        )
        
        # Create secondary scan line (slower)
        scan_angle2 = (self.angle * 0.5) % 360
        scan_rad2 = math.radians(scan_angle2)
        
        self.main_canvas.create_line(
            150, 150,
            150 + 130 * math.cos(scan_rad2),
            150 + 130 * math.sin(scan_rad2),
            fill="#ed333b",  # Change from #ed333b80 to full opacity
            width=2,
            tags="scan2",
            dash=(5, 2)
        )
        
        # Central energy core - size pulsates with voice intensity
        core_size = 20 + self.pulse_size + (self.voice_intensity * 0.2)
        
        # Create multi-layer core for better visual effect - without using alpha values
        core_colors = ["#3584e4", "#4a90d9", "#5aa0e6"]
        for i in range(3):
            layer_size = core_size * (1 - i*0.2)
            self.main_canvas.create_oval(
                150 - layer_size, 150 - layer_size,
                150 + layer_size, 150 + layer_size,
                fill="",
                outline=core_colors[i],
                width=3-i,
                tags=f"core{i}"
            )
        
        # Inner core glow - color shifts with activity
        inner_core = 15 + self.pulse_size * 0.5
        if self.is_processing:
            # Orange/yellow core when processing - ensure valid hex format
            r_val = min(255, 180+int(self.pulse_size*5))
            g_val = min(255, 100+int(self.pulse_size*8))
            core_color = f"#{r_val:02x}{g_val:02x}00"
        elif self.is_listening:
            # Blue/cyan core when listening - ensure valid hex format
            g_val = min(255, 150+int(self.pulse_size*5))
            b_val = min(255, 200+int(self.pulse_size*8))
            core_color = f"#00{g_val:02x}{b_val:02x}"
        else:
            # Default blue core
            core_color = "#3584e4"
            
        self.main_canvas.create_oval(
            150 - inner_core, 150 - inner_core,
            150 + inner_core, 150 + inner_core,
            fill=core_color,
            outline="",
            tags="inner_core"
        )
        
        # Add particles
        self.update_particles()
        
        # Add holographic data display (text indicators)
        # Top indicator
        if self.is_processing:
            status = "ANALYSIS IN PROGRESS"
        elif self.is_listening:
            status = "VOICE RECOGNITION ACTIVE"
        else:
            status = "SYSTEMS NOMINAL"
            
        self.main_canvas.create_text(
            150, 30,
            text=status,
            fill="#3584e4",
            font=("Arial", 9, "bold"),
            tags="status_text"
        )
        
        # Bottom mode indicator
        status_text = "LISTENING" if self.is_listening else "STANDBY"
        self.main_canvas.create_text(
            150, 260,
            text=status_text,
            fill="#3584e4",
            font=("Arial", 9),
            tags="mode_text"
        )
        
        # Add energy level indicator
        energy_text = f"ENERGY: {int(self.energy_level)}%  |  VOICE: {int(self.voice_intensity)}%"
        self.main_canvas.create_text(
            150, 280,
            text=energy_text,
            fill="#3584e4",
            font=("Consolas", 8),
            tags="energy_text"
        )
        
        # Add scanning status indicator
        scan_text = f"SCAN: {int(self.angle * 100 / 360)}%"
        self.main_canvas.create_text(
            150, 295,
            text=scan_text,
            fill="#3584e4",
            font=("Consolas", 8),
            tags="scan_text"
        )
    
    def create_voice_bars(self):
        """Create voice activity visualization bars."""
        self.voice_canvas.delete("all")
        
        # Create background
        self.voice_canvas.create_rectangle(
            0, 0, 200, 40,
            fill="#0F1723",
            outline="#1B3045",
            width=1
        )
        
        # Create initial bars
        self.bars = []
        for i in range(20):
            height = 5  # Default height
            bar = self.voice_canvas.create_rectangle(
                i * 10 + 5, 20 - height, 
                i * 10 + 10, 20 + height,
                fill="#3498db",
                outline="",
                tags="bar"
            )
            self.bars.append(bar)
    
    def update_voice_bars(self):
        """Update voice activity visualization."""
        if self.is_listening:
            for i, bar in enumerate(self.bars):
                if i % 2 == 0:
                    height = random.randint(2, 15)
                else:
                    height = random.randint(1, 10)
                
                self.voice_canvas.coords(
                    bar,
                    i * 10 + 5, 20 - height, 
                    i * 10 + 10, 20 + height
                )
                
                # Color based on height (more activity = brighter color)
                intensity = min(255, int(height * 12))
                # Ensure valid hex values
                blue = 255  # Full blue
                green = min(255, intensity + 50)
                color = f"#{intensity:02x}{green:02x}{blue:02x}"
                self.voice_canvas.itemconfig(bar, fill=color)
        else:
            for bar in self.bars:
                height = 2
                self.voice_canvas.coords(
                    bar,
                    int(self.voice_canvas.coords(bar)[0]), 20 - height,
                    int(self.voice_canvas.coords(bar)[2]), 20 + height
                )
                self.voice_canvas.itemconfig(bar, fill="#1B3045")
    
    def update_particles(self):
        """Update energy particles around the core."""
        # Remove old particles
        for particle in self.particles:
            self.main_canvas.delete(particle)
        self.particles = []
        
        # Add new particles if the system is active
        if self.is_listening or self.is_processing:
            particle_count = min(int(self.energy_level / 5), self.max_particles)
            for _ in range(particle_count):
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(40, 110)
                size = random.uniform(1, 3)
                x = 150 + distance * math.cos(angle)
                y = 150 + distance * math.sin(angle)
                
                # More energy = brighter particles
                intensity = min(255, int(self.energy_level * 2.5))
                blue = 255  # Always full blue
                green = min(255, intensity + 50)
                # Ensure the color format is valid hex
                color = f"#{intensity:02x}{green:02x}{blue:02x}"
                
                particle = self.main_canvas.create_oval(
                    x - size, y - size,
                    x + size, y + size,
                    fill=color,
                    outline="",
                    tags="particle"
                )
                self.particles.append(particle)
    
    def update_animations(self):
        """Update all animations on the interface."""
        # Update angle for rotation
        self.angle = (self.angle + 1) % 360
        
        # Update pulse size
        if self.is_listening or self.is_processing:
            # Target higher energy when active
            self.energy_level = min(100, self.energy_level + 1)
            # Pulse effect
            self.pulse_size = 5 + 3 * math.sin(time.time() * 5)
        else:
            # Lower energy in standby
            self.energy_level = max(20, self.energy_level - 0.5)
            self.pulse_size = 3 + math.sin(time.time() * 2)
        
        # Redraw main interface
        self.create_main_circle()
        
        # Update voice visualization
        self.update_voice_bars()
        
        # Schedule next update
        self.after(50, self.update_animations)
    
    def update_time(self):
        """Update time display."""
        self.time_label.config(text=time.strftime("%H:%M:%S"))
        self.after(1000, self.update_time)
    
    def update_system_indicators(self):
        """Update system indicators with some random fluctuations."""
        systems = ["CPU", "MEM", "NET", "SYS"]
        statuses = ["OPTIMAL", "NOMINAL"]
        
        for i, indicator in enumerate(self.system_indicators):
            # 10% chance to change status for more dynamic feel
            if random.random() < 0.1:
                status = random.choice(statuses)
                indicator.config(text=f"{systems[i]}: {status}")
                
        # Schedule next update
        self.after(3000, self.update_system_indicators)
        
    def _create_custom_theme(self):
        """Create custom theme for futuristic appearance."""
        style = ttk.Style()
        
        # Define Iron Man color palette
        bg_color = "#0A0F18"      # Dark blue-black background
        fg_color = "#ECF0F1"      # Light text
        accent_color = "#3498db"  # Iron Man blue
        highlight_color = "#E74C3C"  # Iron Man red
        button_bg = "#0F1723"
        
        # Configure styles
        style.configure("Dark.TFrame", background=bg_color)
        style.configure("TButton", background=button_bg, foreground=fg_color, font=("Arial", 10, "bold"))
        style.configure("Accent.TButton", background=accent_color, foreground=bg_color, font=("Arial", 10, "bold"))
        style.configure("Danger.TButton", background=highlight_color, foreground=bg_color, font=("Arial", 10, "bold"))
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        style.configure("Title.TLabel", background=bg_color, foreground=accent_color)
        style.configure("Status.TLabel", background=bg_color, foreground=highlight_color)
        style.configure("Typing.TLabel", background=bg_color, foreground="#F5C2E7")
        style.configure("Input.TEntry", fieldbackground=button_bg, foreground=fg_color)
        
        # Map styles for button states
        style.map("TButton",
                  background=[("active", "#1B3045"), ("pressed", "#2C3E50")],
                  foreground=[("active", accent_color)])
        style.map("Accent.TButton",
                  background=[("active", "#2980b9"), ("pressed", "#2471a3")],
                  foreground=[("active", fg_color)])
        style.map("Danger.TButton",
                  background=[("active", "#C0392B"), ("pressed", "#A93226")],
                  foreground=[("active", fg_color)])
    
    def _dummy_callback(self):
        """Placeholder callback for buttons."""
        if self.is_processing:
            return
        
        self.add_conversation_text("SYSTEM", "Function not implemented in demo mode.")
            
    def _test_input(self):
        """Open a dialog to get test input and process it."""
        if self.test_input_callback:
            dialog = simpledialog.askstring("Command Input", "Enter command:", parent=self)
            if dialog:
                self.text_input.delete(0, tk.END)
                self.text_input.insert(0, dialog)
                self._on_send_click()
    
    def _on_input_enter(self, event):
        """Handle enter key in the input field."""
        self._on_send_click()
    
    def _on_send_click(self):
        """Process the input text when Send is clicked."""
        text = self.text_input.get().strip()
        if not text:
            return
            
        # Disable input during processing
        self.text_input.config(state="disabled")
        self.buttons[1].config(state="disabled")  # Disable send button
        
        # Set processing state
        self.is_processing = True
        self.update_status("PROCESSING INQUIRY")
        self.start_typing_animation()
        
        # Call the callback if set
        if self.test_input_callback:
            self.test_input_callback(text)
        
        # Clear the input field
        self.text_input.config(state="normal")
        self.text_input.delete(0, tk.END)
        self.text_input.focus_set()
        self.buttons[1].config(state="normal")
    
    def _clear_conversation(self):
        """Clear the conversation history."""
        self.conversation_text.config(state=tk.NORMAL)
        self.conversation_text.delete(1.0, tk.END)
        self.conversation_text.config(state=tk.DISABLED)
        
        # Add system message
        self.add_conversation_text("SYSTEM", "Conversation history cleared.")

    def update_status(self, text: str):
        """Update status label with new text."""
        self.status_label.config(text=text)
        if text == "READY" or text == "SYSTEM READY":
            self.stop_typing_animation()
            self.is_processing = False

    def start_typing_animation(self):
        """Start typing indicator animation."""
        if not self.typing_animation_active:
            self.typing_animation_active = True
            self._update_typing_animation(0)
    
    def _update_typing_animation(self, count):
        """Update typing animation dots."""
        if not self.typing_animation_active:
            self.typing_indicator.config(text="")
            return
            
        indicators = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.typing_indicator.config(text=f"PROCESSING {indicators[count % len(indicators)]}")
        self.after(100, self._update_typing_animation, count + 1)
    
    def stop_typing_animation(self):
        """Stop typing indicator animation."""
        self.typing_animation_active = False
        self.typing_indicator.config(text="")

    def set_listening_state(self, is_listening: bool):
        """Update interface based on listening state."""
        self.is_listening = is_listening
        
        if is_listening:
            self.update_status("VOICE RECOGNITION ACTIVE")
            self.buttons[0].config(text="DEACTIVATE")
            self.energy_level = min(100, self.energy_level + 20)  # Boost energy when listening
        else:
            self.update_status("SYSTEM READY")
            self.buttons[0].config(text="ACTIVATE")

    def set_callbacks(self, toggle_callback: Callable, exit_callback: Callable, test_input_callback: Callable = None):
        """Set callbacks for interface actions."""
        self.toggle_listening_callback = toggle_callback
        self.exit_callback = exit_callback
        self.test_input_callback = test_input_callback
        
        # Update button commands
        if exit_callback:
            self.buttons[3].config(command=exit_callback)  # Exit button

    def add_conversation_text(self, speaker: str, text: str):
        """Add text to the conversation with formatting."""
        self.conversation_text.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = time.strftime("%H:%M:%S")
        self.conversation_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Add speaker and text with appropriate formatting
        if speaker.upper() == "SYSTEM":
            self.conversation_text.insert(tk.END, f"{speaker}: ", "system")
            self.conversation_text.insert(tk.END, f"{text}\n\n", "system")
        elif speaker.upper() == "YOU":
            self.conversation_text.insert(tk.END, f"{speaker}: ", "user")
            self.conversation_text.insert(tk.END, f"{text}\n\n", "user")
        else:
            self.conversation_text.insert(tk.END, f"{speaker}: ", "assistant")
            self.conversation_text.insert(tk.END, f"{text}\n\n", "assistant")
            
            # Reset processing state
            self.is_processing = False
            self.stop_typing_animation()
            self.update_status("SYSTEM READY")
        
        self.conversation_text.see(tk.END)
        self.conversation_text.config(state=tk.DISABLED)
    
    def show_thinking(self):
        """Show 'thinking' animation in the conversation."""
        self.conversation_text.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.conversation_text.insert(tk.END, f"[{timestamp}] PROCESSING QUERY...\n", "thinking")
        self.conversation_text.see(tk.END)
        self.conversation_text.config(state=tk.DISABLED)

    def on_closing(self):
        """Handle window closing."""
        if self.exit_callback:
            self.exit_callback()
        else:
            self.destroy()

    def update_frequency_data(self):
        """Simulate and update frequency data based on voice activity."""
        # In a real implementation, this would read from microphone data
        # For now, we'll simulate frequencies based on listening/processing state
        
        if self.is_listening:
            # Generate dynamic frequency data when listening
            # More variation in higher frequencies and stronger bass
            for i in range(32):
                if i < 8:  # Bass frequencies (stronger when speaking)
                    self.frequency_data[i] = min(20, max(5, 
                        self.frequency_data[i] + random.uniform(-2, 3)))
                elif i < 16:  # Mid-range frequencies
                    self.frequency_data[i] = min(15, max(2, 
                        self.frequency_data[i] + random.uniform(-1.5, 2)))
                else:  # High frequencies (more sporadic)
                    self.frequency_data[i] = min(10, max(1, 
                        self.frequency_data[i] + random.uniform(-1, 1.5)))
                        
            # Overall voice intensity increases more dramatically when listening
            self.voice_intensity = min(100, self.voice_intensity + random.uniform(-5, 7))
            
        elif self.is_processing:
            # When processing, frequencies should be more stable but still active
            for i in range(32):
                # Less variation during processing, more organized pattern
                self.frequency_data[i] = min(18, max(3, 
                    self.frequency_data[i] + random.uniform(-1, 1.2)))
            
            # Processing voice intensity should be more stable
            self.voice_intensity = min(100, max(40, 
                self.voice_intensity + random.uniform(-2, 3)))
        else:
            # In standby mode, minimal frequency activity
            for i in range(32):
                # Tendency toward lower values when inactive
                self.frequency_data[i] = max(1, 
                    self.frequency_data[i] * 0.95 + random.uniform(0, 0.8))
            
            # Voice intensity decreases in standby
            self.voice_intensity = max(10, self.voice_intensity * 0.98)
        
        # Update the spectrum history (shift and add new data)
        self.spectrum_history.pop(0)  # Remove oldest frame
        self.spectrum_history.append(self.frequency_data.copy())  # Add current frame
        
        # Update wave offset for flowing animations
        self.wave_offset = (self.wave_offset + 0.05) % (2 * math.pi)

    def draw_circular_spectrum(self, canvas, x, y, radius):
        """Draw a circular audio spectrum visualization."""
        # Calculate time difference for smoother animations
        now = time.time()
        dt = min(0.1, now - self.last_update)  # Cap at 0.1 seconds to prevent large jumps
        self.last_update = now
        
        # Number of frequency bands to display
        bands = len(self.frequency_data)
        
        # Create outer spectrum ring
        for i in range(bands):
            # Calculate angle for this frequency band
            angle = 2 * math.pi * i / bands
            
            # Get normalized magnitude of this frequency band (0-1)
            magnitude = self.frequency_data[i] / 20.0  # Max value is 20
            
            # Calculate line coordinates
            inner_radius = radius * 0.8
            outer_radius = radius * (0.8 + 0.2 * magnitude)
            
            x1 = x + inner_radius * math.cos(angle)
            y1 = y + inner_radius * math.sin(angle)
            x2 = x + outer_radius * math.cos(angle)
            y2 = y + outer_radius * math.sin(angle)
            
            # Color scales with intensity - blue to cyan to white
            intensity = int(magnitude * 255)
            r = min(255, int(intensity * 0.5))
            g = min(255, int(intensity * 0.8))
            b = 255
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            canvas.create_line(x1, y1, x2, y2, fill=color, width=2, tags="spectrum")
        
        # Draw internal frequency waves (circular)
        for j in range(3):  # Draw 3 internal circular waves
            points = []
            wave_radius = radius * (0.4 - j * 0.1)  # Different radii for each wave
            wave_phase = self.wave_offset + j * math.pi / 4  # Different phases
            
            for i in range(0, 360, 5):  # 5-degree intervals
                rad_angle = math.radians(i)
                # Calculate wave amplitude based on frequency content
                freq_index = int((i / 360) * bands) % bands
                wave_height = self.frequency_data[freq_index] / 40.0  # Smaller amplitude
                
                # Apply sine wave modulation
                wave_mod = 0.05 * math.sin(rad_angle * 6 + wave_phase)
                r = wave_radius * (1 + wave_height + wave_mod)
                
                points.append(x + r * math.cos(rad_angle))
                points.append(y + r * math.sin(rad_angle))
            
            # Choose color based on wave index
            wave_colors = ["#1a5fb4", "#3584e4", "#62a0ea"]
            canvas.create_polygon(points, fill="", outline=wave_colors[j], width=1.5, smooth=True, tags="wave")

# For backwards compatibility
ModernCircularInterface = IronManJarvisInterface
CircularInterface = IronManJarvisInterface 