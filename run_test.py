#!/usr/bin/env python3
"""
Simple test runner for the Complete Career OCR test script.
This script provides an easy way to run the test and handle any import errors.
"""

import sys
import os

def main():
    """Run the Complete Career OCR test"""
    try:
        print("Starting Complete Career OCR test...")
        
        # Import and run the test
        from test_complete_career_ocr import main as run_test
        run_test()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Test execution error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

