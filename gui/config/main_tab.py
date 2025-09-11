"""
Main Tab for Uma Musume Auto-Train Bot GUI Configuration

Contains ADB configuration and screenshot capture settings.
"""

import customtkinter as ctk
import tkinter as tk

try:
    from ..font_manager import get_font
except ImportError:
    from font_manager import get_font

class MainTab:
    """Main configuration tab containing ADB and capture settings"""
    
    def __init__(self, tabview, config_panel, colors):
        """Initialize the Main tab
        
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
        """Create the Main tab with ADB configuration"""
        # Add tab to tabview
        main_tab = self.tabview.add("Main")
        
        # Create scrollable frame inside the main tab
        main_scroll = ctk.CTkScrollableFrame(main_tab, fg_color="transparent", corner_radius=0)
        main_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        cfg = self.main_window.get_config()

        # ADB Configuration Frame
        adb_frame = ctk.CTkFrame(main_scroll, fg_color=self.colors['bg_light'], corner_radius=10)
        adb_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # ADB Configuration Title
        adb_title = ctk.CTkLabel(adb_frame, text="ADB Configuration", font=get_font('section_title'), text_color=self.colors['text_light'])
        adb_title.pack(pady=(15, 10))
        
        # Device Address
        device_frame = ctk.CTkFrame(adb_frame, fg_color="transparent")
        device_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(device_frame, text="Device Address:", text_color=self.colors['text_light'], font=get_font('label')).pack(side=tk.LEFT)
        self.config_panel.device_address_var = tk.StringVar(value=cfg.get('adb_config', {}).get('device_address', '127.0.0.1:7555'))
        ctk.CTkEntry(device_frame, textvariable=self.config_panel.device_address_var, width=200, corner_radius=8, font=get_font('input')).pack(side=tk.RIGHT)
        
        # ADB Path
        adb_path_frame = ctk.CTkFrame(adb_frame, fg_color="transparent")
        adb_path_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(adb_path_frame, text="ADB Path:", text_color=self.colors['text_light'], font=get_font('label')).pack(side=tk.LEFT)
        self.config_panel.adb_path_var = tk.StringVar(value=cfg.get('adb_config', {}).get('adb_path', 'adb'))
        ctk.CTkEntry(adb_path_frame, textvariable=self.config_panel.adb_path_var, width=200, corner_radius=8, font=get_font('input')).pack(side=tk.RIGHT)
        
        # Screenshot Timeout
        timeout_frame = ctk.CTkFrame(adb_frame, fg_color="transparent")
        timeout_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(timeout_frame, text="Screenshot Timeout:", text_color=self.colors['text_light'], font=get_font('label')).pack(side=tk.LEFT)
        self.config_panel.screenshot_timeout_var = tk.IntVar(value=cfg.get('adb_config', {}).get('screenshot_timeout', 5))
        ctk.CTkEntry(timeout_frame, textvariable=self.config_panel.screenshot_timeout_var, width=100, corner_radius=8, font=get_font('input')).pack(side=tk.RIGHT)
        
        # Input Delay
        delay_frame = ctk.CTkFrame(adb_frame, fg_color="transparent")
        delay_frame.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(delay_frame, text="Input Delay:", text_color=self.colors['text_light'], font=get_font('label')).pack(side=tk.LEFT)
        self.config_panel.input_delay_var = tk.DoubleVar(value=cfg.get('adb_config', {}).get('input_delay', 0.5))
        ctk.CTkEntry(delay_frame, textvariable=self.config_panel.input_delay_var, width=100, corner_radius=8, font=get_font('input')).pack(side=tk.RIGHT)
        
        # Connection Timeout
        conn_frame = ctk.CTkFrame(adb_frame, fg_color="transparent")
        conn_frame.pack(fill=tk.X, padx=15, pady=(5, 15))
        ctk.CTkLabel(conn_frame, text="Connection Timeout:", text_color=self.colors['text_light'], font=get_font('label')).pack(side=tk.LEFT)
        self.config_panel.connection_timeout_var = tk.IntVar(value=cfg.get('adb_config', {}).get('connection_timeout', 10))
        ctk.CTkEntry(conn_frame, textvariable=self.config_panel.connection_timeout_var, width=100, corner_radius=8, font=get_font('input')).pack(side=tk.RIGHT)

        # Capture Method Section
        capture_frame = ctk.CTkFrame(main_scroll, fg_color=self.colors['bg_light'], corner_radius=10)
        capture_frame.pack(fill=tk.X, pady=10, padx=10)

        ctk.CTkLabel(capture_frame, text="Screenshot Capture", font=get_font('section_title'), text_color=self.colors['text_light']).pack(pady=(15, 10))

        # Method selector
        method_row = ctk.CTkFrame(capture_frame, fg_color="transparent")
        method_row.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(method_row, text="Method:", text_color=self.colors['text_light'], font=get_font('label')).pack(side=tk.LEFT)
        self.config_panel.capture_method_var = tk.StringVar(value=cfg.get('capture_method', 'adb'))
        ctk.CTkOptionMenu(method_row, values=['adb', 'nemu_ipc'], variable=self.config_panel.capture_method_var,
                          fg_color=self.colors['accent_blue'], corner_radius=8,
                          button_color=self.colors['accent_blue'],
                          button_hover_color=self.colors['accent_green'],
                          font=get_font('dropdown'),
                          command=lambda _: self.config_panel.toggle_nemu_settings()).pack(side=tk.RIGHT)

        # Nemu IPC settings (hidden unless selected)
        self.config_panel.nemu_settings_frame = ctk.CTkFrame(capture_frame, fg_color=self.colors['bg_light'], corner_radius=10)
        nemu_cfg = cfg.get('nemu_ipc_config', {})
        # Fields
        nemu_folder_row = ctk.CTkFrame(self.config_panel.nemu_settings_frame, fg_color="transparent")
        nemu_folder_row.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(nemu_folder_row, text="MuMu/Nemu Folder:", text_color=self.colors['text_light'], font=get_font('label')).pack(side=tk.LEFT)
        self.config_panel.nemu_folder_var = tk.StringVar(value=nemu_cfg.get('nemu_folder', 'J:\\MuMuPlayerGlobal'))
        ctk.CTkEntry(nemu_folder_row, textvariable=self.config_panel.nemu_folder_var, width=320, corner_radius=8, font=get_font('input')).pack(side=tk.RIGHT)

        instance_row = ctk.CTkFrame(self.config_panel.nemu_settings_frame, fg_color="transparent")
        instance_row.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(instance_row, text="Instance ID:", text_color=self.colors['text_light'], font=get_font('label')).pack(side=tk.LEFT)
        self.config_panel.nemu_instance_var = tk.IntVar(value=nemu_cfg.get('instance_id', 2))
        ctk.CTkEntry(instance_row, textvariable=self.config_panel.nemu_instance_var, width=100, corner_radius=8, font=get_font('input')).pack(side=tk.RIGHT)

        display_row = ctk.CTkFrame(self.config_panel.nemu_settings_frame, fg_color="transparent")
        display_row.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkLabel(display_row, text="Display ID:", text_color=self.colors['text_light'], font=get_font('label')).pack(side=tk.LEFT)
        self.config_panel.nemu_display_var = tk.IntVar(value=nemu_cfg.get('display_id', 0))
        ctk.CTkEntry(display_row, textvariable=self.config_panel.nemu_display_var, width=100, corner_radius=8, font=get_font('input')).pack(side=tk.RIGHT)

        timeout_row = ctk.CTkFrame(self.config_panel.nemu_settings_frame, fg_color="transparent")
        timeout_row.pack(fill=tk.X, padx=15, pady=(5, 15))
        ctk.CTkLabel(timeout_row, text="Timeout (s):", text_color=self.colors['text_light'], font=get_font('label')).pack(side=tk.LEFT)
        self.config_panel.nemu_timeout_var = tk.DoubleVar(value=nemu_cfg.get('timeout', 1.0))
        ctk.CTkEntry(timeout_row, textvariable=self.config_panel.nemu_timeout_var, width=100, corner_radius=8, font=get_font('input')).pack(side=tk.RIGHT)

        # Initial visibility
        self.config_panel.toggle_nemu_settings()
        
        # Save button for Main tab (place at bottom)
        save_btn = ctk.CTkButton(main_scroll, text="Save Settings", 
                                command=self.config_panel.save_config,
                                fg_color=self.colors['accent_green'], corner_radius=8, height=35,
                                font=get_font('button'))
        save_btn.pack(pady=20)
