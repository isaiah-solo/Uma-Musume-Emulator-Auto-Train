import re
import time
import json
import os

from PIL import Image, ImageEnhance
from utils.adb_screenshot import capture_region, enhanced_screenshot, enhanced_screenshot_for_failure, enhanced_screenshot_for_year, take_screenshot
from core.ocr import extract_text, extract_number, extract_turn_number, extract_mood_text, extract_failure_text, extract_failure_text_with_confidence
from utils.adb_recognizer import match_template
from core.skill_auto_purchase import execute_skill_purchases, click_image_button, extract_skill_points
from core.skill_recognizer import scan_all_skills_with_scroll
from core.skill_purchase_optimizer import load_skill_config, create_purchase_plan, filter_affordable_skills

from utils.constants_phone import (
    SUPPORT_CARD_ICON_REGION, MOOD_REGION, TURN_REGION, FAILURE_REGION, YEAR_REGION, 
    MOOD_LIST, CRITERIA_REGION, SPD_REGION, STA_REGION, PWR_REGION, GUTS_REGION, WIT_REGION,
    SKILL_PTS_REGION, FAILURE_REGION_SPD, FAILURE_REGION_STA, FAILURE_REGION_PWR, FAILURE_REGION_GUTS, FAILURE_REGION_WIT
)

# Load config and check debug mode
with open("config.json", "r", encoding="utf-8") as config_file:
    config = json.load(config_file)
    DEBUG_MODE = config.get("debug_mode", False)

from utils.log import debug_print
from utils.template_matching import deduplicated_matches

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
    """Enhanced criteria detection"""
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
    else:
        # Single fallback attempt
        fallback_text = extract_text(criteria_img)
        if fallback_text.strip():
            debug_print(f"[DEBUG] Using fallback criteria OCR result: '{fallback_text}'")
            text = fallback_text.strip()
        else:
            text = "Unknown Criteria"
    
    return text

def check_goal_name():
    """Detect the current goal name using simple Tesseract OCR.

    Captures the region (372, 113, 912, 152) and returns the recognized
    goal name as a string. Mirrors the lightweight OCR approach used in
    check_criteria (PSM 7, single line) with a single fallback to the
    shared extract_text helper.
    """
    GOAL_REGION = (372, 113, 912, 152)

    # Capture enhanced image of the goal name region for better OCR
    goal_img = enhanced_screenshot(GOAL_REGION)

    # Save debug images if enabled
    if DEBUG_MODE:
        try:
            raw_img = capture_region(GOAL_REGION)
            raw_img.save("debug_goal_region_raw.png")
        except Exception:
            pass
        try:
            goal_img.save("debug_goal_region_enhanced.png")
        except Exception:
            pass

    # Primary OCR path: single line recognition
    import pytesseract
    text = pytesseract.image_to_string(goal_img, config='--oem 3 --psm 7').strip()

    if not text:
        # Fallback once to the shared OCR helper
        fallback_text = extract_text(goal_img)
        if fallback_text.strip():
            debug_print(f"[DEBUG] Using fallback goal OCR result: '{fallback_text}'")
            text = fallback_text.strip()

    if DEBUG_MODE:
        debug_print(f"[DEBUG] Goal name OCR result: '{text}'")

    return text

def check_goal_name_with_g1_requirement():
    """Detect the current goal name and check if it requires G1 races.
    
    Returns:
        dict: Dictionary with goal name text and G1 race requirement flag
    """
    goal_name = check_goal_name()
    
    # Check if goal name contains G1 race requirements
    requires_g1_races = False
    if goal_name and "G1" in goal_name.upper():
        requires_g1_races = True
        debug_print(f"[DEBUG] G1 race requirement detected in goal name: '{goal_name}'")
    
    return {
        "text": goal_name,
        "requires_g1_races": requires_g1_races
    }

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
    
    # Cache the skill points for reuse in skill auto-purchase
    if result > 0:
        from core.skill_auto_purchase import cache_skill_points
        cache_skill_points(result)
    
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
                skill_file = config.get("skill_file", "skills.json")
                print(f"[INFO] Loading skills from: {skill_file}")
                cfg = load_skill_config(skill_file)
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

def check_current_stats():
    """
    Check current character stats using OCR on the stat regions.
    
    Returns:
        dict: Dictionary of current stats with keys: spd, sta, pwr, guts, wit
    """
    from utils.constants_phone import SPD_REGION, STA_REGION, PWR_REGION, GUTS_REGION, WIT_REGION
    from utils.adb_screenshot import take_screenshot
    import pytesseract
    from PIL import Image, ImageEnhance
    
    stats = {}
    stat_regions = {
        'spd': SPD_REGION,
        'sta': STA_REGION,
        'pwr': PWR_REGION,
        'guts': GUTS_REGION,
        'wit': WIT_REGION
    }
    
    for stat_name, region in stat_regions.items():
        try:
            # Take screenshot and crop to stat region
            screenshot = take_screenshot()
            stat_img = screenshot.crop(region)
            
            # Enhance image for better OCR
            stat_img = stat_img.resize((stat_img.width * 2, stat_img.height * 2), Image.BICUBIC)
            stat_img = stat_img.convert("L")  # Convert to grayscale
            stat_img = ImageEnhance.Contrast(stat_img).enhance(2.0)  # Increase contrast
            
            # OCR the stat value
            stat_text = pytesseract.image_to_string(stat_img, config='--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789').strip()
            
            # Try to extract the number
            if stat_text:
                # Remove any non-digit characters and take the first number
                import re
                numbers = re.findall(r'\d+', stat_text)
                if numbers:
                    stats[stat_name] = int(numbers[0])
                    debug_print(f"[DEBUG] {stat_name.upper()} stat: {stats[stat_name]}")
                else:
                    stats[stat_name] = 0
                    debug_print(f"[DEBUG] Failed to extract {stat_name.upper()} stat from text: '{stat_text}'")
            else:
                stats[stat_name] = 0
                debug_print(f"[DEBUG] No text found for {stat_name.upper()} stat")
                
        except Exception as e:
            debug_print(f"[DEBUG] Error reading {stat_name.upper()} stat: {e}")
            stats[stat_name] = 0
    
    debug_print(f"[DEBUG] Current stats: {stats}")
    return stats



def check_energy_bar():
    """
    Check the energy bar fill percentage using the same logic as energy_detector.py.
    
    Returns:
        float: Energy percentage (0.0 to 100.0)
    """
    try:
        import cv2
        import numpy as np
        
        # Take screenshot and crop to energy bar region (updated coordinates from user)
        screenshot = take_screenshot()
        x, y, width, height = 294, 203, 648, 102
        cropped = screenshot.crop((x, y, x + width, y + height))
        
        # Convert to numpy array and handle RGBA -> RGB
        cropped_np = np.array(cropped, dtype=np.uint8)
        if cropped_np.shape[2] == 4:
            cropped_np = cropped_np[:, :, :3]  # Keep only RGB channels
        
        # Step 1: Find the white border (253, 253, 253)
        white_tolerance = 5
        white_lower = np.array([253 - white_tolerance, 253 - white_tolerance, 253 - white_tolerance])
        white_upper = np.array([253 + white_tolerance, 253 + white_tolerance, 253 + white_tolerance])
        white_mask = cv2.inRange(cropped_np, white_lower, white_upper)
        
        # Step 2: Find the rounded rectangle contour and create an interior mask
        contours, _ = cv2.findContours(white_mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            debug_print("[DEBUG] No energy bar contour found")
            return 0.0
        
        # Find the largest contour (should be the energy bar's outer white border)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Create a mask for the area enclosed by the white border
        border_mask = np.zeros(cropped_np.shape[:2], dtype=np.uint8)
        cv2.drawContours(border_mask, [largest_contour], -1, 255, cv2.FILLED)
        
        # Erode the border mask to get the interior (remove the border itself)
        kernel = np.ones((5,5), np.uint8)
        interior_mask = cv2.erode(border_mask, kernel, iterations=1)
        
        # Step 3: Count gray pixels vs total pixels in the interior using horizontal line analysis
        # Create mask for gray pixels (117, 117, 117)
        gray_tolerance = 10
        gray_lower = np.array([117 - gray_tolerance, 117 - gray_tolerance, 117 - gray_tolerance])
        gray_upper = np.array([117 + gray_tolerance, 117 + gray_tolerance, 117 + gray_tolerance])
        gray_mask = cv2.inRange(cropped_np, gray_lower, gray_upper)
        
        # Apply interior mask to only consider gray pixels inside the rounded rectangle
        gray_pixels_inside = cv2.bitwise_and(gray_mask, interior_mask)
        
        # Horizontal line analysis
        contours_interior, _ = cv2.findContours(interior_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours_interior:
            debug_print("[DEBUG] No interior contour found")
            return 0.0
        
        x_rect, y_rect, w_rect, h_rect = cv2.boundingRect(contours_interior[0])
        
        # Use the middle horizontal line for analysis
        middle_y = y_rect + h_rect // 2
        
        # Ensure middle_y is within bounds
        if not (0 <= middle_y < interior_mask.shape[0]):
            debug_print("[DEBUG] Middle Y coordinate out of bounds")
            return 0.0
        
        # Extract the horizontal line from both interior and gray masks
        interior_line = interior_mask[middle_y, :]
        gray_line = gray_pixels_inside[middle_y, :]
        
        # Find the leftmost and rightmost points of the bar on this line
        interior_points = np.where(interior_line > 0)[0]
        if len(interior_points) > 0:
            leftmost = interior_points[0]
            rightmost = interior_points[-1]
            total_width = rightmost - leftmost + 1
            
            # Count gray pixels in this horizontal line within the bar's width
            gray_points = np.where(gray_line[leftmost:rightmost+1] > 0)[0]
            gray_width = len(gray_points)
            filled_width = total_width - gray_width
            
            # Calculate fill percentage based on horizontal line
            fill_percentage = (filled_width / total_width) * 100.0 if total_width > 0 else 0.0
            
            debug_print(f"[DEBUG] Energy bar: width={total_width}px, gray={gray_width}px, filled={filled_width}px, percentage={fill_percentage:.1f}%")
            return fill_percentage
        else:
            debug_print("[DEBUG] No interior points found on analysis line")
            return 0.0
            
    except Exception as e:
        debug_print(f"[DEBUG] Energy bar check failed: {e}")
        return 0.0

 