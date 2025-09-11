"""
Restart Tab for Uma Musume Auto-Train Bot GUI Configuration

Contains restart conditions and career management settings.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

try:
    from ..font_manager import get_font
except ImportError:
    from font_manager import get_font

class RestartTab:
    """Restart configuration tab containing restart career settings"""
    
    def __init__(self, tabview, config_panel, colors):
        """Initialize the Restart tab
        
        Args:
            tabview: The parent CTkTabview widget
            config_panel: Reference to the main ConfigPanel instance
            colors: Color scheme dictionary
        """
        self.tabview = tabview
        self.config_panel = config_panel
        self.colors = colors
        self.main_window = config_panel.main_window
        
        # Create the tab
        self.create_tab()
    
    def create_tab(self):
        """Create the Restart tab with restart career settings"""
        # Add tab to tabview
        restart_tab = self.tabview.add("Restart")
        
        # Create scrollable frame inside the restart tab
        restart_scroll = ctk.CTkScrollableFrame(restart_tab, fg_color="transparent", corner_radius=0)
        restart_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        config = self.main_window.get_config()
        
        # Restart Career Settings Section
        self._create_restart_settings_section(restart_scroll, config)
        
        # Legacy Settings Section
        self._create_legacy_settings_section(restart_scroll, config)
        
        # Support Settings Section
        self._create_support_settings_section(restart_scroll, config)
        
        # Save button
        restart_save_btn = ctk.CTkButton(restart_tab, text="Save Restart Settings", 
                                       command=self.save_restart_settings,
                                       fg_color=self.colors['accent_green'], corner_radius=8, height=35,
                                       font=get_font('button'))
        restart_save_btn.pack(side=tk.BOTTOM, pady=20)
    
    def _create_restart_settings_section(self, parent, config):
        """Create the restart career settings section"""
        restart_frame = ctk.CTkFrame(parent, fg_color=self.colors['bg_light'], corner_radius=10)
        restart_frame.pack(fill=tk.X, pady=10, padx=10)
        
        restart_title = ctk.CTkLabel(restart_frame, text="Restart Career Settings", font=get_font('section_title'), text_color=self.colors['text_light'])
        restart_title.pack(pady=(15, 10))
        
        # Restart Career Run checkbox
        self.restart_enabled_var = tk.BooleanVar(value=config.get('restart_career', {}).get('restart_enabled', False))
        restart_checkbox = ctk.CTkCheckBox(restart_frame, text="Restart Career run", variable=self.restart_enabled_var, 
                                         text_color=self.colors['text_light'], font=get_font('checkbox'),
                                         command=self.toggle_restart_settings)
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
                                       text_color=self.colors['text_light'], font=get_font('radiobutton'),
                                       command=self.on_criteria_change)
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
                                      text_color=self.colors['text_light'], font=get_font('radiobutton'),
                                      command=self.on_criteria_change)
        fans_radio.pack(side=tk.LEFT)
        self.total_fans_requirement_var = tk.IntVar(value=config.get('restart_career', {}).get('total_fans_requirement', 0))
        fans_entry = ctk.CTkEntry(fans_frame, textvariable=self.total_fans_requirement_var, width=80, corner_radius=8)
        fans_entry.pack(side=tk.LEFT, padx=(10, 0))
        fans_label = ctk.CTkLabel(fans_frame, text="fans", text_color=self.colors['text_light'])
        fans_label.pack(side=tk.LEFT, padx=(5, 0))
    
    def _create_legacy_settings_section(self, parent, config):
        """Create the legacy settings section"""
        self.legacy_frame = ctk.CTkFrame(parent, fg_color=self.colors['bg_light'], corner_radius=10)
        if self.restart_enabled_var.get():
            self.legacy_frame.pack(fill=tk.X, pady=10, padx=10)
        
        legacy_title = ctk.CTkLabel(self.legacy_frame, text="Legacy Settings", font=get_font('section_title'), text_color=self.colors['text_light'])
        legacy_title.pack(pady=(15, 10))
        
        # Include Legacy from Guests checkbox
        self.include_guests_legacy_var = tk.BooleanVar(value=config.get('auto_start_career', {}).get('include_guests_legacy', False))
        legacy_checkbox = ctk.CTkCheckBox(self.legacy_frame, text="Include Legacy from Guests", variable=self.include_guests_legacy_var, 
                                        text_color=self.colors['text_light'], font=get_font('checkbox'))
        legacy_checkbox.pack(anchor=tk.W, pady=(0, 15))
    
    def _create_support_settings_section(self, parent, config):
        """Create the support settings section"""
        self.support_frame = ctk.CTkFrame(parent, fg_color=self.colors['bg_light'], corner_radius=10)
        if self.restart_enabled_var.get():
            self.support_frame.pack(fill=tk.X, pady=10, padx=10)
        
        support_title = ctk.CTkLabel(self.support_frame, text="Support Settings (Note: Only choose followed player support)", 
                                   font=get_font('section_title'), text_color=self.colors['text_light'])
        support_title.pack(pady=(15, 10))
        
        # Support Speciality
        speciality_frame = ctk.CTkFrame(self.support_frame, fg_color="transparent")
        speciality_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(speciality_frame, text="Support Speciality:", text_color=self.colors['text_light'], font=get_font('label')).pack(side=tk.LEFT)
        self.support_speciality_var = tk.StringVar(value=config.get('auto_start_career', {}).get('support_speciality', 'STA'))
        speciality_combo = ctk.CTkOptionMenu(speciality_frame, values=['SPD', 'STA', 'PWR', 'GUTS', 'WIT', 'PAL'], 
                                           variable=self.support_speciality_var, fg_color=self.colors['accent_blue'], 
                                           corner_radius=8, button_color=self.colors['accent_blue'],
                                           button_hover_color=self.colors['accent_green'])
        speciality_combo.pack(side=tk.RIGHT)
        
        # Support Rarity
        rarity_frame = ctk.CTkFrame(self.support_frame, fg_color="transparent")
        rarity_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(rarity_frame, text="Support Rarity:", text_color=self.colors['text_light'], font=get_font('label')).pack(side=tk.LEFT)
        self.support_rarity_var = tk.StringVar(value=config.get('auto_start_career', {}).get('support_rarity', 'SSR'))
        rarity_combo = ctk.CTkOptionMenu(rarity_frame, values=['R', 'SR', 'SSR'], 
                                       variable=self.support_rarity_var, fg_color=self.colors['accent_blue'], 
                                       corner_radius=8, button_color=self.colors['accent_blue'],
                                       button_hover_color=self.colors['accent_green'])
        rarity_combo.pack(side=tk.RIGHT)
    
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