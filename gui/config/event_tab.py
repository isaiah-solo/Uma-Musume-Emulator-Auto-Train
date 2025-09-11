"""
Event Tab for Uma Musume Auto-Train Bot GUI Configuration

Contains event handling settings and choice priorities.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import os

try:
    from ..font_manager import get_font
except ImportError:
    from font_manager import get_font

class EventTab:
    """Event configuration tab containing event choice management"""
    
    def __init__(self, tabview, config_panel, colors):
        """Initialize the Event tab
        
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
        """Create the Event tab with event choice management"""
        # Add tab to tabview
        event_tab = self.tabview.add("Event")
        
        # Create scrollable frame inside the event tab
        event_scroll = ctk.CTkScrollableFrame(event_tab, fg_color="transparent", corner_radius=0)
        event_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Event Settings Frame
        event_frame = ctk.CTkFrame(event_scroll, fg_color=self.colors['bg_light'], corner_radius=10)
        event_frame.pack(fill=tk.X, pady=10, padx=10)
        
        event_title = ctk.CTkLabel(event_frame, text="Event Choice Management", font=get_font('section_title'), text_color=self.colors['text_light'])
        event_title.pack(pady=(15, 10))
        
        # Good Choices Section
        good_frame = ctk.CTkFrame(event_frame, fg_color="transparent")
        good_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ctk.CTkLabel(good_frame, text="Good Choices:", text_color=self.colors['text_light'], font=get_font('body_large')).pack(side=tk.LEFT)
        good_btn = ctk.CTkButton(good_frame, text="Open List", 
                                command=self.open_good_choices_window,
                                fg_color=self.colors['accent_green'], corner_radius=8, height=30, width=100,
                                font=get_font('button'))
        good_btn.pack(side=tk.RIGHT)
        
        # Bad Choices Section
        bad_frame = ctk.CTkFrame(event_frame, fg_color="transparent")
        bad_frame.pack(fill=tk.X, padx=15, pady=(10, 15))
        
        ctk.CTkLabel(bad_frame, text="Bad Choices:", text_color=self.colors['text_light'], font=get_font('body_large')).pack(side=tk.LEFT)
        bad_btn = ctk.CTkButton(bad_frame, text="Open List", 
                               command=self.open_bad_choices_window,
                               fg_color=self.colors['accent_red'], corner_radius=8, height=30, width=100,
                               font=get_font('button'))
        bad_btn.pack(side=tk.RIGHT)
    
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
            window = ctk.CTkToplevel(self.config_panel.winfo_toplevel())
            window.title(f"Edit {title}")
            window.geometry("500x400")
            window.configure(fg_color=self.colors['bg_dark'])
            try:
                window.transient(self.config_panel.winfo_toplevel())
            except Exception:
                pass
            window.lift()
            window.focus_force()
            try:
                window.attributes("-topmost", True)
                window.after(200, lambda: window.attributes("-topmost", False))
            except Exception:
                pass
            
            # Title
            title_label = ctk.CTkLabel(window, text=f"Edit {title}", font=get_font('title_medium'), text_color=self.colors['text_light'])
            title_label.pack(pady=(15, 10))
            
            # List frame
            list_frame = ctk.CTkFrame(window, fg_color=self.colors['bg_medium'], corner_radius=10)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
            
            # Choices listbox
            choices_listbox = tk.Listbox(list_frame, bg=self.colors['bg_light'], fg=self.colors['text_light'], 
                                       selectmode=tk.SINGLE, font=get_font('body_large'))
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