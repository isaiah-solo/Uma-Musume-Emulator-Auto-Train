"""
Others Tab for Uma Musume Auto-Train Bot GUI Configuration

Contains debug settings and other miscellaneous configuration options.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

try:
    from ..font_manager import get_font
except ImportError:
    from font_manager import get_font

class OthersTab:
    """Others configuration tab containing debug and miscellaneous settings"""
    
    def __init__(self, tabview, config_panel, colors):
        """Initialize the Others tab
        
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
        """Create the Others tab"""
        # Add tab to tabview
        others_tab = self.tabview.add("Others")
        
        # Create scrollable frame inside the others tab
        others_scroll = ctk.CTkScrollableFrame(others_tab, fg_color="transparent", corner_radius=0)
        others_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        config = self.main_window.get_config()
        
        # Debug Mode Section
        self._create_debug_section(others_scroll, config)
        
        # Save button
        save_btn = ctk.CTkButton(others_scroll, text="Save Other Settings", 
                               command=self.save_other_settings,
                               fg_color=self.colors['accent_green'], corner_radius=8, height=35,
                               font=get_font('button'))
        save_btn.pack(pady=20)
    
    def _create_debug_section(self, parent, config):
        """Create the debug settings section"""
        debug_frame = ctk.CTkFrame(parent, fg_color=self.colors['bg_light'], corner_radius=10)
        debug_frame.pack(fill=tk.X, pady=10, padx=10)
        
        debug_title = ctk.CTkLabel(debug_frame, text="Debug Settings", font=get_font('section_title'), text_color=self.colors['text_light'])
        debug_title.pack(pady=(15, 10))
        
        self.debug_mode_var = tk.BooleanVar(value=config.get('debug_mode', False))
        debug_checkbox = ctk.CTkCheckBox(debug_frame, text="Debug Mode", variable=self.debug_mode_var, text_color=self.colors['text_light'], font=get_font('checkbox'))
        debug_checkbox.pack(pady=(0, 15))
    
    def save_other_settings(self):
        """Save other settings to config"""
        try:
            config = self.main_window.get_config()
            
            # Update debug mode
            config['debug_mode'] = self.debug_mode_var.get()
            
            # Save to file
            self.main_window.set_config(config)
            messagebox.showinfo("Success", "Other settings saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save other settings: {e}")
