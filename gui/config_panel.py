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
        self.create_restart_tab()
        self.create_others_tab()
    
    def create_main_tab(self):
        """Create the Main tab with ADB configuration"""
        # Add tab to tabview
        main_tab = self.tabview.add("Main")
        
        # Create scrollable frame inside the main tab
        main_scroll = ctk.CTkScrollableFrame(main_tab, fg_color="transparent", corner_radius=0)
        main_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ADB Configuration Frame
        adb_frame = ctk.CTkFrame(main_scroll, fg_color=self.colors['bg_light'], corner_radius=10)
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
        
        # Save button for ADB config
        save_btn = ctk.CTkButton(adb_frame, text="Save ADB Settings", 
                                command=self.save_config,
                                fg_color=self.colors['accent_green'], corner_radius=8, height=35)
        save_btn.pack(pady=(10, 15))
    
    def create_training_tab(self):
        """Create the Training tab with all training-related settings"""
        # Add tab to tabview
        training_tab = self.tabview.add("Training")
        
        # Create scrollable frame inside the training tab
        training_scroll = ctk.CTkScrollableFrame(training_tab, fg_color="transparent", corner_radius=0)
        training_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        config = self.main_window.get_config()
        
        # Stats Priority Section
        priority_frame = ctk.CTkFrame(training_scroll, fg_color=self.colors['bg_light'], corner_radius=10)
        priority_frame.pack(fill=tk.X, pady=10, padx=10)
        
        priority_title = ctk.CTkLabel(priority_frame, text="Stats Priority", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_light'])
        priority_title.pack(pady=(15, 10))
        
        # Click to swap instruction
        instruction_label = ctk.CTkLabel(priority_frame, text="Click on two boxes to swap their positions (left to right = highest to lowest priority):", 
                                       text_color=self.colors['text_gray'], font=ctk.CTkFont(size=11))
        instruction_label.pack(pady=(0, 15))
        
        # Priority stats container with drag and drop
        self.priority_container = ctk.CTkFrame(priority_frame, fg_color="transparent")
        self.priority_container.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Create draggable stat boxes for the 5 fixed stats
        self.priority_vars = []
        self.stat_boxes = []
        priority_stats = config.get('priority_stat', ['spd', 'sta', 'wit', 'pwr', 'guts'])
        
        # Ensure we have exactly 5 stats
        while len(priority_stats) < 5:
            priority_stats.append('spd')  # Default fallback
        priority_stats = priority_stats[:5]  # Limit to 5
        
        for i, stat in enumerate(priority_stats):
            self.create_draggable_stat_box(stat, i)
        
        # Training Settings Section
        settings_frame = ctk.CTkFrame(training_scroll, fg_color=self.colors['bg_light'], corner_radius=10)
        settings_frame.pack(fill=tk.X, pady=10, padx=10)
        
        settings_title = ctk.CTkLabel(settings_frame, text="Training Settings", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_light'])
        settings_title.pack(pady=(15, 10))
        
        # Minimum Mood
        mood_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        mood_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(mood_frame, text="Minimum Mood:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        self.minimum_mood_var = tk.StringVar(value=config.get('minimum_mood', 'GREAT'))
        mood_combo = ctk.CTkOptionMenu(mood_frame, values=['GREAT', 'GOOD', 'NORMAL', 'BAD', 'AWFUL'], 
                                       variable=self.minimum_mood_var, fg_color=self.colors['accent_blue'], 
                                       corner_radius=8, button_color=self.colors['accent_blue'],
                                       button_hover_color=self.colors['accent_green'])
        mood_combo.pack(side=tk.RIGHT)
        
        # Maximum Failure Rate
        fail_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        fail_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(fail_frame, text="Maximum Failure Rate:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        self.maximum_failure_var = tk.IntVar(value=config.get('maximum_failure', 15))
        ctk.CTkEntry(fail_frame, textvariable=self.maximum_failure_var, width=100, corner_radius=8).pack(side=tk.RIGHT)
        
        # Minimum Energy for Training
        energy_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        energy_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(energy_frame, text="Minimum Energy for Training:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        self.min_energy_var = tk.IntVar(value=config.get('min_energy', 30))
        ctk.CTkEntry(energy_frame, textvariable=self.min_energy_var, width=100, corner_radius=8).pack(side=tk.RIGHT)
        
        # Do Race if no good training found
        race_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        race_frame.pack(fill=tk.X, padx=15, pady=5)
        self.do_race_var = tk.BooleanVar(value=config.get('do_race_when_bad_training', True))
        race_checkbox = ctk.CTkCheckBox(race_frame, text="Do Race if no good training found", 
                                      variable=self.do_race_var, text_color=self.colors['text_light'],
                                      command=self.toggle_race_settings)
        race_checkbox.pack(anchor=tk.W)
        
        # Race-related settings (initially visible if do_race is True)
        self.race_settings_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        if self.do_race_var.get():
            self.race_settings_frame.pack(fill=tk.X, pady=5)
        
        # Minimum Training Score
        score_frame = ctk.CTkFrame(self.race_settings_frame, fg_color="transparent")
        score_frame.pack(fill=tk.X, pady=5)
        ctk.CTkLabel(score_frame, text="Minimum Training Score:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        self.min_score_var = tk.DoubleVar(value=config.get('min_score', 1.0))
        ctk.CTkEntry(score_frame, textvariable=self.min_score_var, width=100, corner_radius=8).pack(side=tk.RIGHT)
        
        # Minimum WIT Training Score
        wit_score_frame = ctk.CTkFrame(self.race_settings_frame, fg_color="transparent")
        wit_score_frame.pack(fill=tk.X, pady=5)
        ctk.CTkLabel(wit_score_frame, text="Minimum WIT Training Score:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        self.min_wit_score_var = tk.DoubleVar(value=config.get('min_wit_score', 1.0))
        ctk.CTkEntry(wit_score_frame, textvariable=self.min_wit_score_var, width=100, corner_radius=8).pack(side=tk.RIGHT)
        
        # Stat Caps Section
        caps_frame = ctk.CTkFrame(training_scroll, fg_color=self.colors['bg_light'], corner_radius=10)
        caps_frame.pack(fill=tk.X, pady=10, padx=10)
        
        caps_title = ctk.CTkLabel(caps_frame, text="Stat Caps", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_light'])
        caps_title.pack(pady=(15, 10))
        
        caps_container = ctk.CTkFrame(caps_frame, fg_color="transparent")
        caps_container.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.stat_cap_vars = {}
        stat_caps = config.get('stat_caps', {})
        stats = ['spd', 'sta', 'pwr', 'guts', 'wit']
        
        # Create horizontal stat cap inputs
        for i, stat in enumerate(stats):
            stat_frame = ctk.CTkFrame(caps_container, fg_color="transparent")
            stat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 3) if i < len(stats) - 1 else (0, 0))
            
            # Stat name label
            ctk.CTkLabel(stat_frame, text=stat.upper(), font=ctk.CTkFont(size=10, weight="bold"), 
                        text_color=self.colors['text_gray']).pack(pady=(0, 5))
            
            # Stat cap input
            var = tk.IntVar(value=stat_caps.get(stat, 600))
            self.stat_cap_vars[stat] = var
            ctk.CTkEntry(stat_frame, textvariable=var, width=80, corner_radius=8).pack()
        
        # Training Score Section (collapsible)
        self.create_training_score_section(training_scroll)
        
        # Save button
        save_btn = ctk.CTkButton(training_scroll, text="Save Training Settings", 
                                command=self.save_training_settings,
                                fg_color=self.colors['accent_green'], corner_radius=8, height=35)
        save_btn.pack(pady=20)
    
    def create_draggable_stat_box(self, stat, index):
        """Create a draggable stat box for priority ordering"""
        # Create a container frame for better control - make it responsive
        container_frame = ctk.CTkFrame(self.priority_container, fg_color="transparent", width=70, height=45)
        container_frame.pack(side=tk.LEFT, padx=(0, 8))
        container_frame.pack_propagate(False)  # Prevent size changes
        
        # Create the stat box with much more rounded corners and better styling
        stat_box = ctk.CTkFrame(container_frame, fg_color=self.colors['accent_blue'], 
                               corner_radius=20, width=65, height=40,
                               border_width=1, border_color=self.colors['accent_blue'])  # Add subtle border for better definition
        stat_box.place(relx=0.5, rely=0.5, anchor="center")
        
        # Create the stat label with better font and styling
        stat_label = ctk.CTkLabel(stat_box, text=stat.upper(), 
                                font=ctk.CTkFont(size=12, weight="bold"), 
                                text_color=self.colors['text_light'])
        stat_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Store the stat box and its data
        box_data = {
            'frame': stat_box,
            'container': container_frame,
            'label': stat_label,
            'stat': stat,
            'index': index,
            'hovered': False  # Track hover state
        }
        
        self.stat_boxes.append(box_data)
        
        # Bind click events for swapping positions - bind to ALL elements for better click detection
        container_frame.bind('<Button-1>', lambda e, b=box_data: self.on_stat_box_click(e, b))
        stat_box.bind('<Button-1>', lambda e, b=box_data: self.on_stat_box_click(e, b))
        stat_label.bind('<Button-1>', lambda e, b=box_data: self.on_stat_box_click(e, b))
        
        # Add hover effects for better interactivity - bind to all elements
        container_frame.bind('<Enter>', lambda e, b=box_data: self.on_hover_enter(e, b))
        container_frame.bind('<Leave>', lambda e, b=box_data: self.on_hover_leave(e, b))
        stat_box.bind('<Enter>', lambda e, b=box_data: self.on_hover_enter(e, b))
        stat_box.bind('<Leave>', lambda e, b=box_data: self.on_hover_leave(e, b))
        stat_label.bind('<Enter>', lambda e, b=box_data: self.on_hover_enter(e, b))
        stat_label.bind('<Leave>', lambda e, b=box_data: self.on_hover_leave(e, b))
        
        # Make the entire area look clickable
        container_frame.configure(cursor="hand2")
        stat_box.configure(cursor="hand2")
        stat_label.configure(cursor="hand2")
        
        # Create variable for the stat value
        var = tk.StringVar(value=stat)
        self.priority_vars.append(var)
    
    def on_stat_box_click(self, event, box_data):
        """Handle click on stat box for swapping positions"""
        # If no box is currently selected, select this one
        if not hasattr(self, 'selected_box') or self.selected_box is None:
            self.selected_box = box_data
            # Highlight the selected box
            box_data['frame'].configure(fg_color=self.colors['accent_yellow'])
            print(f"Selected {box_data['stat']} for swapping")
        else:
            # If a box is already selected, swap with this one
            if self.selected_box != box_data:
                # Swap the positions
                old_index = self.selected_box['index']
                new_index = box_data['index']
                self.swap_stat_boxes(old_index, new_index)
                print(f"Swapped {self.selected_box['stat']} with {box_data['stat']}")
            
            # Reset selection
            self.selected_box['frame'].configure(fg_color=self.colors['accent_blue'])
            self.selected_box = None
    
    def on_hover_enter(self, event, box_data):
        """Handle mouse enter hover effect"""
        # Don't change color if this box is currently selected for swapping
        if not hasattr(self, 'selected_box') or self.selected_box != box_data:
            if not box_data.get('hovered', False):
                box_data['hovered'] = True
                box_data['frame'].configure(fg_color=self.colors['accent_green'])
    
    def on_hover_leave(self, event, box_data):
        """Handle mouse leave hover effect"""
        # Don't change color if this box is currently selected for swapping
        if not hasattr(self, 'selected_box') or self.selected_box != box_data:
            if box_data.get('hovered', False):
                # Add a small delay to prevent flickering
                def delayed_leave():
                    if not box_data.get('hovered', False):
                        box_data['frame'].configure(fg_color=self.colors['accent_blue'])
                
                # Schedule the color change with a small delay
                self.after(50, delayed_leave)
                box_data['hovered'] = False
    
    def swap_stat_boxes(self, index1, index2):
        """Swap two stat boxes at the given indices"""
        # Swap the boxes in the list
        self.stat_boxes[index1], self.stat_boxes[index2] = self.stat_boxes[index2], self.stat_boxes[index1]
        
        # Swap the variables
        self.priority_vars[index1], self.priority_vars[index2] = self.priority_vars[index2], self.priority_vars[index1]
        
        # Update indices
        for i, box_data in enumerate(self.stat_boxes):
            box_data['index'] = i
        
        # Repack all containers in the new order
        for box_data in self.stat_boxes:
            box_data['container'].pack_forget()
        
        for box_data in self.stat_boxes:
            box_data['container'].pack(side=tk.LEFT, padx=(0, 8))
    
    def reorder_stat_boxes(self, old_index, new_index):
        """Reorder the stat boxes and variables"""
        # Reorder the boxes list
        box = self.stat_boxes.pop(old_index)
        self.stat_boxes.insert(new_index, box)
        
        # Reorder the variables list
        var = self.priority_vars.pop(old_index)
        self.priority_vars.insert(new_index, var)
        
        # Update indices
        for i, box_data in enumerate(self.stat_boxes):
            box_data['index'] = i
        
        # Repack all containers in the new order
        for box_data in self.stat_boxes:
            box_data['container'].pack_forget()
        
        for box_data in self.stat_boxes:
            box_data['container'].pack(side=tk.LEFT, padx=(0, 8))
    

    
    def toggle_race_settings(self):
        """Toggle visibility of race-related settings"""
        if self.do_race_var.get():
            self.race_settings_frame.pack(fill=tk.X, pady=5)
        else:
            self.race_settings_frame.pack_forget()
    
    def toggle_skill_settings(self):
        """Toggle visibility of skill-related settings"""
        if self.enable_skill_check_var.get():
            # Show all skill settings
            self.skill_settings_container.pack(fill=tk.X, pady=5)
            # Also check if auto settings should be shown
            self.toggle_skill_purchase_settings()
        else:
            # Hide all skill settings including auto settings
            self.skill_settings_container.pack_forget()
            self.auto_settings_frame.pack_forget()
    
    def toggle_skill_purchase_settings(self, value=None):
        """Toggle visibility of auto-specific skill settings"""
        # Only show auto settings if skill check is enabled AND mode is auto
        if self.enable_skill_check_var.get() and self.skill_purchase_var.get() == 'auto':
            self.auto_settings_frame.pack(fill=tk.X, pady=5)
        else:
            self.auto_settings_frame.pack_forget()
    
    def create_training_score_section(self, parent):
        """Create the collapsible training score section"""
        # Training Score Frame
        score_frame = ctk.CTkFrame(parent, fg_color=self.colors['bg_light'], corner_radius=10)
        score_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # Collapsible header
        self.score_header = ctk.CTkFrame(score_frame, fg_color="transparent")
        self.score_header.pack(fill=tk.X, padx=15, pady=10)
        
        # Training score variables
        self.rainbow_support_var = tk.DoubleVar(value=1.0)
        self.low_bond_support_var = tk.DoubleVar(value=0.7)
        self.high_bond_support_var = tk.DoubleVar(value=0.0)
        self.hint_var = tk.DoubleVar(value=0.3)
        
        # Header label with click binding
        header_label = ctk.CTkLabel(self.score_header, text="Training Score (Click to expand)", 
                                  font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors['text_light'])
        header_label.pack()
        
        # Bind click event to expand/collapse
        header_label.bind('<Button-1>', self.toggle_training_score)
        self.score_header.bind('<Button-1>', self.toggle_training_score)
        
        # Initially hidden content
        self.score_content_frame = ctk.CTkFrame(score_frame, fg_color="transparent")
        self.score_content_frame.pack_forget()
    
    def toggle_training_score(self, event):
        """Toggle training score section visibility"""
        if self.score_content_frame.winfo_viewable():
            self.score_content_frame.pack_forget()
        else:
            self.score_content_frame.pack(fill=tk.X, pady=(10, 15), padx=15)
            self.populate_training_score_content()
    
    def populate_training_score_content(self):
        """Populate the training score content"""
        # Clear existing content
        for widget in self.score_content_frame.winfo_children():
            widget.destroy()
        
        # Rainbow Support
        rainbow_frame = ctk.CTkFrame(self.score_content_frame, fg_color="transparent")
        rainbow_frame.pack(fill=tk.X, pady=5)
        ctk.CTkLabel(rainbow_frame, text="Rainbow Support:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        ctk.CTkEntry(rainbow_frame, textvariable=self.rainbow_support_var, width=100, corner_radius=8).pack(side=tk.RIGHT)
        
        # Low Bond Support
        low_bond_frame = ctk.CTkFrame(self.score_content_frame, fg_color="transparent")
        low_bond_frame.pack(fill=tk.X, pady=5)
        ctk.CTkLabel(low_bond_frame, text="Low Bond (<4) Support:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        ctk.CTkEntry(low_bond_frame, textvariable=self.low_bond_support_var, width=100, corner_radius=8).pack(side=tk.RIGHT)
        
        # High Bond Different Type Support
        high_bond_frame = ctk.CTkFrame(self.score_content_frame, fg_color="transparent")
        high_bond_frame.pack(fill=tk.X, pady=5)
        ctk.CTkLabel(high_bond_frame, text="High Bond (>=4) Different Type:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        ctk.CTkEntry(high_bond_frame, textvariable=self.high_bond_support_var, width=100, corner_radius=8).pack(side=tk.RIGHT)
        
        # Hint
        hint_frame = ctk.CTkFrame(self.score_content_frame, fg_color="transparent")
        hint_frame.pack(fill=tk.X, pady=5)
        ctk.CTkLabel(hint_frame, text="Hint:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        ctk.CTkEntry(hint_frame, textvariable=self.hint_var, width=100, corner_radius=8).pack(side=tk.RIGHT)
    
    def save_training_settings(self):
        """Save training settings to config"""
        try:
            config = self.main_window.get_config()
            
            # Update priority stats (in current order)
            config['priority_stat'] = [var.get() for var in self.priority_vars]
            
            # Update training settings
            config['minimum_mood'] = self.minimum_mood_var.get()
            config['maximum_failure'] = self.maximum_failure_var.get()
            config['min_energy'] = self.min_energy_var.get()
            config['do_race_when_bad_training'] = self.do_race_var.get()
            
            # Update race-related settings
            if self.do_race_var.get():
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
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save training settings: {e}")
    
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
    
    def create_racing_tab(self):
        """Create the Racing tab"""
        # Add tab to tabview
        racing_tab = self.tabview.add("Racing")
        
        # Create scrollable frame inside the racing tab
        racing_scroll = ctk.CTkScrollableFrame(racing_tab, fg_color="transparent", corner_radius=0)
        racing_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        config = self.main_window.get_config()
        
        # Racing Settings Frame
        racing_frame = ctk.CTkFrame(racing_scroll, fg_color=self.colors['bg_light'], corner_radius=10)
        racing_frame.pack(fill=tk.X, pady=10, padx=10)
        
        racing_title = ctk.CTkLabel(racing_frame, text="Racing Settings", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_light'])
        racing_title.pack(pady=(15, 10))
        
        # G1 Race Prioritize
        g1_frame = ctk.CTkFrame(racing_frame, fg_color="transparent")
        g1_frame.pack(fill=tk.X, padx=15, pady=5)
        self.prioritize_g1_var = tk.BooleanVar(value=config.get('prioritize_g1_race', False))
        g1_checkbox = ctk.CTkCheckBox(g1_frame, text="G1 Race Prioritize (For Fan Farming)", 
                                     variable=self.prioritize_g1_var, text_color=self.colors['text_light'])
        g1_checkbox.pack(anchor=tk.W)
        
        # Strategy
        strategy_frame = ctk.CTkFrame(racing_frame, fg_color="transparent")
        strategy_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(strategy_frame, text="Strategy:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        self.strategy_var = tk.StringVar(value=config.get('strategy', 'PACE'))
        strategy_combo = ctk.CTkOptionMenu(strategy_frame, values=['FRONT', 'PACE', 'LATE', 'END'], 
                                          variable=self.strategy_var, fg_color=self.colors['accent_blue'], 
                                          corner_radius=8, button_color=self.colors['accent_blue'],
                                          button_hover_color=self.colors['accent_green'])
        strategy_combo.pack(side=tk.RIGHT)
        
        # Race Retry
        retry_frame = ctk.CTkFrame(racing_frame, fg_color="transparent")
        retry_frame.pack(fill=tk.X, padx=15, pady=(5, 15))
        self.retry_race_var = tk.BooleanVar(value=config.get('retry_race', True))
        retry_checkbox = ctk.CTkCheckBox(retry_frame, text="Race Retry using Clock", 
                                       variable=self.retry_race_var, text_color=self.colors['text_light'])
        retry_checkbox.pack(anchor=tk.W)
        
        # Save button
        save_btn = ctk.CTkButton(racing_scroll, text="Save Racing Settings", 
                               command=self.save_racing_settings,
                               fg_color=self.colors['accent_green'], corner_radius=8, height=35)
        save_btn.pack(pady=20)
    
    def save_racing_settings(self):
        """Save racing settings to config"""
        try:
            config = self.main_window.get_config()
            config['prioritize_g1_race'] = self.prioritize_g1_var.get()
            config['strategy'] = self.strategy_var.get()
            config['retry_race'] = self.retry_race_var.get()
            
            self.main_window.set_config(config)
            messagebox.showinfo("Success", "Racing settings saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save racing settings: {e}")
    
    def save_skill_settings(self):
        """Save skill settings to config"""
        try:
            config = self.main_window.get_config()
            config['enable_skill_point_check'] = self.enable_skill_check_var.get()
            config['skill_point_cap'] = self.skill_point_cap_var.get()
            config['skill_purchase'] = self.skill_purchase_var.get()
            config['skill_file'] = self.skill_file_var.get()
            
            self.main_window.set_config(config)
            messagebox.showinfo("Success", "Skill settings saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save skill settings: {e}")
    
    def create_event_tab(self):
        """Create the Event tab with event choice management"""
        # Add tab to tabview
        event_tab = self.tabview.add("Event")
        
        # Create scrollable frame inside the event tab
        event_scroll = ctk.CTkScrollableFrame(event_tab, fg_color="transparent", corner_radius=0)
        event_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Event Settings Frame
        event_frame = ctk.CTkFrame(event_scroll, fg_color=self.colors['bg_light'], corner_radius=10)
        event_frame.pack(fill=tk.X, pady=10, padx=10)
        
        event_title = ctk.CTkLabel(event_frame, text="Event Choice Management", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_light'])
        event_title.pack(pady=(15, 10))
        
        # Good Choices Section
        good_frame = ctk.CTkFrame(event_frame, fg_color="transparent")
        good_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ctk.CTkLabel(good_frame, text="Good Choices:", text_color=self.colors['text_light'], font=ctk.CTkFont(size=12, weight="bold")).pack(side=tk.LEFT)
        good_btn = ctk.CTkButton(good_frame, text="Open List", 
                                command=self.open_good_choices_window,
                                fg_color=self.colors['accent_green'], corner_radius=8, height=30, width=100)
        good_btn.pack(side=tk.RIGHT)
        
        # Bad Choices Section
        bad_frame = ctk.CTkFrame(event_frame, fg_color="transparent")
        bad_frame.pack(fill=tk.X, padx=15, pady=(10, 15))
        
        ctk.CTkLabel(bad_frame, text="Bad Choices:", text_color=self.colors['text_light'], font=ctk.CTkFont(size=12, weight="bold")).pack(side=tk.LEFT)
        bad_btn = ctk.CTkButton(bad_frame, text="Open List", 
                               command=self.open_bad_choices_window,
                               fg_color=self.colors['accent_red'], corner_radius=8, height=30, width=100)
        bad_btn.pack(side=tk.RIGHT)
    
    def create_skill_tab(self):
        """Create the Skill tab with skill management settings"""
        # Add tab to tabview
        skill_tab = self.tabview.add("Skill")
        
        config = self.main_window.get_config()
        
        # Fixed header section (always visible)
        header_frame = ctk.CTkFrame(skill_tab, fg_color=self.colors['bg_light'], corner_radius=10)
        header_frame.pack(fill=tk.X, pady=(10, 5), padx=10)
        
        skill_title = ctk.CTkLabel(header_frame, text="Skill Management", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_light'])
        skill_title.pack(pady=(15, 10))
        
        # Enable Skill Point Check
        enable_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        enable_frame.pack(fill=tk.X, padx=15, pady=5)
        self.enable_skill_check_var = tk.BooleanVar(value=config.get('enable_skill_point_check', True))
        enable_checkbox = ctk.CTkCheckBox(enable_frame, text="Enable Skill Point check and Skill Purchase", 
                                        variable=self.enable_skill_check_var, text_color=self.colors['text_light'],
                                        command=self.toggle_skill_settings)
        enable_checkbox.pack(anchor=tk.W)
        
        # Container for all skill settings (hidden when checkbox is unchecked)
        self.skill_settings_container = ctk.CTkFrame(header_frame, fg_color=self.colors['bg_light'], corner_radius=10)
        if self.enable_skill_check_var.get():
            self.skill_settings_container.pack(fill=tk.X, pady=5)
        
        # Skill Point Cap
        cap_frame = ctk.CTkFrame(self.skill_settings_container, fg_color="transparent")
        cap_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(cap_frame, text="Skill Point Cap:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        self.skill_point_cap_var = tk.IntVar(value=config.get('skill_point_cap', 400))
        ctk.CTkEntry(cap_frame, textvariable=self.skill_point_cap_var, width=100, corner_radius=8).pack(side=tk.RIGHT)
        
        # Skill Purchase Mode
        mode_frame = ctk.CTkFrame(self.skill_settings_container, fg_color=self.colors['bg_light'], corner_radius=10)
        mode_frame.pack(fill=tk.X, pady=5)
        
        mode_label = ctk.CTkLabel(mode_frame, text="Skill Purchase Mode:", text_color=self.colors['text_light'])
        mode_label.pack(side=tk.LEFT, padx=15, pady=15)
        
        self.skill_purchase_var = tk.StringVar(value=config.get('skill_purchase', 'auto'))
        mode_combo = ctk.CTkOptionMenu(mode_frame, values=['auto', 'manual'], 
                                      variable=self.skill_purchase_var, fg_color=self.colors['accent_blue'], 
                                      corner_radius=8, button_color=self.colors['accent_blue'],
                                      button_hover_color=self.colors['accent_green'],
                                      command=self.toggle_skill_purchase_settings)
        mode_combo.pack(side=tk.RIGHT, padx=15, pady=15)
        
        # Auto-specific settings (initially visible if mode is auto and skill check is enabled)
        self.auto_settings_frame = ctk.CTkFrame(self.skill_settings_container, fg_color="transparent")
        if self.enable_skill_check_var.get() and self.skill_purchase_var.get() == 'auto':
            self.auto_settings_frame.pack(fill=tk.X, pady=5)
        
        # Skill Template
        template_frame = ctk.CTkFrame(self.auto_settings_frame, fg_color="transparent")
        template_frame.pack(fill=tk.X, pady=15, padx=15)
        
        template_label = ctk.CTkLabel(template_frame, text="Skill Template:", text_color=self.colors['text_light'])
        template_label.pack(side=tk.LEFT)
        
        # File input and buttons container
        file_container = ctk.CTkFrame(template_frame, fg_color="transparent")
        file_container.pack(side=tk.RIGHT)
        
        self.skill_file_var = tk.StringVar(value=config.get('skill_file', 'skills_example.json'))
        ctk.CTkEntry(file_container, textvariable=self.skill_file_var, width=150, corner_radius=8).pack(side=tk.LEFT, padx=(0, 5))
        
        open_file_btn = ctk.CTkButton(file_container, text="Open File", 
                                    command=self.open_skill_file,
                                    fg_color=self.colors['accent_blue'], corner_radius=8, height=30, width=80)
        open_file_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        edit_list_btn = ctk.CTkButton(file_container, text="Edit Skill List", 
                                    command=self.open_skill_list_window,
                                    fg_color=self.colors['accent_green'], corner_radius=8, height=30, width=100)
        edit_list_btn.pack(side=tk.LEFT)
        
        # Save button - always at the bottom 
        self.skill_save_btn = ctk.CTkButton(skill_tab, text="Save Skill Settings", 
                                          command=self.save_skill_settings,
                                          fg_color=self.colors['accent_green'], corner_radius=8, height=35)
        self.skill_save_btn.pack(side=tk.BOTTOM, pady=20)
    
    def create_restart_tab(self):
        """Create the Restart tab with restart career settings"""
        # Add tab to tabview
        restart_tab = self.tabview.add("Restart")
        
        # Create scrollable frame inside the restart tab
        restart_scroll = ctk.CTkScrollableFrame(restart_tab, fg_color="transparent", corner_radius=0)
        restart_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        config = self.main_window.get_config()
        
        # Restart Career Settings Section
        restart_frame = ctk.CTkFrame(restart_scroll, fg_color=self.colors['bg_light'], corner_radius=10)
        restart_frame.pack(fill=tk.X, pady=10, padx=10)
        
        restart_title = ctk.CTkLabel(restart_frame, text="Restart Career Settings", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_light'])
        restart_title.pack(pady=(15, 10))
        
        # Restart Career Run checkbox
        self.restart_enabled_var = tk.BooleanVar(value=config.get('restart_career', {}).get('restart_enabled', False))
        restart_checkbox = ctk.CTkCheckBox(restart_frame, text="Restart Career run", variable=self.restart_enabled_var, 
                                         text_color=self.colors['text_light'], command=self.toggle_restart_settings)
        restart_checkbox.pack(anchor=tk.W, pady=(0, 15))
        
        # Restart criteria frame (initially hidden if restart is disabled)
        self.restart_criteria_frame = ctk.CTkFrame(restart_frame, fg_color="transparent")
        if self.restart_enabled_var.get():
            self.restart_criteria_frame.pack(fill=tk.X, pady=5)
        
        # Restart criteria radio buttons
        self.restart_criteria_var = tk.StringVar(value="times")
        if config.get('restart_career', {}).get('total_fans_requirement', 0) > 0:
            self.restart_criteria_var.set("fans")
        else:
            self.restart_criteria_var.set("times")
        
        criteria_label = ctk.CTkLabel(self.restart_criteria_frame, text="Restart Criteria (choose one):", text_color=self.colors['text_light'])
        criteria_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Times radio button and input
        times_frame = ctk.CTkFrame(self.restart_criteria_frame, fg_color="transparent")
        times_frame.pack(fill=tk.X, pady=5)
        times_radio = ctk.CTkRadioButton(times_frame, text="Restart career", variable=self.restart_criteria_var, value="times",
                                       text_color=self.colors['text_light'], command=self.on_criteria_change)
        times_radio.pack(side=tk.LEFT)
        self.restart_times_var = tk.IntVar(value=config.get('restart_career', {}).get('restart_times', 5))
        times_entry = ctk.CTkEntry(times_frame, textvariable=self.restart_times_var, width=80, corner_radius=8)
        times_entry.pack(side=tk.LEFT, padx=(10, 0))
        times_label = ctk.CTkLabel(times_frame, text="times", text_color=self.colors['text_light'])
        times_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Fans radio button and input
        fans_frame = ctk.CTkFrame(self.restart_criteria_frame, fg_color="transparent")
        fans_frame.pack(fill=tk.X, pady=5)
        fans_radio = ctk.CTkRadioButton(fans_frame, text="Run until achieve", variable=self.restart_criteria_var, value="fans",
                                      text_color=self.colors['text_light'], command=self.on_criteria_change)
        fans_radio.pack(side=tk.LEFT)
        self.total_fans_requirement_var = tk.IntVar(value=config.get('restart_career', {}).get('total_fans_requirement', 0))
        fans_entry = ctk.CTkEntry(fans_frame, textvariable=self.total_fans_requirement_var, width=80, corner_radius=8)
        fans_entry.pack(side=tk.LEFT, padx=(10, 0))
        fans_label = ctk.CTkLabel(fans_frame, text="fans", text_color=self.colors['text_light'])
        fans_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Legacy Settings Section
        self.legacy_frame = ctk.CTkFrame(restart_scroll, fg_color=self.colors['bg_light'], corner_radius=10)
        if self.restart_enabled_var.get():
            self.legacy_frame.pack(fill=tk.X, pady=10, padx=10)
        
        legacy_title = ctk.CTkLabel(self.legacy_frame, text="Legacy Settings", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_light'])
        legacy_title.pack(pady=(15, 10))
        
        # Include Legacy from Guests checkbox
        self.include_guests_legacy_var = tk.BooleanVar(value=config.get('auto_start_career', {}).get('include_guests_legacy', False))
        legacy_checkbox = ctk.CTkCheckBox(self.legacy_frame, text="Include Legacy from Guests", variable=self.include_guests_legacy_var, 
                                        text_color=self.colors['text_light'])
        legacy_checkbox.pack(anchor=tk.W, pady=(0, 15))
        
        # Support Settings Section
        self.support_frame = ctk.CTkFrame(restart_scroll, fg_color=self.colors['bg_light'], corner_radius=10)
        if self.restart_enabled_var.get():
            self.support_frame.pack(fill=tk.X, pady=10, padx=10)
        
        support_title = ctk.CTkLabel(self.support_frame, text="Support Settings (Note: Only choose followed player support)", 
                                   font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_light'])
        support_title.pack(pady=(15, 10))
        
        # Support Speciality
        speciality_frame = ctk.CTkFrame(self.support_frame, fg_color="transparent")
        speciality_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(speciality_frame, text="Support Speciality:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        self.support_speciality_var = tk.StringVar(value=config.get('auto_start_career', {}).get('support_speciality', 'STA'))
        speciality_combo = ctk.CTkOptionMenu(speciality_frame, values=['SPD', 'STA', 'PWR', 'GUTS', 'WIT', 'PAL'], 
                                           variable=self.support_speciality_var, fg_color=self.colors['accent_blue'], 
                                           corner_radius=8, button_color=self.colors['accent_blue'],
                                           button_hover_color=self.colors['accent_green'])
        speciality_combo.pack(side=tk.RIGHT)
        
        # Support Rarity
        rarity_frame = ctk.CTkFrame(self.support_frame, fg_color="transparent")
        rarity_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(rarity_frame, text="Support Rarity:", text_color=self.colors['text_light']).pack(side=tk.LEFT)
        self.support_rarity_var = tk.StringVar(value=config.get('auto_start_career', {}).get('support_rarity', 'SSR'))
        rarity_combo = ctk.CTkOptionMenu(rarity_frame, values=['R', 'SR', 'SSR'], 
                                       variable=self.support_rarity_var, fg_color=self.colors['accent_blue'], 
                                       corner_radius=8, button_color=self.colors['accent_blue'],
                                       button_hover_color=self.colors['accent_green'])
        rarity_combo.pack(side=tk.RIGHT)
        
        # Save button
        restart_save_btn = ctk.CTkButton(restart_tab, text="Save Restart Settings", 
                                       command=self.save_restart_settings,
                                       fg_color=self.colors['accent_green'], corner_radius=8, height=35)
        restart_save_btn.pack(side=tk.BOTTOM, pady=20)
    
    def toggle_restart_settings(self):
        """Toggle visibility of restart settings based on restart enabled checkbox"""
        if self.restart_enabled_var.get():
            self.restart_criteria_frame.pack(fill=tk.X, pady=5)
            self.legacy_frame.pack(fill=tk.X, pady=10, padx=10)
            self.support_frame.pack(fill=tk.X, pady=10, padx=10)
        else:
            self.restart_criteria_frame.pack_forget()
            self.legacy_frame.pack_forget()
            self.support_frame.pack_forget()
    
    def on_criteria_change(self):
        """Handle changes in restart criteria selection"""
        # When criteria changes, update the other field to 0
        if self.restart_criteria_var.get() == "times":
            self.total_fans_requirement_var.set(0)
        else:  # fans
            self.restart_times_var.set(0)
    
    def save_restart_settings(self):
        """Save restart career settings"""
        try:
            # Get current config
            config = self.main_window.get_config()
            
            # Update restart career config
            if 'restart_career' not in config:
                config['restart_career'] = {}
            
            config['restart_career']['restart_enabled'] = self.restart_enabled_var.get()
            
            # Update restart criteria based on radio button selection
            if self.restart_criteria_var.get() == "times":
                config['restart_career']['restart_times'] = self.restart_times_var.get()
                config['restart_career']['total_fans_requirement'] = 0
            else:  # fans
                config['restart_career']['restart_times'] = 0
                config['restart_career']['total_fans_requirement'] = self.total_fans_requirement_var.get()
            
            # Update auto start career config
            if 'auto_start_career' not in config:
                config['auto_start_career'] = {}
            
            config['auto_start_career']['include_guests_legacy'] = self.include_guests_legacy_var.get()
            config['auto_start_career']['support_speciality'] = self.support_speciality_var.get()
            config['auto_start_career']['support_rarity'] = self.support_rarity_var.get()
            
            # Save to file
            self.main_window.set_config(config)
            
            messagebox.showinfo("Success", "Restart settings saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save restart settings: {e}")
    
    def create_others_tab(self):
        """Create the Others tab"""
        # Add tab to tabview
        others_tab = self.tabview.add("Others")
        
        # Create scrollable frame inside the others tab
        others_scroll = ctk.CTkScrollableFrame(others_tab, fg_color="transparent", corner_radius=0)
        others_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        config = self.main_window.get_config()
        
        # Debug Mode
        debug_frame = ctk.CTkFrame(others_scroll, fg_color=self.colors['bg_light'], corner_radius=10)
        debug_frame.pack(fill=tk.X, pady=10, padx=10)
        
        debug_title = ctk.CTkLabel(debug_frame, text="Debug Settings", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_light'])
        debug_title.pack(pady=(15, 10))
        
        self.debug_mode_var = tk.BooleanVar(value=config.get('debug_mode', False))
        debug_checkbox = ctk.CTkCheckBox(debug_frame, text="Debug Mode", variable=self.debug_mode_var, text_color=self.colors['text_light'])
        debug_checkbox.pack(pady=(0, 15))
    
    def refresh_config(self):
        """Refresh the configuration display (placeholder for now)"""
        # This would update all displayed values when config changes
        # For now, just a placeholder
        pass
    
    def save_config(self):
        """Save the current configuration"""
        try:
            # Get current config
            config = self.main_window.get_config()
            
            # Update ADB config
            config['adb_config'] = {
                'device_address': self.device_address_var.get(),
                'adb_path': self.adb_path_var.get(),
                'screenshot_timeout': self.screenshot_timeout_var.get(),
                'input_delay': self.input_delay_var.get(),
                'connection_timeout': self.connection_timeout_var.get()
            }
            
            # Update debug mode
            config['debug_mode'] = self.debug_mode_var.get()
            
            # Save to file
            self.main_window.set_config(config)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def open_good_choices_window(self):
        """Open window to edit good choices list"""
        self.open_event_choices_window("Good_choices", "Good Choices")
    
    def open_bad_choices_window(self):
        """Open window to edit bad choices list"""
        self.open_event_choices_window("Bad_choices", "Bad Choices")
    
    def open_event_choices_window(self, choice_type, title):
        """Open window to edit event choices"""
        try:
            # Load current event priority data
            with open('event_priority.json', 'r', encoding='utf-8') as f:
                event_data = json.load(f)
            
            choices = event_data.get(choice_type, [])
            
            # Create new window
            window = ctk.CTkToplevel()
            window.title(f"Edit {title}")
            window.geometry("500x400")
            window.configure(fg_color=self.colors['bg_dark'])
            
            # Title
            title_label = ctk.CTkLabel(window, text=f"Edit {title}", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.colors['text_light'])
            title_label.pack(pady=(15, 10))
            
            # List frame
            list_frame = ctk.CTkFrame(window, fg_color=self.colors['bg_medium'], corner_radius=10)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
            
            # Choices listbox
            choices_listbox = tk.Listbox(list_frame, bg=self.colors['bg_light'], fg=self.colors['text_light'], 
                                       selectmode=tk.SINGLE, font=ctk.CTkFont(size=12))
            choices_listbox.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
            
            # Populate listbox
            for choice in choices:
                choices_listbox.insert(tk.END, choice)
            
            # Buttons frame
            btn_frame = ctk.CTkFrame(window, fg_color="transparent")
            btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
            
            # Add button
            add_btn = ctk.CTkButton(btn_frame, text="Add", command=lambda: self.add_event_choice(choices_listbox, choices),
                                  fg_color=self.colors['accent_green'], corner_radius=8)
            add_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # Remove button
            remove_btn = ctk.CTkButton(btn_frame, text="Remove", command=lambda: self.remove_event_choice(choices_listbox, choices),
                                     fg_color=self.colors['accent_red'], corner_radius=8)
            remove_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # Move up button
            up_btn = ctk.CTkButton(btn_frame, text="↑", command=lambda: self.move_event_choice(choices_listbox, choices, -1),
                                 fg_color=self.colors['accent_blue'], corner_radius=8, width=40)
            up_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # Move down button
            down_btn = ctk.CTkButton(btn_frame, text="↓", command=lambda: self.move_event_choice(choices_listbox, choices, 1),
                                   fg_color=self.colors['accent_blue'], corner_radius=8, width=40)
            down_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # Save button
            save_btn = ctk.CTkButton(btn_frame, text="Save", command=lambda: self.save_event_choices(window, choice_type, choices),
                                   fg_color=self.colors['accent_green'], corner_radius=8)
            save_btn.pack(side=tk.RIGHT)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open {title} window: {e}")
    
    def add_event_choice(self, listbox, choices):
        """Add a new event choice"""
        dialog = ctk.CTkInputDialog(text="Enter new choice:", title="Add Choice")
        choice = dialog.get_input()
        if choice and choice.strip():
            choices.append(choice.strip())
            listbox.insert(tk.END, choice.strip())
    
    def remove_event_choice(self, listbox, choices):
        """Remove selected event choice"""
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            choices.pop(index)
            listbox.delete(index)
    
    def move_event_choice(self, listbox, choices, direction):
        """Move event choice up or down"""
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            new_index = index + direction
            if 0 <= new_index < len(choices):
                choices[index], choices[new_index] = choices[new_index], choices[index]
                # Refresh listbox
                listbox.delete(0, tk.END)
                for choice in choices:
                    listbox.insert(tk.END, choice)
                listbox.selection_set(new_index)
    
    def save_event_choices(self, window, choice_type, choices):
        """Save event choices to file"""
        try:
            with open('event_priority.json', 'r', encoding='utf-8') as f:
                event_data = json.load(f)
            
            event_data[choice_type] = choices
            
            with open('event_priority.json', 'w', encoding='utf-8') as f:
                json.dump(event_data, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Success", f"{choice_type} saved successfully!")
            window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save {choice_type}: {e}")
    
    def open_skill_file(self):
        """Open file dialog to select skill file"""
        filename = filedialog.askopenfilename(
            title="Select Skill File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=self.skill_file_var.get()
        )
        if filename:
            self.skill_file_var.set(os.path.basename(filename))
    
    def open_skill_list_window(self):
        """Open window to edit skill lists"""
        try:
            # Load current skill data
            skill_file = self.skill_file_var.get()
            if not os.path.exists(skill_file):
                messagebox.showerror("Error", f"Skill file {skill_file} not found!")
                return
            
            with open(skill_file, 'r', encoding='utf-8') as f:
                skill_data = json.load(f)
            
            # Create new window
            window = ctk.CTkToplevel()
            window.title("Edit Skill Lists")
            window.geometry("800x600")
            window.configure(fg_color=self.colors['bg_dark'])
            
            # Title
            title_label = ctk.CTkLabel(window, text="Edit Skill Lists", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.colors['text_light'])
            title_label.pack(pady=(15, 10))
            
            # Main content frame
            content_frame = ctk.CTkFrame(window, fg_color="transparent")
            content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
            
            # Left side - Priority Skills
            left_frame = ctk.CTkFrame(content_frame, fg_color=self.colors['bg_medium'], corner_radius=10)
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
            
            ctk.CTkLabel(left_frame, text="Priority Skills", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_light']).pack(pady=(15, 10))
            
            # Priority skills listbox
            priority_listbox = tk.Listbox(left_frame, bg=self.colors['bg_light'], fg=self.colors['text_light'], 
                                        selectmode=tk.SINGLE, font=ctk.CTkFont(size=12))
            priority_listbox.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
            
            priority_skills = skill_data.get('skill_priority', [])
            for i, skill in enumerate(priority_skills, 1):
                priority_listbox.insert(tk.END, f"{i}. {skill}")
            
            # Priority skills buttons
            priority_btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
            priority_btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
            
            ctk.CTkButton(priority_btn_frame, text="Add", command=lambda: self.add_priority_skill(priority_listbox, priority_skills),
                         fg_color=self.colors['accent_green'], corner_radius=8).pack(side=tk.LEFT, padx=(0, 5))
            ctk.CTkButton(priority_btn_frame, text="Remove", command=lambda: self.remove_priority_skill(priority_listbox, priority_skills),
                         fg_color=self.colors['accent_red'], corner_radius=8).pack(side=tk.LEFT, padx=(0, 5))
            ctk.CTkButton(priority_btn_frame, text="↑", command=lambda: self.move_priority_skill(priority_listbox, priority_skills, -1),
                         fg_color=self.colors['accent_blue'], corner_radius=8, width=40).pack(side=tk.LEFT, padx=(0, 5))
            ctk.CTkButton(priority_btn_frame, text="↓", command=lambda: self.move_priority_skill(priority_listbox, priority_skills, 1),
                         fg_color=self.colors['accent_blue'], corner_radius=8, width=40).pack(side=tk.LEFT, padx=(0, 5))
            
            # Right side - Gold Skill Relationships
            right_frame = ctk.CTkFrame(content_frame, fg_color=self.colors['bg_medium'], corner_radius=10)
            right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
            
            ctk.CTkLabel(right_frame, text="Gold Skill Relationships", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_light']).pack(pady=(15, 10))
            
            # Gold skill relationships frame
            gold_frame = ctk.CTkFrame(right_frame, fg_color=self.colors['bg_light'], corner_radius=8)
            gold_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
            
            # Headers
            header_frame = ctk.CTkFrame(gold_frame, fg_color="transparent")
            header_frame.pack(fill=tk.X, padx=10, pady=5)
            ctk.CTkLabel(header_frame, text="Gold Skill", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors['text_gray']).pack(side=tk.LEFT)
            ctk.CTkLabel(header_frame, text="Base Skill", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors['text_gray']).pack(side=tk.RIGHT)
            
            # Gold skill relationships listbox
            gold_listbox = tk.Listbox(gold_frame, bg=self.colors['bg_light'], fg=self.colors['text_light'], 
                                    selectmode=tk.SINGLE, font=ctk.CTkFont(size=11))
            gold_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
            
            gold_relationships = skill_data.get('gold_skill_upgrades', {})
            for gold_skill, base_skill in gold_relationships.items():
                gold_listbox.insert(tk.END, f"{gold_skill} → {base_skill}")
            
            # Gold skill buttons
            gold_btn_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
            gold_btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
            
            ctk.CTkButton(gold_btn_frame, text="Add", command=lambda: self.add_gold_relationship(gold_listbox, gold_relationships),
                         fg_color=self.colors['accent_green'], corner_radius=8).pack(side=tk.LEFT, padx=(0, 5))
            ctk.CTkButton(gold_btn_frame, text="Remove", command=lambda: self.remove_gold_relationship(gold_listbox, gold_relationships),
                         fg_color=self.colors['accent_red'], corner_radius=8).pack(side=tk.LEFT, padx=(0, 5))
            
            # Save button
            save_btn = ctk.CTkButton(window, text="Save All Changes", 
                                   command=lambda: self.save_skill_lists(window, skill_file, priority_skills, gold_relationships),
                                   fg_color=self.colors['accent_green'], corner_radius=8, height=35)
            save_btn.pack(pady=(0, 15))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open skill list window: {e}")
    
    def add_priority_skill(self, listbox, skills):
        """Add a new priority skill"""
        dialog = ctk.CTkInputDialog(text="Enter new skill:", title="Add Priority Skill")
        skill = dialog.get_input()
        if skill and skill.strip():
            skills.append(skill.strip())
            listbox.insert(tk.END, f"{len(skills)}. {skill.strip()}")
    
    def remove_priority_skill(self, listbox, skills):
        """Remove selected priority skill"""
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            skills.pop(index)
            # Refresh listbox
            listbox.delete(0, tk.END)
            for i, skill in enumerate(skills, 1):
                listbox.insert(tk.END, f"{i}. {skill}")
    
    def move_priority_skill(self, listbox, skills, direction):
        """Move priority skill up or down"""
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            new_index = index + direction
            if 0 <= new_index < len(skills):
                skills[index], skills[new_index] = skills[new_index], skills[index]
                # Refresh listbox
                listbox.delete(0, tk.END)
                for i, skill in enumerate(skills, 1):
                    listbox.insert(tk.END, f"{i}. {skill}")
                listbox.selection_set(new_index)
    
    def add_gold_relationship(self, listbox, relationships):
        """Add a new gold skill relationship"""
        dialog = ctk.CTkInputDialog(text="Enter gold skill:", title="Add Gold Skill")
        gold_skill = dialog.get_input()
        if gold_skill and gold_skill.strip():
            dialog2 = ctk.CTkInputDialog(text="Enter base skill:", title="Add Base Skill")
            base_skill = dialog2.get_input()
            if base_skill and base_skill.strip():
                relationships[gold_skill.strip()] = base_skill.strip()
                listbox.insert(tk.END, f"{gold_skill.strip()} → {base_skill.strip()}")
    
    def remove_gold_relationship(self, listbox, relationships):
        """Remove selected gold skill relationship"""
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            item = listbox.get(index)
            gold_skill = item.split(" → ")[0]
            if gold_skill in relationships:
                del relationships[gold_skill]
                listbox.delete(index)
    
    def save_skill_lists(self, window, skill_file, priority_skills, gold_relationships):
        """Save skill lists to file"""
        try:
            skill_data = {
                "skill_priority": priority_skills,
                "gold_skill_upgrades": gold_relationships
            }
            
            with open(skill_file, 'w', encoding='utf-8') as f:
                json.dump(skill_data, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Success", "Skill lists saved successfully!")
            window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save skill lists: {e}")
