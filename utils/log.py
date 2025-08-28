import json
import os
import sys

# Load DEBUG_MODE once; fallback to False on error
try:
    with open("config.json", "r", encoding="utf-8") as _f:
        _cfg = json.load(_f)
        DEBUG_MODE = _cfg.get("debug_mode", False)
except Exception:
    DEBUG_MODE = False

def debug_print(message):
    if DEBUG_MODE:
        try:
            print(message)
        except UnicodeEncodeError:
            try:
                safe_message = str(message).encode('ascii', errors='replace').decode('ascii')
                print(safe_message)
            except Exception:
                print("[DEBUG] (encoding error)")

def safe_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        try:
            safe_message = str(message).encode('ascii', errors='replace').decode('ascii')
            print(safe_message)
        except Exception:
            print("Error: Could not display message due to encoding issues")


