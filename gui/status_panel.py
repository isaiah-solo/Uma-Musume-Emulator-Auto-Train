import customtkinter as ctk
import tkinter as tk

class StatusPanel(ctk.CTkFrame):
    def __init__(self, parent, main_window, colors):
        super().__init__(parent, fg_color=colors['bg_medium'], corner_radius=15)
        self.main_window = main_window
        self.colors = colors

        # Title label
        title_label = ctk.CTkLabel(self, text="Real-time Status", font=ctk.CTkFont(size=16, weight="bold"), text_color=colors['text_light'])
        title_label.pack(pady=(15, 10))

        # Create status display widgets
        self.create_status_widgets()

        # Initialize with default values
        self.update_status("Unknown Year", 0.0, "Unknown", "Unknown", False, {})
    
    def create_status_widgets(self):
        """Create all status display widgets with modern rounded cards"""
        # Main content frame - no expand to prevent blank space
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Top row - Year and Energy (modern rounded cards)
        top_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Year display card
        year_card = ctk.CTkFrame(top_frame, fg_color=self.colors['bg_light'], corner_radius=8)
        year_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        ctk.CTkLabel(year_card, text="YEAR", font=ctk.CTkFont(size=10, weight="bold"), text_color=self.colors['text_gray']).pack(pady=(8, 2))
        self.year_label = ctk.CTkLabel(year_card, text="Unknown", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors['text_light'])
        self.year_label.pack(pady=(0, 8))
        
        # Energy display card
        energy_card = ctk.CTkFrame(top_frame, fg_color=self.colors['bg_light'], corner_radius=8)
        energy_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ctk.CTkLabel(energy_card, text="ENERGY", font=ctk.CTkFont(size=10, weight="bold"), text_color=self.colors['text_gray']).pack(pady=(8, 2))
        self.energy_label = ctk.CTkLabel(energy_card, text="0.0%", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors['text_light'])
        self.energy_label.pack(pady=(0, 8))
        
        # Middle row - Turn, Mood, Goal (modern rounded cards)
        middle_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        middle_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Turn display card
        turn_card = ctk.CTkFrame(middle_frame, fg_color=self.colors['bg_light'], corner_radius=8)
        turn_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        ctk.CTkLabel(turn_card, text="TURN", font=ctk.CTkFont(size=10, weight="bold"), text_color=self.colors['text_gray']).pack(pady=(8, 2))
        self.turn_label = ctk.CTkLabel(turn_card, text="Unknown", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_light'])
        self.turn_label.pack(pady=(0, 8))
        
        # Mood display card
        mood_card = ctk.CTkFrame(middle_frame, fg_color=self.colors['bg_light'], corner_radius=8)
        mood_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        ctk.CTkLabel(mood_card, text="MOOD", font=ctk.CTkFont(size=10, weight="bold"), text_color=self.colors['text_gray']).pack(pady=(8, 2))
        self.mood_label = ctk.CTkLabel(mood_card, text="Unknown", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_light'])
        self.mood_label.pack(pady=(0, 8))
        
        # Goal display card
        goal_card = ctk.CTkFrame(middle_frame, fg_color=self.colors['bg_light'], corner_radius=8)
        goal_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ctk.CTkLabel(goal_card, text="GOAL", font=ctk.CTkFont(size=10, weight="bold"), text_color=self.colors['text_gray']).pack(pady=(8, 2))
        self.goal_label = ctk.CTkLabel(goal_card, text="❓", font=ctk.CTkFont(size=18), text_color=self.colors['text_light'])
        self.goal_label.pack(pady=(0, 8))
        
        # Bottom row - Stats (beautiful stat cards)
        stats_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        stats_frame.pack(fill=tk.X)
        
        # Create stat display cards
        self.stat_labels = {}
        stats = ['SPD', 'STA', 'PWR', 'GUTS', 'WIT']
        
        for i, stat in enumerate(stats):
            stat_card = ctk.CTkFrame(stats_frame, fg_color=self.colors['bg_light'], corner_radius=8)
            stat_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 3) if i < len(stats) - 1 else (0, 0))
            
            ctk.CTkLabel(stat_card, text=stat, font=ctk.CTkFont(size=9, weight="bold"), text_color=self.colors['text_gray']).pack(pady=(6, 2))
            stat_label = ctk.CTkLabel(stat_card, text="0", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors['text_light'])
            stat_label.pack(pady=(0, 6))
            self.stat_labels[stat.lower()] = stat_label
    
    def update_status(self, year, energy, turn, mood, goal_met, stats):
        """Update the status panel with real-time data"""
        # Update year
        self.year_label.configure(text=str(year))
        
        # Update energy
        self.energy_label.configure(text=f"{energy:.1f}%")
        
        # Update turn
        self.turn_label.configure(text=str(turn))
        
        # Update mood
        self.mood_label.configure(text=str(mood))
        
        # Update goal status
        if goal_met:
            self.goal_label.configure(text="✅", text_color=self.colors['accent_green'])
        else:
            self.goal_label.configure(text="❌", text_color=self.colors['accent_red'])
        
        # Update stats
        for stat_name, stat_label in self.stat_labels.items():
            stat_value = stats.get(stat_name, 0)
            stat_label.configure(text=str(stat_value))
    
    def update_from_bot_data(self, bot_data):
        """Update status from bot data dictionary"""
        year = bot_data.get('year', 'Unknown Year')
        energy = bot_data.get('energy', 0.0)
        turn = bot_data.get('turn', 'Unknown')
        mood = bot_data.get('mood', 'Unknown')
        goal_met = bot_data.get('goal_met', False)
        stats = bot_data.get('stats', {})
        
        self.update_status(year, energy, turn, mood, goal_met, stats)
