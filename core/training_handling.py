import time
import json
from PIL import ImageStat, Image, ImageEnhance
import numpy as np
import pytesseract
import re
import os

from utils.adb_recognizer import locate_on_screen, locate_all_on_screen, is_image_on_screen, match_template, max_match_confidence
from utils.input import tap, triple_click, swipe, tap_on_image
from utils.adb_screenshot import take_screenshot, enhanced_screenshot
from utils.constants_phone import *
from utils.log import debug_print
from utils.template_matching import wait_for_image, deduplicated_matches

# Load config for DEBUG_MODE
try:
    with open("config.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
        DEBUG_MODE = config.get("debug_mode", False)
except Exception:
    DEBUG_MODE = False



# Import ADB state functions



# Support icon templates for detailed detection
SUPPORT_ICON_PATHS = {
    "spd": "assets/icons/support_card_type_spd.png",
    "sta": "assets/icons/support_card_type_sta.png",
    "pwr": "assets/icons/support_card_type_pwr.png",
    "guts": "assets/icons/support_card_type_guts.png",
    "wit": "assets/icons/support_card_type_wit.png",
    "friend": "assets/icons/support_card_type_friend.png",
}

# Bond color classification helpers
BOND_SAMPLE_OFFSET = (-2, 116)
BOND_LEVEL_COLORS = {
    5: (255, 235, 120),
    4: (255, 173, 30),
    3: (162, 230, 30),
    2: (42, 192, 255),
    1: (109, 108, 117),
}

def _classify_bond_level(rgb_tuple):
    """Classify bond level based on RGB color values"""
    r, g, b = rgb_tuple
    best_level, best_dist = 1, float('inf')
    for level, (cr, cg, cb) in BOND_LEVEL_COLORS.items():
        dr, dg, db = r - cr, g - cg, b - cb
        dist = dr*dr + dg*dg + db*db
        if dist < best_dist:
            best_dist, best_level = dist, level
    return best_level

def _filtered_template_matches(screenshot, template_path, region_cv, confidence=0.8):
    """Get filtered template matches with deduplication"""
    raw = match_template(screenshot, template_path, confidence, region_cv)
    if not raw:
        return []
    return deduplicated_matches(raw, threshold=30)



def go_to_training():
    """Go to training screen"""
    debug_print("[DEBUG] Going to training screen...")
    time.sleep(1)
    return tap_on_image("assets/buttons/training_btn.png", min_search=10)

def check_training():
    """Check training results using fixed coordinates, collecting support counts,
    bond levels and hint presence in one hover pass before computing failure rates."""
    debug_print("[DEBUG] Checking training options...")
    
    # Fixed coordinates for each training type
    training_coords = {
        "spd": (165, 1557),
        "sta": (357, 1563),
        "pwr": (546, 1557),
        "guts": (735, 1566),
        "wit": (936, 1572)
    }
    results = {}

    for key, coords in training_coords.items():
        debug_print(f"[DEBUG] Checking {key.upper()} training at coordinates {coords}...")
        
        # Proper hover simulation: move to position, hold, check, move away, release
        debug_print(f"[DEBUG] Hovering over {key.upper()} training to check support cards...")
        
        # Step 1: Hold at button position and move mouse up 300 pixels to simulate hover
        debug_print(f"[DEBUG] Holding at {key.upper()} training button and moving mouse up...")
        # Swipe from button position up 300 pixels with longer duration to simulate holding and moving
        start_x, start_y = coords
        end_x, end_y = start_x, start_y - 200  # Move up 300 pixels
        swipe(start_x, start_y, end_x, end_y, duration_ms=100)  # Shorter duration for hover effect
        time.sleep(0.1)  # Wait for hover effect to register
        
        # Step 2: One pass: capture screenshot, evaluate support counts, bond levels, and hint
        screenshot = take_screenshot()
        left, top, right, bottom = SUPPORT_CARD_ICON_REGION
        region_cv = (left, top, right - left, bottom - top)

        # Support counts - pass screenshot to avoid taking new one
        support_counts = check_support_card(screenshot)  # ✅ Pass screenshot
        total_support = sum(support_counts.values())

        # Bond levels per type
        detailed_support = {}
        rgb_img = screenshot.convert("RGB")
        width, height = rgb_img.size
        dx, dy = BOND_SAMPLE_OFFSET
        for t_key, tpl in SUPPORT_ICON_PATHS.items():
            matches = _filtered_template_matches(screenshot, tpl, region_cv, confidence=0.8)
            if not matches:
                continue
            entries = []
            for (x, y, w, h) in matches:
                cx, cy = int(x + w // 2), int(y + h // 2)
                sx, sy = cx + dx, cy + dy
                sx = max(0, min(width - 1, sx))
                sy = max(0, min(height - 1, sy))
                r, g, b = rgb_img.getpixel((sx, sy))
                level = _classify_bond_level((r, g, b))
                entries.append({
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "center": [cx, cy],
                    "bond_sample_point": [int(sx), int(sy)],
                    "bond_color": [int(r), int(g), int(b)],
                    "bond_level": int(level),
                })
            if entries:
                detailed_support[t_key] = entries

        # Hint - pass screenshot to avoid taking new one
        hint_found = check_hint(screenshot)  # ✅ Pass screenshot

        # Calculate score for this training type
        score = calculate_training_score(detailed_support, hint_found, key)

        debug_print(f"[DEBUG] Support counts: {support_counts} | hint_found={hint_found} | score={score}")

        debug_print(f"[DEBUG] Checking failure rate for {key.upper()} training...")
        # Pass screenshot to avoid taking new ones
        failure_chance, confidence = check_failure(screenshot, key)  # ✅ Pass screenshot
        
        results[key] = {
            "support": support_counts,
            "support_detail": detailed_support,
            "hint": bool(hint_found),
            "total_support": total_support,
            "failure": failure_chance,
            "confidence": confidence,
            "score": score
        }
        
        # Use clean format matching training_score_test.py exactly
        print(f"\n[{key.upper()}]")
        
        # Show support card details (similar to test script)
        if detailed_support:
            support_lines = []
            for card_type, entries in detailed_support.items():
                for idx, entry in enumerate(entries, start=1):
                    level = entry['bond_level']
                    is_rainbow = (card_type == key and level >= 4)
                    label = f"{card_type.upper()}{idx}: {level}"
                    if is_rainbow:
                        label += " (Rainbow)"
                    support_lines.append(label)
            print(", ".join(support_lines))
        else:
            print("-")
        
        print(f"hint={hint_found}")
        print(f"Fail: {failure_chance}% - Confident: {confidence:.2f}")
        print(f"Score: {score}")
        

    
    debug_print("[DEBUG] Going back from training screen...")
    tap_on_image("assets/buttons/back_btn.png")
    
    # Print overall summary
    print("\n=== Overall ===")
    for k in ["spd", "sta", "pwr", "guts", "wit"]:
        if k in results:
            data = results[k]
            print(f"{k.upper()}: Score={data['score']:.2f}, Fail={data['failure']}% - Confident: {data['confidence']:.2f}")
    
    return results

def do_train(train):
    """Perform training of specified type"""
    debug_print(f"[DEBUG] Performing {train.upper()} training...")
    
    # First, go to training screen
    if not go_to_training():
        debug_print(f"[DEBUG] Failed to go to training screen, cannot perform {train.upper()} training")
        return
    
    # Wait for screen to load and verify we're on training screen
    time.sleep(1.0)
    
    # Fixed coordinates for each training type
    training_coords = {
        "spd": (165, 1557),
        "sta": (357, 1563),
        "pwr": (546, 1557),
        "guts": (735, 1566),
        "wit": (936, 1572)
    }
    
    # Check if the requested training type exists
    if train not in training_coords:
        debug_print(f"[DEBUG] Unknown training type: {train}")
        return
    
    # Get the coordinates for the requested training type
    train_coords = training_coords[train]
    debug_print(f"[DEBUG] Found {train.upper()} training at coordinates {train_coords}")
    triple_click(train_coords[0], train_coords[1], interval=0.1)
    debug_print(f"[DEBUG] Triple clicked {train.upper()} training button")

# Training-related functions moved from state_adb.py
def check_support_card(screenshot, threshold=0.85):
    SUPPORT_ICONS = {
        "spd": "assets/icons/support_card_type_spd.png",
        "sta": "assets/icons/support_card_type_sta.png",
        "pwr": "assets/icons/support_card_type_pwr.png",
        "guts": "assets/icons/support_card_type_guts.png",
        "wit": "assets/icons/support_card_type_wit.png",
        "friend": "assets/icons/support_card_type_friend.png"
    }

    count_result = {}

    # Use provided screenshot instead of taking new one
    # screenshot = take_screenshot()  # ❌ REMOVED
    
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
        filtered_matches = deduplicated_matches(matches, threshold=30) if matches else []
        
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

def check_hint(screenshot, template_path: str = "assets/icons/hint.png", confidence: float = 0.6) -> bool:
    """Detect presence of a hint icon within the support card search region.

    Args:
        template_path: Path to the hint icon template image.
        confidence: Minimum confidence threshold for template matching.

    Returns:
        True if at least one hint icon is found in `SUPPORT_CARD_ICON_REGION`, otherwise False.
    """
    try:
        # Use provided screenshot instead of taking new one
        # screenshot = take_screenshot()  # ❌ REMOVED

        # Convert PIL (left, top, right, bottom) to OpenCV (x, y, width, height)
        left, top, right, bottom = SUPPORT_CARD_ICON_REGION
        region_cv = (left, top, right - left, bottom - top)
        debug_print(f"[DEBUG] Checking hint in region: {region_cv} using template: {template_path}")

        if DEBUG_MODE:
            try:
                screenshot.crop(SUPPORT_CARD_ICON_REGION).save("debug_hint_search_region.png")
                debug_print("[DEBUG] Saved hint search region to debug_hint_search_region.png")
            except Exception:
                pass

        matches = match_template(screenshot, template_path, confidence, region_cv)

        found = bool(matches and len(matches) > 0)
        debug_print(f"[DEBUG] Hint icon found: {found}")
        return found
    except Exception as e:
        debug_print(f"[DEBUG] check_hint failed: {e}")
        return False

def check_failure(screenshot, train_type):
    """
    Check failure rate for a specific training type using provided screenshot instead of taking new ones.
    Args:
        screenshot: PIL Image object to analyze
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
        # Crop from provided screenshot instead of taking new one
        img = screenshot.crop(region)  # ✅ Use provided screenshot instead of enhanced_screenshot()
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
        # Crop from provided screenshot instead of taking new one
        raw_img = screenshot.crop(region)  # ✅ Use provided screenshot instead of take_screenshot()
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

def choose_best_training(training_results, config, current_stats):
    """
    Choose the best training option based on scoring algorithm.
    
    Args:
        training_results (dict): Results from check_training()
        config (dict): Training configuration with thresholds
        current_stats (dict): Current character stats to check against caps
        
    Returns:
        str: Best training type (spd, sta, pwr, guts, wit) or None
    """
    if not training_results:
        return None
    
    max_failure = config.get("maximum_failure", 15)
    min_score = config.get("min_score", 1.0)
    min_wit_score = config.get("min_wit_score", 1.0)
    priority_stat = config.get("priority_stat", ["spd", "sta", "wit", "pwr", "guts"])
    
    # Filter out training options with failure rates above maximum
    safe_options = {k: v for k, v in training_results.items() 
                   if v.get('failure', 100) <= max_failure}
    
    if not safe_options:
        debug_print(f"[DEBUG] No training options with failure rate <= {max_failure}%")
        return None
    
    # Filter by minimum score requirements
    valid_options = {}
    for k, v in capped_options.items():
        score = v.get('score', 0)
        if k == 'wit' and score < min_wit_score:
            continue
        if score < min_score:
            continue
        valid_options[k] = v
    
    if not valid_options:
        debug_print(f"[DEBUG] No training options meet minimum score requirements")
        return None
    
    # Filter by stat caps BEFORE other filtering
    from core.logic import filter_by_stat_caps
    
    # Safety check for current_stats
    if not current_stats:
        debug_print("[DEBUG] No current stats available, skipping stat cap filtering")
        capped_options = safe_options
    else:
        debug_print(f"[DEBUG] Applying stat cap filtering with current stats: {current_stats}")
        capped_options = filter_by_stat_caps(safe_options, current_stats)
    
    if not capped_options:
        debug_print(f"[DEBUG] All training options filtered out by stat caps")
        return None
    
    # Sort by priority stat order and then by score
    def sort_key(item):
        k, v = item
        priority_index = priority_stat.index(k) if k in priority_stat else len(priority_stat)
        return (priority_index, -v.get('score', 0))  # Higher score first
    
    sorted_options = sorted(valid_options.items(), key=sort_key)
    best_training = sorted_options[0][0]
    
    debug_print(f"[DEBUG] Best training selected: {best_training} (score: {sorted_options[0][1].get('score', 0):.2f})")
    return best_training

def calculate_training_score(support_detail, hint_found, training_type):
    """
    Calculate training score based on support cards, bond levels, and hints.
    
    Args:
        support_detail: Dictionary of support card details with bond levels
        hint_found: Boolean indicating if hint is present
        training_type: The type of training being evaluated
    
    Returns:
        float: Calculated score for the training
    """
    # Load scoring rules from training_score.json
    scoring_rules = {}
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'training_score.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            scoring_rules = config.get('scoring_rules', {})
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Could not load training_score.json: {e}")
        # Fallback to default values if config file is not available
        scoring_rules = {
            "rainbow_support": {"points": 1.0},
            "not_rainbow_support_low": {"points": 0.7},
            "not_rainbow_support_high": {"points": 0.0},
            "hint": {"points": 0.3}
        }
    
    score = 0.0
    
    # Score support cards based on bond levels
    for card_type, entries in support_detail.items():
        for entry in entries:
            level = entry['bond_level']
            is_rainbow = (card_type == training_type and level >= 4)
            
            if is_rainbow:
                score += scoring_rules.get("rainbow_support", {}).get("points", 1.0)
            else:
                if level < 4:
                    score += scoring_rules.get("not_rainbow_support_low", {}).get("points", 0.7)
                # bond >= 4 for non-rainbow gets points from not_rainbow_support_high (0.0)
    
    # Add hint bonus
    if hint_found:
        score += scoring_rules.get("hint", {}).get("points", 0.3)
    
    return round(score, 2)
