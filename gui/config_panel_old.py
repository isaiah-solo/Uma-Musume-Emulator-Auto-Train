import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os

class ConfigPanel(ctk.CTkFrame):
    def __init__(self, parent, main_window, colors):
        super().__init__(parent, fg_color=colors['bg_medium'], corner_radius=15)
        self.main_window = main_window
        self.colors = colors

        # Title label
        title_label = ctk.CTkLabel(self, text="CONFIG", font=ctk.CTkFont(size=16, weight="bold"), text_color=colors['text_light'])
        title_label.pack(pady=(15, 10))

        # Create tabview for different config sections (modern rounded tabs)
        self.tabview = ctk.CTkTabview(self, fg_color=colors['bg_light'], corner_radius=10)
        self.tabview.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Create all config tabs
        self.create_main_tab()
        self.create_training_tab()
        self.create_racing_tab()
        self.create_event_tab()
        self.create_skill_tab()
        self.create_others_tab()
        
        # Load training score config
        self.load_training_score_config()
        self.load_event_priority_config()
        self.load_skills_config()
    
    def create_main_tab(self):
        """Create the Main tab with ADB configuration"""
        # Add tab to tabview
        main_tab = self.tabview.add("Main")
        
        # ADB Configuration Frame
        adb_frame = ctk.CTkFrame(main_tab, fg_color=self.colors['bg_light'], corner_radius=10)
        adb_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # ADB Configuration Title
        adb_title = ctk.CTkLabel(adb_frame, text="ADB Configuration", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_light'])
        adb_title.pack(pady=(15, 10))
        
        # Device Address
        device_frame = ctk.CTkFrame(adb_frame, fg_color="transparent")
        device_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(device_frame, text="Device Address:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        self.device_address_var = tk.StringVar(value=self.main_window.get_config().get('adb_config', {}).get('device_address', '127.0.0.1:7555'))
        ctk.CTkEntry(device_frame, textvariable=self.device_address_var, width=200, corner_radius=8).pack(side=tk.RIGHT)
        
        # ADB Path
        adb_path_frame = ctk.CTkFrame(adb_frame, fg_color="transparent")
        adb_path_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(adb_path_frame, text="ADB Path:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        self.adb_path_var = tk.StringVar(value=self.main_window.get_config().get('adb_config', {}).get('adb_path', 'adb'))
        ctk.CTkEntry(adb_path_frame, textvariable=self.adb_path_var, width=200, corner_radius=8).pack(side=tk.RIGHT)
        
        # Screenshot Timeout
        timeout_frame = ctk.CTkFrame(adb_frame, fg_color="transparent")
        timeout_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(timeout_frame, text="Screenshot Timeout:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        self.screenshot_timeout_var = tk.IntVar(value=self.main_window.get_config().get('adb_config', {}).get('screenshot_timeout', 5))
        ctk.CTkEntry(timeout_frame, textvariable=self.screenshot_timeout_var, width=100, corner_radius=8).pack(side=tk.RIGHT)
        
        # Input Delay
        delay_frame = ctk.CTkFrame(adb_frame, fg_color="transparent")
        delay_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(delay_frame, text="Input Delay:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        self.input_delay_var = tk.DoubleVar(value=self.main_window.get_config().get('adb_config', {}).get('input_delay', 0.5))
        ctk.CTkEntry(delay_frame, textvariable=self.input_delay_var, width=100, corner_radius=8).pack(side=tk.RIGHT)
        
        # Connection Timeout
        conn_frame = ctk.CTkFrame(adb_frame, fg_color="transparent")
        conn_frame.pack(fill=tk.X, padx=15, pady=(5, 15))
        ctk.CTkLabel(conn_frame, text="Connection Timeout:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        self.connection_timeout_var = tk.IntVar(value=self.main_window.get_config().get('adb_config', {}).get('connection_timeout', 10))
        ctk.CTkEntry(conn_frame, textvariable=self.connection_timeout_var, width=100, corner_radius=8).pack(side=tk.RIGHT)
    
    def create_training_tab(self):
        """Create the Training tab with all training-related settings"""
        # Add tab to tabview
        training_tab = self.tabview.add("Training")
        
        # Placeholder content for now
        placeholder_label = ctk.CTkLabel(training_tab, text="Training settings coming soon...", text_color=self.colors['text_light'])
        placeholder_label.pack(pady=50)
        

        
        ttk.Label(priority_frame, text="Drag and drop to reorder priority:", style='Dark.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # Priority stats display (simplified for now - will implement drag and drop)
        self.priority_vars = []
        priority_container = ttk.Frame(priority_frame, style='Dark.TFrame')
        priority_container.pack(fill=tk.X)
        
        config = self.main_window.get_config()
        priority_stats = config.get('priority_stat', ['spd', 'sta', 'wit', 'pwr', 'guts'])
        
        for i, stat in enumerate(priority_stats):
            var = tk.StringVar(value=stat)
            self.priority_vars.append(var)
            ttk.Entry(priority_container, textvariable=var, style='Dark.TEntry', width=8).pack(side=tk.LEFT, padx=(0, 5))
        
        # Add/Remove buttons
        btn_frame = ttk.Frame(priority_frame, style='Dark.TFrame')
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="Add Stat", command=self.add_stat_field, style='Dark.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Remove Stat", command=self.remove_stat_field, style='Dark.TButton').pack(side=tk.LEFT)
        
        # Training Settings
        settings_frame = ttk.LabelFrame(training_frame, text="Training Settings", style='Dark.TLabelframe', padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Minimum Mood
        mood_frame = ttk.Frame(settings_frame, style='Dark.TFrame')
        mood_frame.pack(fill=tk.X, pady=5)
        ttk.Label(mood_frame, text="Minimum Mood:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.minimum_mood_var = tk.StringVar(value=config.get('minimum_mood', 'GREAT'))
        mood_combo = ttk.Combobox(mood_frame, textvariable=self.minimum_mood_var, 
                                 values=['GREAT', 'GOOD', 'NORMAL', 'BAD', 'AWFUL'], 
                                 state='readonly', style='Dark.TCombobox', width=15)
        mood_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Maximum Failure Rate
        fail_frame = ttk.Frame(settings_frame, style='Dark.TFrame')
        fail_frame.pack(fill=tk.X, pady=5)
        ttk.Label(fail_frame, text="Maximum Failure Rate:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.maximum_failure_var = tk.IntVar(value=config.get('maximum_failure', 15))
        ttk.Spinbox(fail_frame, from_=0, to=100, textvariable=self.maximum_failure_var, 
                   style='Dark.TSpinbox', width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Minimum Energy for Training
        energy_frame = ttk.Frame(settings_frame, style='Dark.TFrame')
        energy_frame.pack(fill=tk.X, pady=5)
        ttk.Label(energy_frame, text="Minimum Energy for Training:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.min_energy_var = tk.IntVar(value=config.get('min_energy', 30))
        ttk.Spinbox(energy_frame, from_=0, to=100, textvariable=self.min_energy_var, 
                   style='Dark.TSpinbox', width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Do Race if no good training found
        race_frame = ttk.Frame(settings_frame, style='Dark.TFrame')
        race_frame.pack(fill=tk.X, pady=5)
        self.do_race_var = tk.BooleanVar(value=config.get('do_race_when_bad_training', True))
        ttk.Checkbutton(race_frame, text="Do Race if no good training found", 
                       variable=self.do_race_var, style='Dark.TCheckbutton',
                       command=self.toggle_race_settings).pack(anchor=tk.W)
        
        # Race-related settings (initially hidden if do_race is False)
        self.race_settings_frame = ttk.Frame(settings_frame, style='Dark.TFrame')
        self.race_settings_frame.pack(fill=tk.X, pady=5)
        
        # Minimum Training Score
        score_frame = ttk.Frame(self.race_settings_frame, style='Dark.TFrame')
        score_frame.pack(fill=tk.X, pady=5)
        ttk.Label(score_frame, text="Minimum Training Score:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.min_score_var = tk.DoubleVar(value=config.get('min_score', 1.0))
        ttk.Spinbox(score_frame, from_=0.0, to=10.0, increment=0.1, textvariable=self.min_score_var, 
                   style='Dark.TSpinbox', width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Minimum WIT Training Score
        wit_score_frame = ttk.Frame(self.race_settings_frame, style='Dark.TFrame')
        wit_score_frame.pack(fill=tk.X, pady=5)
        ttk.Label(wit_score_frame, text="Minimum WIT Training Score:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.min_wit_score_var = tk.DoubleVar(value=config.get('min_wit_score', 1.0))
        ttk.Spinbox(wit_score_frame, from_=0.0, to=10.0, increment=0.1, textvariable=self.min_wit_score_var, 
                   style='Dark.TSpinbox', width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Stat Caps
        caps_frame = ttk.LabelFrame(training_frame, text="Stat Caps", style='Dark.TLabelframe', padding="10")
        caps_frame.pack(fill=tk.X, pady=(0, 10))
        
        caps_container = ttk.Frame(caps_frame, style='Dark.TFrame')
        caps_container.pack(fill=tk.X)
        
        self.stat_cap_vars = {}
        stat_caps = config.get('stat_caps', {})
        stats = ['spd', 'sta', 'pwr', 'guts', 'wit']
        
        for i, stat in enumerate(stats):
            # Stat name label
            ttk.Label(caps_container, text=stat.upper(), style='Dark.TLabel').grid(row=0, column=i, pady=(0, 5))
            # Stat cap input
            var = tk.IntVar(value=stat_caps.get(stat, 600))
            self.stat_cap_vars[stat] = var
            ttk.Spinbox(caps_container, from_=0, to=2000, textvariable=var, 
                       style='Dark.TSpinbox', width=8).grid(row=1, column=i, padx=2)
        
        # Training Score (collapsible)
        self.create_training_score_section(training_frame)
        
        # Save button
        ttk.Button(training_frame, text="Save Training Settings", 
                  command=self.save_training_settings, style='Config.TButton').pack(pady=10)
    
    def create_training_score_section(self, parent):
        """Create the collapsible training score section"""
        # Training Score Frame
        score_frame = ttk.LabelFrame(parent, text="Training Score (Click to expand)", style='Dark.TLabelframe', padding="5")
        score_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Collapsible content
        self.score_content_frame = ttk.Frame(score_frame, style='Dark.TFrame')
        
        # Training score variables
        self.rainbow_support_var = tk.DoubleVar(value=1.0)
        self.low_bond_support_var = tk.DoubleVar(value=0.7)
        self.high_bond_support_var = tk.DoubleVar(value=0.0)
        self.hint_var = tk.DoubleVar(value=0.3)
        
        # Bind click event to expand/collapse
        score_frame.bind('<Button-1>', self.toggle_training_score)
        ttk.Label(score_frame, text="Training Score (Click to expand)", style='Dark.TLabel').pack()
        
        # Initially hidden content
        self.score_content_frame.pack_forget()
    
    def toggle_training_score(self, event):
        """Toggle training score section visibility"""
        if self.score_content_frame.winfo_viewable():
            self.score_content_frame.pack_forget()
        else:
            self.score_content_frame.pack(fill=tk.X, pady=(10, 0))
            self.populate_training_score_content()
    
    def populate_training_score_content(self):
        """Populate the training score content"""
        # Clear existing content
        for widget in self.score_content_frame.winfo_children():
            widget.destroy()
        
        # Rainbow Support
        rainbow_frame = ttk.Frame(self.score_content_frame, style='Dark.TFrame')
        rainbow_frame.pack(fill=tk.X, pady=5)
        ttk.Label(rainbow_frame, text="Rainbow Support:", style='Dark.TLabel').pack(side=tk.LEFT)
        ttk.Spinbox(rainbow_frame, from_=0.0, to=10.0, increment=0.1, textvariable=self.rainbow_support_var, 
                   style='Dark.TSpinbox', width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Low Bond Support
        low_bond_frame = ttk.Frame(self.score_content_frame, style='Dark.TFrame')
        low_bond_frame.pack(fill=tk.X, pady=5)
        ttk.Label(low_bond_frame, text="Low Bond (<4) Support:", style='Dark.TLabel').pack(side=tk.LEFT)
        ttk.Spinbox(low_bond_frame, from_=0.0, to=10.0, increment=0.1, textvariable=self.low_bond_support_var, 
                   style='Dark.TSpinbox', width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # High Bond Different Type Support
        high_bond_frame = ttk.Frame(self.score_content_frame, style='Dark.TFrame')
        high_bond_frame.pack(fill=tk.X, pady=5)
        ttk.Label(high_bond_frame, text="High Bond (>=4) Different Type:", style='Dark.TLabel').pack(side=tk.LEFT)
        ttk.Spinbox(high_bond_frame, from_=0.0, to=10.0, increment=0.1, textvariable=self.high_bond_support_var, 
                   style='Dark.TSpinbox', width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Hint
        hint_frame = ttk.Frame(self.score_content_frame, style='Dark.TFrame')
        hint_frame.pack(fill=tk.X, pady=5)
        ttk.Label(hint_frame, text="Hint:", style='Dark.TLabel').pack(side=tk.LEFT)
        ttk.Spinbox(hint_frame, from_=0.0, to=10.0, increment=0.1, textvariable=self.hint_var, 
                   style='Dark.TSpinbox', width=10).pack(side=tk.LEFT, padx=(10, 0))
    
    def create_racing_tab(self):
        """Create the Racing tab"""
        racing_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(racing_frame, text="Racing")
        
        config = self.main_window.get_config()
        

        
        # Strategy
        strategy_frame = ttk.Frame(racing_frame, style='Dark.TFrame')
        strategy_frame.pack(fill=tk.X, pady=10)
        ttk.Label(strategy_frame, text="Strategy:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.strategy_var = tk.StringVar(value=config.get('strategy', 'PACE'))
        strategy_combo = ttk.Combobox(strategy_frame, textvariable=self.strategy_var, 
                                    values=['FRONT', 'PACE', 'LATE', 'END'], 
                                    state='readonly', style='Dark.TCombobox', width=15)
        strategy_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Race Retry
        retry_frame = ttk.Frame(racing_frame, style='Dark.TFrame')
        retry_frame.pack(fill=tk.X, pady=10)
        self.retry_race_var = tk.BooleanVar(value=config.get('retry_race', True))
        ttk.Checkbutton(retry_frame, text="Race Retry using Clock", 
                       variable=self.retry_race_var, style='Dark.TCheckbutton').pack(anchor=tk.W)
        
        # Save button
        ttk.Button(racing_frame, text="Save Racing Settings", 
                  command=self.save_racing_settings, style='Config.TButton').pack(pady=10)
    
    def create_event_tab(self):
        """Create the Event tab"""
        event_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(event_frame, text="Event")
        
        # Good Choices
        good_frame = ttk.Frame(event_frame, style='Dark.TFrame')
        good_frame.pack(fill=tk.X, pady=10)
        ttk.Button(good_frame, text="Good Choices", command=self.open_good_choices_window, 
                  style='Config.TButton').pack(anchor=tk.W)
        
        # Bad Choices
        bad_frame = ttk.Frame(event_frame, style='Dark.TFrame')
        bad_frame.pack(fill=tk.X, pady=10)
        ttk.Button(bad_frame, text="Bad Choices", command=self.open_bad_choices_window, 
                  style='Config.TButton').pack(anchor=tk.W)
    
    def create_skill_tab(self):
        """Create the Skill tab"""
        skill_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(skill_frame, text="Skill")
        
        config = self.main_window.get_config()
        
        # Enable Skill Point Check
        enable_frame = ttk.Frame(skill_frame, style='Dark.TFrame')
        enable_frame.pack(fill=tk.X, pady=10)
        self.enable_skill_check_var = tk.BooleanVar(value=config.get('enable_skill_point_check', True))
        ttk.Checkbutton(enable_frame, text="Enable Skill Point Check and Skill Purchase", 
                       variable=self.enable_skill_check_var, style='Dark.TCheckbutton',
                       command=self.toggle_skill_settings).pack(anchor=tk.W)
        
        # Skill settings container (initially visible if enabled)
        self.skill_settings_frame = ttk.Frame(skill_frame, style='Dark.TFrame')
        self.skill_settings_frame.pack(fill=tk.X, pady=10)
        
        # Skill Point Cap
        cap_frame = ttk.Frame(self.skill_settings_frame, style='Dark.TFrame')
        cap_frame.pack(fill=tk.X, pady=5)
        ttk.Label(cap_frame, text="Skill Point Cap:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.skill_point_cap_var = tk.IntVar(value=config.get('skill_point_cap', 400))
        ttk.Spinbox(cap_frame, from_=0, to=9999, textvariable=self.skill_point_cap_var, 
                   style='Dark.TSpinbox', width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Skill Purchase Mode
        mode_frame = ttk.Frame(self.skill_settings_frame, style='Dark.TFrame')
        mode_frame.pack(fill=tk.X, pady=5)
        ttk.Label(mode_frame, text="Skill Purchase Mode:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.skill_purchase_var = tk.StringVar(value=config.get('skill_purchase', 'auto'))
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.skill_purchase_var, 
                                 values=['Auto', 'Manual'], state='readonly', 
                                 style='Dark.TCombobox', width=15)
        mode_combo.pack(side=tk.LEFT, padx=(10, 0))
        mode_combo.bind('<<ComboboxSelected>>', self.toggle_auto_skill_settings)
        
        # Auto skill settings (initially visible if auto)
        self.auto_skill_frame = ttk.Frame(self.skill_settings_frame, style='Dark.TFrame')
        self.auto_skill_frame.pack(fill=tk.X, pady=10)
        
        # Skill Template
        template_frame = ttk.Frame(self.auto_skill_frame, style='Dark.TFrame')
        template_frame.pack(fill=tk.X, pady=5)
        ttk.Label(template_frame, text="Skill Template:", style='Dark.TLabel').pack(side=tk.LEFT)
        self.skill_file_var = tk.StringVar(value=config.get('skill_file', 'skills_example.json'))
        ttk.Entry(template_frame, textvariable=self.skill_file_var, style='Dark.TEntry', width=20).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(template_frame, text="Browse", command=self.browse_skill_file, 
                  style='Dark.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(template_frame, text="Edit Skill List", command=self.open_skill_editor, 
                  style='Config.TButton').pack(side=tk.LEFT)
        
        # Save button
        ttk.Button(skill_frame, text="Save Skill Settings", 
                  command=self.save_skill_settings, style='Config.TButton').pack(pady=10)
    
    def create_others_tab(self):
        """Create the Others tab"""
        others_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(others_frame, text="Others")
        
        config = self.main_window.get_config()
        
        # Debug Mode
        debug_frame = ttk.Frame(others_frame, style='Dark.TFrame')
        debug_frame.pack(fill=tk.X, pady=10)
        self.debug_mode_var = tk.BooleanVar(value=config.get('debug_mode', False))
        ttk.Checkbutton(debug_frame, text="Debug Mode", 
                       variable=self.debug_mode_var, style='Dark.TCheckbutton').pack(anchor=tk.W)
        
        # Save button
        ttk.Button(others_frame, text="Save Other Settings", 
                  command=self.save_other_settings, style='Config.TButton').pack(pady=10)
    
    def add_stat_field(self):
        """Add a new stat field to priority stats"""
        var = tk.StringVar(value="spd")
        self.priority_vars.append(var)
        # This would need to be implemented with proper widget management
    
    def remove_stat_field(self):
        """Remove the last stat field from priority stats"""
        if len(self.priority_vars) > 1:
            self.priority_vars.pop()
            # This would need to be implemented with proper widget management
    
    def toggle_race_settings(self):
        """Toggle visibility of race-related settings"""
        if self.do_race_var.get():
            self.race_settings_frame.pack(fill=tk.X, pady=5)
        else:
            self.race_settings_frame.pack_forget()
    
    def toggle_skill_settings(self):
        """Toggle visibility of skill settings"""
        if self.enable_skill_check_var.get():
            self.skill_settings_frame.pack(fill=tk.X, pady=10)
        else:
            self.skill_settings_frame.pack_forget()
    
    def toggle_auto_skill_settings(self, event=None):
        """Toggle visibility of auto skill settings"""
        if self.skill_purchase_var.get() == 'Auto':
            self.auto_skill_frame.pack(fill=tk.X, pady=10)
        else:
            self.auto_skill_frame.pack_forget()
    
    def browse_skill_file(self):
        """Browse for skill file"""
        filename = filedialog.askopenfilename(
            title="Select Skill File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.skill_file_var.set(filename)
    
    def open_good_choices_window(self):
        """Open good choices editor window"""
        # This would open a new window for editing good choices
        messagebox.showinfo("Info", "Good Choices editor will be implemented")
    
    def open_bad_choices_window(self):
        """Open bad choices editor window"""
        # This would open a new window for editing bad choices
        messagebox.showinfo("Info", "Bad Choices editor will be implemented")
    
    def open_skill_editor(self):
        """Open skill editor window"""
        # This would open a new window for editing skills
        messagebox.showinfo("Info", "Skill editor will be implemented")
    
    def load_training_score_config(self):
        """Load training score configuration"""
        try:
            if os.path.exists('training_score.json'):
                with open('training_score.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    scoring_rules = config.get('scoring_rules', {})
                    
                    self.rainbow_support_var.set(scoring_rules.get('rainbow_support', {}).get('points', 1.0))
                    self.low_bond_support_var.set(scoring_rules.get('not_rainbow_support_low', {}).get('points', 0.7))
                    self.high_bond_support_var.set(scoring_rules.get('not_rainbow_support_high', {}).get('points', 0.0))
                    self.hint_var.set(scoring_rules.get('hint', {}).get('points', 0.3))
        except Exception as e:
            print(f"Error loading training score config: {e}")
    
    def load_event_priority_config(self):
        """Load event priority configuration"""
        try:
            if os.path.exists('event_priority.json'):
                with open('event_priority.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Store for use in editor windows
                    self.event_priorities = config
        except Exception as e:
            print(f"Error loading event priority config: {e}")
    
    def load_skills_config(self):
        """Load skills configuration"""
        try:
            config = self.main_window.get_config()
            skill_file = config.get('skill_file', 'skills_example.json')
            if os.path.exists(skill_file):
                with open(skill_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Store for use in editor windows
                    self.skills_config = config
        except Exception as e:
            print(f"Error loading skills config: {e}")
    
    def save_training_settings(self):
        """Save training settings to config"""
        config = self.main_window.get_config()
        
        # Update priority stats
        config['priority_stat'] = [var.get() for var in self.priority_vars]
        config['minimum_mood'] = self.minimum_mood_var.get()
        config['maximum_failure'] = self.maximum_failure_var.get()
        config['min_energy'] = self.min_energy_var.get()
        config['do_race_when_bad_training'] = self.do_race_var.get()
        config['min_score'] = self.min_score_var.get()
        config['min_wit_score'] = self.min_wit_score_var.get()
        
        # Update stat caps
        for stat, var in self.stat_cap_vars.items():
            config['stat_caps'][stat] = var.get()
        
        # Save training score config
        self.save_training_score_config()
        
        # Update main config
        self.main_window.set_config(config)
        messagebox.showinfo("Success", "Training settings saved successfully!")
    
    def save_training_score_config(self):
        """Save training score configuration"""
        try:
            config = {
                "scoring_rules": {
                    "rainbow_support": {
                        "description": "Same type support card with bond level >= 4",
                        "points": self.rainbow_support_var.get()
                    },
                    "not_rainbow_support_low": {
                        "description": "Support with bond level < 4",
                        "points": self.low_bond_support_var.get()
                    },
                    "not_rainbow_support_high": {
                        "description": "Not same type support with bond level >= 4 (no need to get more bond)",
                        "points": self.high_bond_support_var.get()
                    },
                    "hint": {
                        "description": "Hint icon present",
                        "points": self.hint_var.get()
                    }
                }
            }
            
            with open('training_score.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving training score config: {e}")
    
    def save_racing_settings(self):
        """Save racing settings to config"""
        config = self.main_window.get_config()

        config['strategy'] = self.strategy_var.get()
        config['retry_race'] = self.retry_race_var.get()
        
        self.main_window.set_config(config)
        messagebox.showinfo("Success", "Racing settings saved successfully!")
    
    def save_skill_settings(self):
        """Save skill settings to config"""
        config = self.main_window.get_config()
        config['enable_skill_point_check'] = self.enable_skill_check_var.get()
        config['skill_point_cap'] = self.skill_point_cap_var.get()
        config['skill_purchase'] = self.skill_purchase_var.get().lower()
        config['skill_file'] = self.skill_file_var.get()
        
        self.main_window.set_config(config)
        messagebox.showinfo("Success", "Skill settings saved successfully!")
    
    def save_other_settings(self):
        """Save other settings to config"""
        config = self.main_window.get_config()
        config['debug_mode'] = self.debug_mode_var.get()
        
        self.main_window.set_config(config)
        messagebox.showinfo("Success", "Other settings saved successfully!")
    
    def refresh_config(self):
        """Refresh configuration display"""
        # This would refresh all the configuration displays
        pass
