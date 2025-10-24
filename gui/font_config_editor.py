"""
Font Configuration Editor for Uma Musume Auto-Train Bot GUI

This module provides a GUI for editing font configurations.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, font
import json
import os

try:
    from .font_manager import get_font_manager, reload_fonts
except ImportError:
    from font_manager import get_font_manager, reload_fonts

class FontConfigEditor:
    """GUI for editing font configurations"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.font_manager = get_font_manager()
        self.window = None
        self.font_vars = {}
        
    def open_editor(self):
        """Open the font configuration editor window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
            
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("Font Configuration Editor")
        self.window.geometry("800x600")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Colors
        colors = {
            'bg_dark': '#212121',
            'bg_medium': '#2b2b2b', 
            'bg_light': '#3c3c3c',
            'text_light': '#ffffff',
            'text_gray': '#b0b0b0',
            'accent_blue': '#1f538d',
            'accent_green': '#2d5a27',
            'accent_red': '#8b2635'
        }
        
        # Main frame
        main_frame = ctk.CTkFrame(self.window, fg_color=colors['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="Font Configuration Editor", 
                                  font=ctk.CTkFont(size=18, weight="bold"),
                                  text_color=colors['text_light'])
        title_label.pack(pady=(0, 20))
        
        # Scrollable frame for font settings
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color=colors['bg_medium'])
        scroll_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create font controls
        self.create_font_controls(scroll_frame, colors)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill=tk.X)
        
        ctk.CTkButton(button_frame, text="Apply Changes", 
                     command=self.apply_changes,
                     fg_color=colors['accent_green'],
                     width=120).pack(side=tk.LEFT, padx=(0, 10))
        
        ctk.CTkButton(button_frame, text="Reset to Defaults",
                     command=self.reset_to_defaults,
                     fg_color=colors['accent_red'],
                     width=120).pack(side=tk.LEFT, padx=(0, 10))
        
        ctk.CTkButton(button_frame, text="Close",
                     command=self.window.destroy,
                     fg_color=colors['accent_blue'],
                     width=120).pack(side=tk.RIGHT)
    
    def create_font_controls(self, parent, colors):
        """Create controls for each font setting"""
        fonts = self.font_manager.fonts
        
        # Get available system fonts
        system_fonts = sorted(font.families())
        
        for font_name, font_config in fonts.items():
            # Frame for this font
            font_frame = ctk.CTkFrame(parent, fg_color=colors['bg_light'])
            font_frame.pack(fill=tk.X, pady=5, padx=10)
            
            # Font name label
            name_label = ctk.CTkLabel(font_frame, text=font_name.replace('_', ' ').title(),
                                    font=ctk.CTkFont(size=12, weight="bold"),
                                    text_color=colors['text_light'])
            name_label.pack(anchor=tk.W, padx=15, pady=(10, 5))
            
            # Controls frame
            controls_frame = ctk.CTkFrame(font_frame, fg_color="transparent")
            controls_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
            
            # Family dropdown
            ctk.CTkLabel(controls_frame, text="Family:", text_color=colors['text_gray']).grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
            family_var = tk.StringVar(value=font_config.get('family', 'Comic Sans MS'))
            family_dropdown = ctk.CTkComboBox(controls_frame, values=system_fonts[:50], variable=family_var, width=200)
            family_dropdown.grid(row=0, column=1, padx=(0, 20), sticky=tk.W)
            
            # Size spinbox
            ctk.CTkLabel(controls_frame, text="Size:", text_color=colors['text_gray']).grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
            size_var = tk.IntVar(value=font_config.get('size', 11))
            size_spinbox = ctk.CTkEntry(controls_frame, textvariable=size_var, width=60)
            size_spinbox.grid(row=0, column=3, padx=(0, 20), sticky=tk.W)
            
            # Weight dropdown
            ctk.CTkLabel(controls_frame, text="Weight:", text_color=colors['text_gray']).grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
            weight_var = tk.StringVar(value=font_config.get('weight', 'normal'))
            weight_dropdown = ctk.CTkComboBox(controls_frame, values=['normal', 'bold'], variable=weight_var, width=100)
            weight_dropdown.grid(row=0, column=5, sticky=tk.W)
            
            # Store variables
            self.font_vars[font_name] = {
                'family': family_var,
                'size': size_var,
                'weight': weight_var
            }
            
            # Configure grid weights
            controls_frame.grid_columnconfigure(1, weight=1)
    
    def apply_changes(self):
        """Apply font changes and reload the configuration"""
        try:
            # Build new font configuration
            new_fonts = {}
            for font_name, vars_dict in self.font_vars.items():
                new_fonts[font_name] = {
                    'family': vars_dict['family'].get(),
                    'size': vars_dict['size'].get(),
                    'weight': vars_dict['weight'].get()
                }
            
            # Save configuration
            new_config = {
                'fonts': new_fonts,
                'fallback_fonts': self.font_manager.fallback_fonts
            }
            
            self.font_manager.save_config(new_config)
            
            # Reload fonts
            reload_fonts()
            
            messagebox.showinfo("Success", "Font configuration saved successfully!\n\nNote: Some changes may require restarting the application to take full effect.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save font configuration:\n{e}")
    
    def reset_to_defaults(self):
        """Reset all fonts to default values"""
        if messagebox.askyesno("Reset Fonts", "Are you sure you want to reset all fonts to default values?"):
            # Reset all variables to defaults
            defaults = {
                'title_large': {'family': 'Comic Sans MS', 'size': 18, 'weight': 'bold'},
                'title_medium': {'family': 'Comic Sans MS', 'size': 16, 'weight': 'bold'},
                'title_small': {'family': 'Comic Sans MS', 'size': 14, 'weight': 'bold'},
                'body_large': {'family': 'Comic Sans MS', 'size': 12, 'weight': 'normal'},
                'body_medium': {'family': 'Comic Sans MS', 'size': 11, 'weight': 'normal'},
                'body_small': {'family': 'Comic Sans MS', 'size': 10, 'weight': 'normal'},
                'monospace_large': {'family': 'Consolas', 'size': 18, 'weight': 'normal'},
                'monospace_medium': {'family': 'Consolas', 'size': 14, 'weight': 'normal'},
                'monospace_small': {'family': 'Consolas', 'size': 12, 'weight': 'normal'},
                'button': {'family': 'Comic Sans MS', 'size': 11, 'weight': 'bold'},
                'label': {'family': 'Comic Sans MS', 'size': 14, 'weight': 'normal'},
                'input': {'family': 'Comic Sans MS', 'size': 11, 'weight': 'normal'},
                'section_title': {'family': 'Comic Sans MS', 'size': 14, 'weight': 'bold'},
                'tab_title': {'family': 'Comic Sans MS', 'size': 16, 'weight': 'bold'},
                'status_title': {'family': 'Comic Sans MS', 'size': 16, 'weight': 'bold'},
                'status_value': {'family': 'Comic Sans MS', 'size': 14, 'weight': 'bold'},
                'status_label': {'family': 'Comic Sans MS', 'size': 10, 'weight': 'normal'},
                'log_text': {'family': 'Consolas', 'size': 18, 'weight': 'normal'},
                'dropdown': {'family': 'Comic Sans MS', 'size': 11, 'weight': 'normal'},
                'checkbox': {'family': 'Comic Sans MS', 'size': 10, 'weight': 'normal'},
                'radiobutton': {'family': 'Comic Sans MS', 'size': 10, 'weight': 'normal'},
                'tooltip': {'family': 'Comic Sans MS', 'size': 9, 'weight': 'normal'}
            }
            
            for font_name, default_config in defaults.items():
                if font_name in self.font_vars:
                    self.font_vars[font_name]['family'].set(default_config['family'])
                    self.font_vars[font_name]['size'].set(default_config['size'])
                    self.font_vars[font_name]['weight'].set(default_config['weight'])


def open_font_editor(parent=None):
    """Convenience function to open the font editor"""
    editor = FontConfigEditor(parent)
    editor.open_editor()
