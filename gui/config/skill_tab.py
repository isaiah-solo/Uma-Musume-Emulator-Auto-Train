"""
Skill Tab for Uma Musume Auto-Train Bot GUI Configuration

Contains skill purchase settings, support card configuration, and skill priorities.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os

try:
    from ..font_manager import get_font
    from .skill_list_helper import open_skill_list_window
except ImportError:
    from font_manager import get_font
    from skill_list_helper import open_skill_list_window

class SkillTab:
    """Skill configuration tab containing skill management settings"""
    
    def __init__(self, tabview, config_panel, colors):
        """Initialize the Skill tab
        
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
        """Create the Skill tab with skill management settings"""
        # Add tab to tabview
        skill_tab = self.tabview.add("Skill")
        
        config = self.main_window.get_config()
        
        # Fixed header section (always visible)
        header_frame = ctk.CTkFrame(skill_tab, fg_color=self.colors['bg_light'], corner_radius=10)
        header_frame.pack(fill=tk.X, pady=(10, 5), padx=10)
        
        skill_title = ctk.CTkLabel(header_frame, text="Skill Management", font=get_font('section_title'), text_color=self.colors['text_light'])
        skill_title.pack(pady=(15, 10))
        
        # Enable Skill Point Check
        enable_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        enable_frame.pack(fill=tk.X, padx=15, pady=5)
        self.enable_skill_check_var = tk.BooleanVar(value=config.get('enable_skill_point_check', True))
        enable_checkbox = ctk.CTkCheckBox(enable_frame, text="Enable Skill Point check and Skill Purchase", 
                                        variable=self.enable_skill_check_var, text_color=self.colors['text_light'],
                                        font=get_font('checkbox'), command=self.toggle_skill_settings)
        enable_checkbox.pack(anchor=tk.W)
        
        self._create_skill_settings(header_frame, config)
        self._create_save_button(skill_tab)
    
    def _create_skill_settings(self, parent, config):
        """Create skill settings section"""
        # Container for all skill settings (hidden when checkbox is unchecked)
        self.skill_settings_container = ctk.CTkFrame(parent, fg_color=self.colors['bg_light'], corner_radius=10)
        if self.enable_skill_check_var.get():
            self.skill_settings_container.pack(fill=tk.X, pady=5)
        
        # Skill Point Cap
        cap_frame = ctk.CTkFrame(self.skill_settings_container, fg_color="transparent")
        cap_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(cap_frame, text="Skill Point Cap:", text_color=self.colors['text_light'], font=get_font('label')).pack(side=tk.LEFT)
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
    
    def _create_save_button(self, parent):
        """Create save button"""
        self.skill_save_btn = ctk.CTkButton(parent, text="Save Skill Settings", 
                                          command=self.save_skill_settings,
                                          fg_color=self.colors['accent_green'], corner_radius=8, height=35)
        self.skill_save_btn.pack(side=tk.BOTTOM, pady=20)
    
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
    
    def open_skill_file(self):
        """Open file dialog to select skill file"""
        filename = filedialog.askopenfilename(
            title="Select Skill File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=self.skill_file_var.get(),
            parent=self.config_panel.winfo_toplevel()
        )
        if filename:
            self.skill_file_var.set(os.path.basename(filename))
    
    def open_skill_list_window(self):
        """Open window to edit skill lists"""
        open_skill_list_window(self)
