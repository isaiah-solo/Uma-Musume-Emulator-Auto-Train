#!/usr/bin/env python3
"""
Font Audit Script for Uma Musume Auto-Train Bot GUI

This script scans GUI files to find UI elements that might be using default fonts
instead of the centralized font system.
"""

import os
import re
from pathlib import Path

def scan_file_for_default_fonts(filepath):
    """Scan a file for UI elements that might be using default fonts"""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Check for CTk elements without font specifications
            patterns = [
                # Labels without fonts
                (r'ctk\.CTkLabel\([^)]*\)(?!.*font=)', 'CTkLabel without font'),
                # Buttons without fonts  
                (r'ctk\.CTkButton\([^)]*\)(?!.*font=)', 'CTkButton without font'),
                # Option menus without fonts
                (r'ctk\.CTkOptionMenu\([^)]*\)(?!.*font=)', 'CTkOptionMenu without font'),
                # Entries without fonts
                (r'ctk\.CTkEntry\([^)]*\)(?!.*font=)', 'CTkEntry without font'),
                # Checkboxes without fonts
                (r'ctk\.CTkCheckBox\([^)]*\)(?!.*font=)', 'CTkCheckBox without font'),
                # ComboBox without fonts
                (r'ctk\.CTkComboBox\([^)]*\)(?!.*font=)', 'CTkComboBox without font'),
            ]
            
            for pattern, description in patterns:
                if re.search(pattern, line_stripped):
                    # Skip if line already contains get_font() call
                    if 'get_font(' not in line_stripped:
                        issues.append({
                            'file': filepath,
                            'line': i,
                            'content': line_stripped,
                            'issue': description
                        })
    
    except Exception as e:
        print(f"Error scanning {filepath}: {e}")
    
    return issues

def main():
    """Main function to scan all GUI files"""
    gui_dir = Path(__file__).parent
    issues = []
    
    # Scan main GUI files
    files_to_scan = [
        gui_dir / 'config_panel.py',
        gui_dir / 'log_panel.py', 
        gui_dir / 'status_panel.py',
        gui_dir / 'main_window.py',
        gui_dir / 'font_config_editor.py'
    ]
    
    # Also scan config folder
    config_dir = gui_dir / 'config'
    if config_dir.exists():
        for py_file in config_dir.glob('*.py'):
            if py_file.name != '__init__.py':
                files_to_scan.append(py_file)
    
    print("🔍 Scanning GUI files for default font usage...\n")
    
    for filepath in files_to_scan:
        if filepath.exists():
            file_issues = scan_file_for_default_fonts(filepath)
            issues.extend(file_issues)
    
    if issues:
        print(f"⚠️  Found {len(issues)} potential font issues:\n")
        
        current_file = None
        for issue in issues:
            if issue['file'] != current_file:
                current_file = issue['file']
                print(f"\n📄 {os.path.relpath(current_file)}:")
            
            print(f"  Line {issue['line']:3d}: {issue['issue']}")
            print(f"           {issue['content'][:80]}{'...' if len(issue['content']) > 80 else ''}")
        
        print(f"\n💡 To fix these issues:")
        print("   1. Add font=get_font('appropriate_font_type') to each element")
        print("   2. Common font types: 'label', 'button', 'input', 'dropdown'")
        print("   3. Make sure get_font is imported at the top of the file")
        
    else:
        print("✅ No font issues found! All UI elements appear to use the centralized font system.")
    
    print(f"\n📊 Scanned {len(files_to_scan)} files")

if __name__ == '__main__':
    main()
