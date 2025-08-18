#!/usr/bin/env python3
"""
Demo script for skill recognition functionality.

This script demonstrates how to use the skill_up.png recognition system
with real screenshots from an Android device connected via ADB.
"""

import sys
import os
import time
from utils.skill_recognizer import recognize_skill_up_locations, test_skill_listing, scan_all_skills_with_scroll

def check_prerequisites():
    """Check if all prerequisites are met."""
    print("Checking prerequisites...")
    
    # Check if skill_up.png exists
    template_path = "assets/buttons/skill_up.png"
    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return False
    else:
        print(f"✅ Template file found: {template_path}")
    
    # Check if ADB is working
    try:
        from utils.adb_screenshot import run_adb_command
        result = run_adb_command(['devices'])
        if result and 'device' in result:
            print("✅ ADB connection working")
            print(f"   Device info: {result}")
        else:
            print("❌ No ADB devices connected")
            print("   Please connect your Android device and enable USB debugging")
            return False
    except Exception as e:
        print(f"❌ ADB error: {e}")
        return False
    
    # Check if debug_images directory can be created
    try:
        os.makedirs("debug_images", exist_ok=True)
        print("✅ Debug images directory ready")
    except Exception as e:
        print(f"❌ Cannot create debug_images directory: {e}")
        return False
    
    return True

def run_single_detection(confidence=0.9, filter_dark=True, brightness_threshold=150):
    """Run a single skill detection with given confidence."""
    print(f"\n🔍 Running skill detection (confidence: {confidence}, filter_dark: {filter_dark})...")
    print("-" * 50)
    
    start_time = time.time()
    result = recognize_skill_up_locations(
        confidence=confidence, 
        debug_output=True,
        filter_dark_buttons=filter_dark,
        brightness_threshold=brightness_threshold
    )
    end_time = time.time()
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"⏱️  Detection time: {end_time - start_time:.2f} seconds")
    print(f"📊 Results:")
    
    if filter_dark:
        print(f"   • Available buttons found: {result['count']}")
        print(f"   • Total detected (before filtering): {result.get('deduplicated_matches', 'N/A')}")
        print(f"   • Dark buttons filtered out: {result.get('dark_buttons_filtered', 0)}")
        print(f"   • Raw matches (before de-duplication): {result.get('raw_matches', 'N/A')}")
        print(f"   • Brightness threshold used: {result.get('brightness_threshold_used', 'N/A')}")
    else:
        print(f"   • Total matches found: {result['count']}")
        print(f"   • Raw matches (before de-duplication): {result.get('raw_matches', 'N/A')}")
    
    print(f"   • Confidence threshold used: {result['confidence_used']}")
    print(f"   • Overlap threshold used: {result.get('overlap_threshold_used', 'N/A')}")
    
    if result['locations']:
        print(f"   • Available button locations:" if filter_dark else "   • Detected locations:")
        for i, (x, y, w, h) in enumerate(result['locations']):
            print(f"     {i+1}. Position: ({x}, {y}) Size: {w}x{h}")
    else:
        print(f"   • No available skill_up icons detected" if filter_dark else "   • No skill_up icons detected")
    
    # Show brightness analysis if available
    if filter_dark and 'brightness_info' in result:
        print(f"   • Brightness analysis:")
        for info in result['brightness_info']:
            x, y, w, h = info['location']
            status = "✓ Available" if info['available'] else "✗ Dark"
            print(f"     ({x}, {y}): {info['brightness']:.1f} - {status}")
    
    if result['debug_image_path']:
        print(f"🖼️  Debug image saved: {result['debug_image_path']}")
        print(f"   Open this image to see bounding boxes around detected skill_up icons")
    
    return True

def run_optimized_detection():
    """Run detection with Auto Skill Purchase optimized settings."""
    print(f"\n📈 Auto Skill Purchase Optimized Detection")
    print("=" * 60)
    print("Using confidence: 0.9, brightness threshold: 150, with skill info extraction")
    
    result = recognize_skill_up_locations(
        confidence=0.9, 
        debug_output=True,
        filter_dark_buttons=True,
        brightness_threshold=150,
        extract_skills=True
    )
    
    if 'error' not in result:
        print(f"\n📊 Results:")
        print(f"  Available skill buttons: {result['count']}")
        print(f"  Raw matches: {result.get('raw_matches', 0)}")
        print(f"  Dark buttons filtered: {result.get('dark_buttons_filtered', 0)}")
        
        if result.get('skills'):
            print(f"\n📋 Detected Skills:")
            for i, skill in enumerate(result['skills'], 1):
                x, y, w, h = skill['location']
                print(f"    {i}. {skill['name']} - Price: {skill['price']} - Button: ({x}, {y})")
        elif result['locations']:
            print("  Available button positions:")
            for i, (x, y, w, h) in enumerate(result['locations']):
                print(f"    {i+1}. ({x}, {y}) - {w}x{h}")
        
        if result['debug_image_path']:
            print(f"  Debug image: {result['debug_image_path']}")
    else:
        print(f"  Error: {result['error']}")
    
    print(f"\n💡 These settings are optimized for reliable Auto Skill Purchase detection")

def interactive_demo():
    """Run interactive demo allowing user to test different settings."""
    print(f"\n🎮 Interactive Demo Mode")
    print("=" * 40)
    
    while True:
        print(f"\nOptions:")
        print(f"1. Auto Skill Purchase optimized detection")
        print(f"2. List all skills with prices (OCR)")
        print(f"3. Scan ALL skills with scrolling")
        print(f"4. Single detection (custom settings)")
        print(f"5. Compare filtered vs unfiltered")
        print(f"6. Brightness threshold tuning")
        print(f"7. Continuous monitoring")
        print(f"8. Exit")
        
        try:
            choice = input("\nEnter your choice (1-8): ").strip()
            
            if choice == '1':
                run_optimized_detection()
                
            elif choice == '2':
                print(f"\n📋 Running comprehensive skill listing with OCR...")
                test_skill_listing()
                
            elif choice == '3':
                print(f"\n🔄 Scanning ALL skills with scrolling...")
                print("This will scroll through the entire skill list until duplicates are found.")
                print("⚠️  Make sure you're on the skill list screen!")
                
                confirm = input("Continue? (y/n): ").lower().startswith('y')
                if confirm:
                    result = scan_all_skills_with_scroll()
                    
                    if 'error' not in result:
                        print(f"\n📊 COMPLETE SKILL INVENTORY:")
                        print("=" * 70)
                        for i, skill in enumerate(result['all_skills'], 1):
                            x, y, w, h = skill['location']
                            print(f"{i:3d}. {skill['name']:<30} | Price: {skill['price']:<6} | Pos: ({x}, {y})")
                        
                        print("=" * 70)
                        print(f"Total unique skills found: {result['total_unique_skills']}")
                        print(f"Scrolls performed: {result['scrolls_performed']}")
                        if result['duplicate_found']:
                            print(f"Stopped at duplicate: {result['duplicate_found']}")
                    else:
                        print(f"Error: {result['error']}")
                else:
                    print("Scan cancelled.")
                
            elif choice == '4':
                print("\n🔧 Custom settings:")
                confidence = float(input("Enter confidence (0.1-1.0): "))
                filter_dark = input("Filter dark buttons? (y/n): ").lower().startswith('y')
                extract_skill_data = input("Extract skill info with OCR? (y/n): ").lower().startswith('y')
                brightness_threshold = 150
                if filter_dark:
                    brightness_threshold = int(input("Enter brightness threshold (0-255): "))
                
                if 0.1 <= confidence <= 1.0:
                    result = recognize_skill_up_locations(
                        confidence=confidence,
                        debug_output=True,
                        filter_dark_buttons=filter_dark,
                        brightness_threshold=brightness_threshold,
                        extract_skills=extract_skill_data
                    )
                    
                    if 'error' not in result:
                        print(f"\nFound {result['count']} available skill buttons")
                        if result.get('skills'):
                            for i, skill in enumerate(result['skills'], 1):
                                print(f"  {i}. {skill['name']} - Price: {skill['price']}")
                    else:
                        print(f"Error: {result['error']}")
                else:
                    print("❌ Confidence must be between 0.1 and 1.0")
                    
            elif choice == '5':
                print(f"\n⚖️  Comparing filtered vs unfiltered detection:")
                print("\n1. Without dark button filtering:")
                run_single_detection(confidence=0.9, filter_dark=False, brightness_threshold=150)
                print("\n2. With dark button filtering (Auto Skill Purchase optimized):")
                run_single_detection(confidence=0.9, filter_dark=True, brightness_threshold=150)
                
            elif choice == '6':
                print(f"\n🔆 Brightness threshold tuning:")
                thresholds = [100, 120, 150, 170, 190]
                for threshold in thresholds:
                    print(f"\nTesting brightness threshold: {threshold}")
                    result = recognize_skill_up_locations(
                        confidence=0.9, 
                        debug_output=False,
                        filter_dark_buttons=True,
                        brightness_threshold=threshold,
                        extract_skills=False
                    )
                    if 'error' not in result:
                        print(f"  Available buttons: {result['count']}")
                        print(f"  Dark buttons filtered: {result.get('dark_buttons_filtered', 0)}")
                
            elif choice == '7':
                print(f"\n🔄 Continuous monitoring mode (Auto Skill Purchase settings)")
                print("Press Ctrl+C to stop...")
                try:
                    while True:
                        result = recognize_skill_up_locations(
                            confidence=0.9, 
                            debug_output=False,
                            filter_dark_buttons=True,
                            brightness_threshold=150,
                            extract_skills=False
                        )
                        if 'error' not in result:
                            available = result['count']
                            filtered = result.get('dark_buttons_filtered', 0)
                            print(f"[{time.strftime('%H:%M:%S')}] Available: {available}, Dark: {filtered}")
                        else:
                            print(f"[{time.strftime('%H:%M:%S')}] Error: {result['error']}")
                        time.sleep(2)
                except KeyboardInterrupt:
                    print("\n⏹️  Monitoring stopped")
                    
            elif choice == '8':
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-8.")
                
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

def main():
    """Main demo function."""
    print("🎯 Uma Musume Skill Recognition Demo")
    print("=" * 50)
    print("This demo will test the skill_up.png recognition system")
    print("on your connected Android device.")
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above and try again.")
        return 1
    
    print("\n✅ All prerequisites met!")
    
    # Ask user what they want to do
    print(f"\nWhat would you like to do?")
    print(f"1. Quick test (Auto Skill Purchase optimized)")
    print(f"2. List all skills with prices (OCR)")
    print(f"3. Scan ALL skills with scrolling")
    print(f"4. Interactive demo")
    print(f"5. Run comprehensive test suite")
    
    try:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            print(f"\n🚀 Running Auto Skill Purchase optimized test...")
            run_optimized_detection()
            
        elif choice == '2':
            print(f"\n📋 Running skill listing with OCR...")
            test_skill_listing()
            
        elif choice == '3':
            print(f"\n🔄 Scanning ALL skills with scrolling...")
            print("This will scroll through the entire skill list until duplicates are found.")
            print("⚠️  Make sure you're on the skill list screen!")
            
            confirm = input("Continue? (y/n): ").lower().startswith('y')
            if confirm:
                result = scan_all_skills_with_scroll()
                
                if 'error' not in result:
                    print(f"\n📊 COMPLETE SKILL INVENTORY:")
                    print("=" * 70)
                    for i, skill in enumerate(result['all_skills'], 1):
                        print(f"{i:3d}. {skill['name']:<30} | Price: {skill['price']:<6}")
                    
                    print("=" * 70)
                    print(f"Total unique skills found: {result['total_unique_skills']}")
                    print(f"Scrolls performed: {result['scrolls_performed']}")
                    if result['duplicate_found']:
                        print(f"Stopped at duplicate: {result['duplicate_found']}")
                else:
                    print(f"Error: {result['error']}")
            else:
                print("Scan cancelled.")
            
        elif choice == '4':
            interactive_demo()
            
        elif choice == '5':
            print(f"\n🧪 Running comprehensive test suite...")
            print("This will run the full test suite including unit tests.")
            os.system("python test_skill_recognition.py --manual")
            
        else:
            print("❌ Invalid choice. Running optimized test instead...")
            run_optimized_detection()
            
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user.")
        return 0
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print(f"\n✅ Demo completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())