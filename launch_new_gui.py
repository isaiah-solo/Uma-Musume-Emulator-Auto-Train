#!/usr/bin/env python3
"""
Uma Musume Auto-Train Bot - New GUI Launcher (Root Directory)

This script launches the redesigned GUI application from the root directory.
Simply run this file to start the new dark-themed GUI.

Usage:
    python launch_new_gui.py
    or
    python3 launch_new_gui.py
"""

import sys
import os

def main():
    """Main launcher function"""
    print("Uma Musume Auto-Train Bot - New GUI Launcher")
    print("=" * 50)
    
    # Check if GUI directory exists
    if not os.path.exists('gui'):
        print("Error: GUI directory not found!")
        print("Please ensure you're running this from the correct directory.")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Add GUI directory to Python path
    gui_path = os.path.join(os.getcwd(), 'gui')
    sys.path.insert(0, gui_path)
    
    # Check configuration files before starting GUI
    try:
        from gui.config_checker import check_configs_from_gui
        print("Checking configuration files...")
        config_summary = check_configs_from_gui()
        
        if config_summary['created']:
            print(f"✓ Created {len(config_summary['created'])} new configuration files")
        if config_summary['errors']:
            print(f"⚠ {len(config_summary['errors'])} errors occurred during config creation")
        
    except Exception as e:
        print(f"Warning: Could not check configuration files: {e}")
        print("GUI will continue without automatic config file creation.")
    
    try:
        # Import and run the GUI
        from launch_gui import main as gui_main
        gui_main()
        
    except Exception as e:
        print(f"Error starting GUI: {e}")
        print("\nPlease check the error message above and try again.")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
