import re
import time
import json

from PIL import Image, ImageEnhance
from utils.adb_screenshot import capture_region, enhanced_screenshot, enhanced_screenshot_for_failure, enhanced_screenshot_for_year, take_screenshot
from core.ocr import extract_text, extract_number, extract_turn_number, extract_mood_text, extract_failure_text, extract_failure_text_with_confidence
from utils.adb_recognizer import match_template
from utils.skill_auto_purchase import execute_skill_purchases, click_image_button
from utils.skill_recognizer import scan_all_skills_with_scroll
from utils.skill_purchase_optimizer import load_skill_config, create_purchase_plan
from test_integrated_skill_purchase import extract_skill_points, filter_affordable_skills

from utils.constants_phone import (
    SUPPORT_CARD_ICON_REGION, MOOD_REGION, TURN_REGION, FAILURE_REGION, YEAR_REGION, 
    MOOD_LIST, CRITERIA_REGION, SPD_REGION, STA_REGION, PWR_REGION, GUTS_REGION, WIT_REGION,
    SKILL_PTS_REGION, FAILURE_REGION_SPD, FAILURE_REGION_STA, FAILURE_REGION_PWR, FAILURE_REGION_GUTS, FAILURE_REGION_WIT
)

# Load config and check debug mode
with open("config.json", "r", encoding="utf-8") as config_file:
    config = json.load(config_file)
    DEBUG_MODE = config.get("debug_mode", False)

def debug_print(message):
    """Print debug message only if DEBUG_MODE is enabled"""
    if DEBUG_MODE:
        print(message)

# Get Stat
def stat_state():
    stat_regions = {
        "spd": SPD_REGION,
        "sta": STA_REGION,
        "pwr": PWR_REGION,
        "guts": GUTS_REGION,
        "wit": WIT_REGION
    }

    result = {}
    for stat, region in stat_regions.items():
        img = enhanced_screenshot(region)
        val = extract_number(img)
        digits = ''.join(filter(str.isdigit, val))
        result[stat] = int(digits) if digits.isdigit() else 0
    return result

# Check support card in each training
def check_support_card(threshold=0.85):
    SUPPORT_ICONS = {
        "spd": "assets/icons/support_card_type_spd.png",
        "sta": "assets/icons/support_card_type_sta.png",
        "pwr": "assets/icons/support_card_type_pwr.png",
        "guts": "assets/icons/support_card_type_guts.png",
        "wit": "assets/icons/support_card_type_wit.png",
        "friend": "assets/icons/support_card_type_friend.png"
    }

    count_result = {}

    # Take a screenshot for template matching
    screenshot = take_screenshot()
    
    # Save full screenshot for debugging only in debug mode
    if DEBUG_MODE:
        screenshot.save("debug_support_cards_screenshot.png")
        debug_print(f"[DEBUG] Saved full screenshot to debug_support_cards_screenshot.png")

    # Convert PIL region format (left, top, right, bottom) to OpenCV format (x, y, width, height)
    left, top, right, bottom = SUPPORT_CARD_ICON_REGION
    region_cv = (left, top, right - left, bottom - top)
    debug_print(f"[DEBUG] Searching in region: {region_cv} (PIL format: {SUPPORT_CARD_ICON_REGION})")
    
    # Crop and save the search region for debugging only in debug mode
    if DEBUG_MODE:
        search_region = screenshot.crop(SUPPORT_CARD_ICON_REGION)
        search_region.save("debug_support_cards_search_region.png")
        debug_print(f"[DEBUG] Saved search region to debug_support_cards_search_region.png")

    for key, icon_path in SUPPORT_ICONS.items():
        debug_print(f"\n[DEBUG] Testing {key.upper()} support card detection...")
        
        # Use single threshold for faster detection
        matches = match_template(screenshot, icon_path, 0.8, region_cv)
        filtered_matches = []
        
        if matches:
            # Efficient duplicate filtering
            for match in matches:
                x, y, w, h = match
                center_x, center_y = x + w//2, y + h//2
                
                # Check if this match is too close to existing matches
                is_duplicate = False
                for existing in filtered_matches:
                    ex, ey, ew, eh = existing
                    existing_center_x, existing_center_y = ex + ew//2, ey + eh//2
                    # If centers are within 30 pixels, consider it a duplicate
                    if abs(center_x - existing_center_x) < 30 and abs(center_y - existing_center_y) < 30:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    filtered_matches.append(match)
            
            debug_print(f"[DEBUG] Found {len(filtered_matches)} {key.upper()} support cards (filtered from {len(matches)})")
            
            # Show coordinates of each match
            for i, match in enumerate(filtered_matches):
                x, y, w, h = match
                center_x, center_y = x + w//2, y + h//2
                debug_print(f"[DEBUG]   {key.upper()} match {i+1}: center=({center_x}, {center_y}), bbox=({x}, {y}, {w}, {h})")
        
        # Skip expensive image annotation and only save debug images when DEBUG_MODE is true
        if not filtered_matches:
            debug_print(f"[DEBUG] No {key.upper()} support cards found")
        
        count_result[key] = len(filtered_matches) if filtered_matches else 0
        
        # Debug output for each support card type
        if count_result[key] > 0:
            debug_print(f"[DEBUG] {key.upper()} support cards found: {count_result[key]}")

    return count_result

def check_failure(train_type):
    """
    Check failure rate for a specific training type using direct region OCR.
    Args:
        train_type (str): One of 'spd', 'sta', 'pwr', 'guts', 'wit'
    Returns:
        (rate, confidence)
    """
    debug_print(f"[DEBUG] ===== STARTING FAILURE DETECTION for {train_type.upper()} =====")
    from utils.constants_phone import FAILURE_REGION_SPD, FAILURE_REGION_STA, FAILURE_REGION_PWR, FAILURE_REGION_GUTS, FAILURE_REGION_WIT
    from utils.adb_screenshot import enhanced_screenshot, take_screenshot
    import numpy as np
    import pytesseract
    import re
    from PIL import ImageEnhance

    region_map = {
        'spd': FAILURE_REGION_SPD,
        'sta': FAILURE_REGION_STA,
        'pwr': FAILURE_REGION_PWR,
        'guts': FAILURE_REGION_GUTS,
        'wit': FAILURE_REGION_WIT
    }
    region = region_map[train_type]
    percentage_patterns = [
        r"(\d{1,3})\s*%",  # "29%", "29 %" - most reliable
        r"%\s*(\d{1,3})",  # "% 29" - reversed format
        r"(\d{1,3})",      # Just the number - fallback
    ]
    # Step 1: Try white-specialized OCR 3 times
    for attempt in range(3):
        debug_print(f"[DEBUG] White OCR attempt {attempt+1}/3 for {train_type.upper()}")
        img = enhanced_screenshot(region)
        if DEBUG_MODE:
            img.save(f"debug_failure_{train_type}_white_attempt_{attempt+1}.png")
        
        # Get OCR data with confidence
        ocr_data = pytesseract.image_to_data(np.array(img), config='--oem 3 --psm 6', output_type=pytesseract.Output.DICT)
        text = pytesseract.image_to_string(np.array(img), config='--oem 3 --psm 6').strip()
        debug_print(f"[DEBUG] White OCR result: '{text}'")
        
        # Calculate average confidence from OCR data
        confidences = [conf for conf in ocr_data['conf'] if conf != -1]
        avg_confidence = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.0
        
        for pattern in percentage_patterns:
            match = re.search(pattern, text)
            if match:
                rate = int(match.group(1))
                if 0 <= rate <= 100:
                    debug_print(f"[DEBUG] Found percentage: {rate}% (white) confidence: {avg_confidence:.2f} for {train_type.upper()}")
                    if avg_confidence >= 0.7:
                        debug_print(f"[DEBUG] Confidence {avg_confidence:.2f} meets minimum 0.7, accepting result")
                        return (rate, avg_confidence)
                    else:
                        debug_print(f"[DEBUG] Confidence {avg_confidence:.2f} below minimum 0.7, continuing to retry")
        if attempt < 2:
            debug_print("[DEBUG] No valid percentage found, retrying...")
            time.sleep(0.1)
    # Step 2: Try yellow threshold OCR 3 times
    for attempt in range(3):
        debug_print(f"[DEBUG] Yellow OCR attempt {attempt+1}/3 for {train_type.upper()}")
        raw_img = take_screenshot().crop(region)
        raw_img = raw_img.resize((raw_img.width * 2, raw_img.height * 2), Image.BICUBIC)
        raw_img = raw_img.convert("RGB")
        raw_np = np.array(raw_img)
        yellow_mask = (
            (raw_np[:, :, 0] > 180) &  # High red
            (raw_np[:, :, 1] > 120) &  # High green
            (raw_np[:, :, 2] < 80)     # Low blue
        )
        yellow_result = np.zeros_like(raw_np)
        yellow_result[yellow_mask] = [255, 255, 255]
        yellow_img = Image.fromarray(yellow_result).convert("L")
        yellow_img = ImageEnhance.Contrast(yellow_img).enhance(1.5)
        if DEBUG_MODE:
            yellow_img.save(f"debug_failure_{train_type}_yellow_attempt_{attempt+1}.png")
        
        # Get OCR data with confidence
        ocr_data = pytesseract.image_to_data(np.array(yellow_img), config='--oem 3 --psm 6', output_type=pytesseract.Output.DICT)
        text = pytesseract.image_to_string(np.array(yellow_img), config='--oem 3 --psm 6').strip()
        debug_print(f"[DEBUG] Yellow OCR result: '{text}'")
        
        # Calculate average confidence from OCR data
        confidences = [conf for conf in ocr_data['conf'] if conf != -1]
        avg_confidence = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.0
        
        for pattern in percentage_patterns:
            match = re.search(pattern, text)
            if match:
                rate = int(match.group(1))
                if 0 <= rate <= 100:
                    debug_print(f"[DEBUG] Found percentage: {rate}% (yellow) confidence: {avg_confidence:.2f} for {train_type.upper()}")
                    if avg_confidence >= 0.7:
                        debug_print(f"[DEBUG] Confidence {avg_confidence:.2f} meets minimum 0.7, accepting result")
                        return (rate, avg_confidence)
                    else:
                        debug_print(f"[DEBUG] Confidence {avg_confidence:.2f} below minimum 0.7, continuing to retry")
        if attempt < 2:
            debug_print("[DEBUG] No valid yellow percentage found, retrying...")
            time.sleep(0.1)
    debug_print(f"[DEBUG] No valid failure rate found for {train_type.upper()}, returning 100% (safe fallback)")
    return (100, 0.0)  # 100% failure rate when detection completely fails (prevents choosing unknown training)

def fuzzy_match_mood(text):
    """
    Perform fuzzy matching for mood detection using pattern-based approach.
    
    Args:
        text (str): The OCR text to match (should be uppercase)
    
    Returns:
        str: The matched mood or "UNKNOWN" if no match found
    """
    # First, try exact match
    if text in MOOD_LIST:
        return text
    
    # Clean common OCR errors
    cleaned_text = text.replace('0', 'O').replace('1', 'I').replace('5', 'S')
    
    # Fuzzy pattern matching with priority order (most restrictive first)
    # AWFUL patterns - check first since it's most likely to be misread
    if any(pattern in cleaned_text for pattern in ['AWF', 'AWFUL', 'AWFU', 'VAWF', 'WAWF']):
        debug_print(f"[DEBUG] AWFUL pattern match in: '{text}'")
        return "AWFUL"
    
    # GREAT patterns - check before GOOD to avoid conflicts
    if any(pattern in cleaned_text for pattern in ['GREAT', 'GREA', 'REAT', 'EA']):
        debug_print(f"[DEBUG] GREAT pattern match in: '{text}'")
        return "GREAT"
    
    # GOOD patterns
    if any(pattern in cleaned_text for pattern in ['GOOD', 'GOO', 'OOD', 'OO']):
        debug_print(f"[DEBUG] GOOD pattern match in: '{text}'")
        return "GOOD"
    
    # NORMAL patterns
    if any(pattern in cleaned_text for pattern in ['NORMAL', 'NORMA', 'ORMA', 'RMAL']):
        debug_print(f"[DEBUG] NORMAL pattern match in: '{text}'")
        return "NORMAL"
    
    # BAD patterns - check last since it's short and might false positive
    if any(pattern in cleaned_text for pattern in ['BAD']) and 'AWF' not in cleaned_text:
        debug_print(f"[DEBUG] BAD pattern match in: '{text}'")
        return "BAD"
    
    # Final fallback: check for partial substring matches
    for mood in MOOD_LIST:
        if mood in cleaned_text:
            debug_print(f"[DEBUG] Substring match: '{mood}' in '{text}'")
            return mood
    
    debug_print(f"[DEBUG] No fuzzy match found for: '{text}'")
    return "UNKNOWN"

def check_mood():
    # Try up to 3 times to detect mood
    max_attempts = 3
    
    for attempt in range(1, max_attempts + 1):
        mood_img = enhanced_screenshot(MOOD_REGION)
        mood_text = extract_mood_text(mood_img)
        
        # Apply fuzzy matching for mood detection
        mood_text_upper = mood_text.upper()
        detected_mood = fuzzy_match_mood(mood_text_upper)
        
        if detected_mood != "UNKNOWN":
            if mood_text != detected_mood:
                debug_print(f"[DEBUG] Fuzzy mood match: '{mood_text}' -> '{detected_mood}'")
            return detected_mood
        
        print(f"[WARNING] Mood not recognized on attempt {attempt}/{max_attempts}: {mood_text}")
        
        if attempt < max_attempts:
            print(f"{attempt}). Retrying...")
            time.sleep(0.5)
    
    print(f"[WARNING] Mood not recognized after {max_attempts} attempts: {mood_text}")
    return "UNKNOWN"

def check_turn():
    """Fast turn detection with minimal OCR"""
    debug_print("[DEBUG] Starting turn detection...")
    
    try:
        turn_img = enhanced_screenshot(TURN_REGION)
        debug_print(f"[DEBUG] Turn region screenshot taken: {TURN_REGION}")
        
        # Save the turn region image for debugging
        turn_img.save("debug_turn_region.png")
        debug_print("[DEBUG] Saved turn region image to debug_turn_region.png")
        
        # Apply additional enhancement for better digit recognition
        from PIL import ImageEnhance
        
        # Increase contrast more aggressively for turn detection
        contrast_enhancer = ImageEnhance.Contrast(turn_img)
        turn_img = contrast_enhancer.enhance(2.0)  # More aggressive contrast
        
        # Increase sharpness to make digits clearer
        sharpness_enhancer = ImageEnhance.Sharpness(turn_img)
        turn_img = sharpness_enhancer.enhance(2.0)
        
        # Save the enhanced version
        turn_img.save("debug_turn_enhanced.png")
        debug_print("[DEBUG] Saved enhanced turn image to debug_turn_enhanced.png")
        
        # Use the best method found in testing: basic processing + PSM 7
        import pytesseract
        import re
        
        # Apply basic grayscale processing (like test_turn_basic_grayscale)
        turn_img = turn_img.convert("L")
        turn_img = turn_img.resize((turn_img.width * 2, turn_img.height * 2), Image.BICUBIC)
        
        # Use PSM 7 (single line) which had 94% confidence in testing
        turn_text = pytesseract.image_to_string(turn_img, config='--oem 3 --psm 7').strip()
        debug_print(f"[DEBUG] Turn OCR raw result: '{turn_text}'")
        
        # Check for "Race Day" first (before character replacements that would corrupt it)
        if "Race Day" in turn_text or "RaceDay" in turn_text or "Race Da" in turn_text:
            debug_print(f"[DEBUG] Race Day detected: {turn_text}")
            return "Race Day"
        
        # Character replacements for common OCR errors (only for digit extraction)
        original_text = turn_text
        turn_text = turn_text.replace('y', '9').replace(']', '1').replace('l', '1').replace('I', '1').replace('o', '0').replace('O', '0').replace('/', '7')
        debug_print(f"[DEBUG] Turn OCR after character replacement: '{turn_text}' (was '{original_text}')")
        
        # Extract all consecutive digits (not just first digit)
        digit_match = re.search(r'(\d+)', turn_text)
        if digit_match:
            turn_num = int(digit_match.group(1))
            debug_print(f"[DEBUG] Turn OCR result: {turn_num} (from '{turn_text}')")
            return turn_num
        
        debug_print(f"[DEBUG] No digits found in turn text: '{turn_text}', defaulting to 1")
        return 1  # Default to turn 1
        
    except Exception as e:
        debug_print(f"[DEBUG] Turn detection failed with error: {e}")
        return 1

def check_current_year():
    """Fast year detection using regular screenshot"""
    year_img = enhanced_screenshot(YEAR_REGION)
    
    # Simple OCR with PSM 7 (single line text)
    import pytesseract
    text = pytesseract.image_to_string(year_img, config='--oem 3 --psm 7').strip()
    
    if text:
        debug_print(f"[DEBUG] Year OCR result: '{text}'")
        return text
    
    return "Unknown Year"

def check_criteria():
    """Fast criteria detection using single OCR attempt"""
    criteria_img = enhanced_screenshot(CRITERIA_REGION)
    
    # Use single, fast OCR configuration
    import pytesseract
    text = pytesseract.image_to_string(criteria_img, config='--oem 3 --psm 7').strip()
    
    if text:
        # Apply common OCR corrections
        text = text.replace("Entrycriteriamet", "Entry criteria met")
        text = text.replace("Entrycriteria", "Entry criteria")  
        text = text.replace("criteriamet", "criteria met")
        text = text.replace("Goalachieved", "Goal achieved")
        
        debug_print(f"[DEBUG] Criteria OCR result: '{text}'")
        return text
    
    # Single fallback attempt
    fallback_text = extract_text(criteria_img)
    if fallback_text.strip():
        debug_print(f"[DEBUG] Using fallback criteria OCR result: '{fallback_text}'")
        return fallback_text.strip()
    
    return "Unknown Criteria"

def check_skill_points():
    skill_img = enhanced_screenshot(SKILL_PTS_REGION)
    
    # Apply sharpening for better OCR accuracy
    sharpener = ImageEnhance.Sharpness(skill_img)
    skill_img_sharp = sharpener.enhance(2.5)  # Increase sharpness by 2.5x
    
    # Save debug images for skill points OCR troubleshooting
    skill_img.save("debug_skill_points_original.png")
    skill_img_sharp.save("debug_skill_points_sharpened.png")
    debug_print(f"[DEBUG] Saved original skill points image to debug_skill_points_original.png")
    debug_print(f"[DEBUG] Saved sharpened skill points image to debug_skill_points_sharpened.png")
    debug_print(f"[DEBUG] Skill points region: {SKILL_PTS_REGION}")
    
    # Use sharpened image for OCR
    skill_text = extract_number(skill_img_sharp)
    digits = ''.join(filter(str.isdigit, skill_text))
    
    debug_print(f"[DEBUG] Skill points OCR raw result: '{skill_text}'")
    debug_print(f"[DEBUG] Extracted digits: '{digits}'")
    
    result = int(digits) if digits.isdigit() else 0
    debug_print(f"[DEBUG] Final skill points value: {result}")
    
    return result

def check_skill_points_cap():
    """Check skill points and handle cap logic (same as PC version)"""
    import json
    import tkinter as tk
    from tkinter import messagebox
    
    # Load config
    try:
        with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
    except Exception as e:
        print(f"Error loading config: {e}")
        return True
    
    skill_point_cap = config.get("skill_point_cap", 9999)
    current_skill_points = check_skill_points()
    
    print(f"[INFO] Current skill points: {current_skill_points}, Cap: {skill_point_cap}")
    
    if current_skill_points > skill_point_cap:
        print(f"[WARNING] Skill points ({current_skill_points}) exceed cap ({skill_point_cap})")
        
        # Decide flow based on config
        skill_purchase_mode = config.get("skill_purchase", "manual").lower()
        if skill_purchase_mode == "auto":
            print("[INFO] Auto skill purchase enabled - starting automation")
            try:
                # 1) Enter skill screen
                entered = click_image_button("assets/buttons/skills_btn.png", "skills button", max_attempts=5)
                if not entered:
                    print("[ERROR] Could not find/open skills screen")
                    return True
                time.sleep(2.0)

                # 2) Scan skills and prepare purchase plan
                scan_result = scan_all_skills_with_scroll()
                if 'error' in scan_result:
                    print(f"[ERROR] Skill scanning failed: {scan_result['error']}")
                    # Attempt to go back anyway
                    click_image_button("assets/buttons/back_btn.png", "back button", max_attempts=5)
                    time.sleep(1.5)
                    return True
                all_skills = scan_result.get('all_skills', [])
                if not all_skills:
                    print("[WARNING] No skills detected on skill screen")
                    click_image_button("assets/buttons/back_btn.png", "back button", max_attempts=5)
                    time.sleep(1.5)
                    return True

                # Read current available skill points from the skill screen
                available_points = extract_skill_points()
                print(f"[INFO] Detected available skill points: {available_points}")

                # Build purchase plan from config priorities
                cfg = load_skill_config()
                purchase_plan = create_purchase_plan(all_skills, cfg)
                if not purchase_plan:
                    print("[INFO] No skills from priority list are currently available")
                    click_image_button("assets/buttons/back_btn.png", "back button", max_attempts=5)
                    time.sleep(1.5)
                    return True

                # Filter by budget if we have points
                final_plan = purchase_plan
                if isinstance(available_points, int) and available_points > 0:
                    affordable_skills, total_cost, remaining_points = filter_affordable_skills(purchase_plan, available_points)
                    final_plan = affordable_skills if affordable_skills else []
                    print(f"[INFO] Affordable skills: {len(final_plan)}; Total cost: {total_cost}; Remaining: {remaining_points}")

                if not final_plan:
                    print("[INFO] Nothing affordable to purchase at the moment")
                    click_image_button("assets/buttons/back_btn.png", "back button", max_attempts=5)
                    time.sleep(1.5)
                    return True

                # Execute automated purchases
                exec_result = execute_skill_purchases(final_plan)
                if not exec_result.get('success'):
                    print(f"[WARNING] Automated purchase completed with issues: {exec_result.get('error', 'unknown error')}")

                # 3) Return to lobby
                back = click_image_button("assets/buttons/back_btn.png", "back button", max_attempts=5)
                if not back:
                    print("[WARNING] Could not find back button after purchases; ensure you return to lobby manually")
                time.sleep(1.5)
            except Exception as e:
                print(f"[ERROR] Auto skill purchase failed: {e}")
            
            return True
        
        # Manual mode (original prompt)
        try:
            # Create a hidden root window
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            # Show the message box
            result = messagebox.showinfo(
                title="Skill Points Cap Reached",
                message=f"Skill points ({current_skill_points}) exceed the cap ({skill_point_cap}).\n\nYou can:\n• Use your skill points manually, then click OK\n• Click OK without spending (automation continues)\n\nNote: This check only happens on race days."
            )
            
            # Destroy the root window
            root.destroy()
            
            print("[INFO] Player acknowledged skill points cap warning")
            
        except Exception as e:
            print(f"[ERROR] Failed to show GUI popup: {e}")
            print("[INFO] Skill points cap reached - automation continuing")
        
        return True
    
    return True 