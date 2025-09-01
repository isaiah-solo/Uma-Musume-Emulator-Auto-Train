import time
import subprocess
import json
import sys
import logging
import os

# Fix Windows console encoding for Unicode support
if os.name == 'nt':  # Windows
    try:
        # Set console to UTF-8 mode
        os.system('chcp 65001 > nul')
        # Also try to set stdout encoding
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from utils.screenshot import get_screen_size, load_config
from utils.device import run_adb
from core.execute import career_lobby

# Configure logging for real-time output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

def log_and_flush(message, level="INFO"):
    """Log message and flush immediately for real-time GUI capture"""
    print(f"[{level}] {message}")
    sys.stdout.flush()

def check_adb_connection():
    """Check if ADB is connected to a device"""
    config = load_config()
    adb_path = config.get('adb_path', 'adb')
    device_address = config.get('device_address', '')
    
    try:
        result = subprocess.run([adb_path, 'devices'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')[1:]  # Skip header line
        connected_devices = [line for line in lines if line.strip() and '\tdevice' in line]
        
        if not connected_devices:
            log_and_flush("No ADB devices connected!", "WARNING")
            # Try to auto-connect using device_address from config.json
            if device_address:
                log_and_flush("Attempting to connect to: " + device_address, "INFO")
                try:
                    connect_result = subprocess.run(
                        [adb_path, 'connect', device_address], capture_output=True, text=True, check=False
                    )
                    output = (connect_result.stdout or '').strip()
                    error_output = (connect_result.stderr or '').strip()
                    if output:
                        log_and_flush(output, "INFO")
                    if error_output and not output:
                        log_and_flush(error_output, "ERROR")

                    # Re-check devices after attempting to connect
                    result = subprocess.run([adb_path, 'devices'], capture_output=True, text=True, check=True)
                    lines = result.stdout.strip().split('\n')[1:]
                    connected_devices = [line for line in lines if line.strip() and '\tdevice' in line]
                    if not connected_devices:
                        log_and_flush("Failed to connect to device at: " + device_address, "ERROR")
                        log_and_flush("Please ensure the emulator/device is running and USB debugging is enabled.", "ERROR")
                        return False
                except Exception as e:
                    log_and_flush("Error during adb connect: " + str(e), "ERROR")
                    return False
            else:
                log_and_flush("No device address configured in config.json (adb_config.device_address).", "ERROR")
                log_and_flush("Please connect your Android device or emulator and enable USB debugging.", "ERROR")
                return False
        
        log_and_flush("Connected devices: " + str(len(connected_devices)), "SUCCESS")
        for device in connected_devices:
            log_and_flush("  " + device.split('\t')[0], "INFO")
        return True
        
    except subprocess.CalledProcessError:
        log_and_flush("ADB not found! Please install Android SDK and add ADB to your PATH.", "ERROR")
        return False
    except FileNotFoundError:
        log_and_flush("ADB not found! Please install Android SDK and add ADB to your PATH.", "ERROR")
        return False

def get_device_info():
    """Get device information"""
    try:
        # Get screen size
        width, height = get_screen_size()
        log_and_flush("Device screen size: " + str(width) + "x" + str(height), "INFO")
        
        # Get device model
        model = run_adb(['shell', 'getprop', 'ro.product.model'])
        if model:
            log_and_flush("Device model: " + model, "INFO")
        
        # Get Android version
        version = run_adb(['shell', 'getprop', 'ro.build.version.release'])
        if version:
            log_and_flush("Android version: " + version, "INFO")
            
        return True
        
    except Exception as e:
        log_and_flush("Error getting device info: " + str(e), "ERROR")
        return False

def main():
    log_and_flush("Uma Auto - ADB Version!", "INFO")
    log_and_flush("=" * 40, "INFO")
    
    # Check ADB connection
    if not check_adb_connection():
        return
    
    # Get device information
    if not get_device_info():
        return
    
    log_and_flush("", "INFO")
    log_and_flush("Starting automation...", "SUCCESS")
    log_and_flush("Make sure Umamusume is running on your device!", "INFO")
    log_and_flush("Press Ctrl+C to stop the automation.", "INFO")
    log_and_flush("=" * 40, "INFO")
    
    try:
        career_lobby()
    except KeyboardInterrupt:
        log_and_flush("", "INFO")
        log_and_flush("Automation stopped by user.", "WARNING")
    except Exception as e:
        log_and_flush("", "INFO")
        log_and_flush("Automation error: " + str(e), "ERROR")

if __name__ == "__main__":
    main() 