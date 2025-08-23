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
    
    def create_racing_tab(self):
        """Create the Racing tab"""
        # Add tab to tabview
        racing_tab = self.tabview.add("Racing")
        
        # Placeholder content for now
        placeholder_label = ctk.CTkLabel(racing_tab, text="Racing settings coming soon...", text_color=self.colors['text_light'])
        placeholder_label.pack(pady=50)
    
    def create_event_tab(self):
        """Create the Event tab"""
        # Add tab to tabview
        event_tab = self.tabview.add("Event")
        
        # Placeholder content for now
        placeholder_label = ctk.CTkLabel(event_tab, text="Event settings coming soon...", text_color=self.colors['text_light'])
        placeholder_label.pack(pady=50)
    
    def create_skill_tab(self):
        """Create the Skill tab"""
        # Add tab to tabview
        skill_tab = self.tabview.add("Skill")
        
        # Placeholder content for now
        placeholder_label = ctk.CTkLabel(skill_tab, text="Skill settings coming soon...", text_color=self.colors['text_light'])
        placeholder_label.pack(pady=50)
    
    def create_others_tab(self):
        """Create the Others tab"""
        # Add tab to tabview
        others_tab = self.tabview.add("Others")
        
        config = self.main_window.get_config()
        
        # Debug Mode
        debug_frame = ctk.CTkFrame(others_tab, fg_color=self.colors['bg_light'], corner_radius=10)
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
