import time
import json
import os
import random
from PIL import ImageStat

from utils.adb_recognizer import locate_on_screen, locate_all_on_screen, wait_for_image, is_image_on_screen, match_template, max_match_confidence
from utils.adb_input import tap, click_at_coordinates, triple_click, move_to_and_click, mouse_down, mouse_up, scroll_down, scroll_up, long_press
from utils.adb_screenshot import take_screenshot, enhanced_screenshot, capture_region
from utils.constants_phone import (
    MOOD_LIST, EVENT_REGION, RACE_CARD_REGION, SUPPORT_CARD_ICON_REGION
)

# Import ADB state and logic modules
from core.state_adb import check_support_card, check_failure, check_turn, check_mood, check_current_year, check_criteria, check_skill_points_cap, check_goal_name, check_goal_name_with_g1_requirement, check_hint, calculate_training_score, choose_best_training, check_current_stats, check_energy_bar

# Import event handling functions
from core.event_handling import count_event_choices, load_event_priorities, analyze_event_options, generate_event_variations, search_events, handle_event_choice, click_event_choice

# Load config and check debug mode
with open("config.json", "r", encoding="utf-8") as config_file:
    config = json.load(config_file)
    DEBUG_MODE = config.get("debug_mode", False)
    RETRY_RACE = config.get("retry_race", True)

def debug_print(message):
    """Print debug message only if DEBUG_MODE is enabled"""
    if DEBUG_MODE:
        print(message)

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
    r, g, b = rgb_tuple
    best_level, best_dist = 1, float('inf')
    for level, (cr, cg, cb) in BOND_LEVEL_COLORS.items():
        dr, dg, db = r - cr, g - cg, b - cb
        dist = dr*dr + dg*dg + db*db
        if dist < best_dist:
            best_dist, best_level = dist, level
    return best_level

def _filtered_template_matches(screenshot, template_path, region_cv, confidence=0.8):
    raw = match_template(screenshot, template_path, confidence, region_cv)
    if not raw:
        return []
    filtered = []
    for (x, y, w, h) in raw:
        cx, cy = x + w // 2, y + h // 2
        duplicate = False
        for (ex, ey, ew, eh) in filtered:
            ecx, ecy = ex + ew // 2, ey + eh // 2
            if abs(cx - ecx) < 30 and abs(cy - ecy) < 30:
                duplicate = True
                break
        if not duplicate:
            filtered.append((x, y, w, h))
    return filtered

def locate_match_track_with_brightness(confidence=0.6, region=None, brightness_threshold=180.0):
    """
    Find center of `assets/ui/match_track.png` that also passes brightness threshold.
    Returns (x, y) center or None.
    """
    try:
        screenshot = take_screenshot()
        matches = match_template(screenshot, "assets/ui/match_track.png", confidence=confidence, region=region)
        if not matches:
            return None

        grayscale = screenshot.convert("L")
        for (x, y, w, h) in matches:
            try:
                roi = grayscale.crop((x, y, x + w, y + h))
                avg_brightness = ImageStat.Stat(roi).mean[0]
                debug_print(f"[DEBUG] match_track bbox=({x},{y},{w},{h}) brightness={avg_brightness:.1f} (thr {brightness_threshold})")
                if avg_brightness > brightness_threshold:
                    center = (x + w//2, y + h//2)
                    return center
            except Exception:
                continue
        return None
    except Exception as e:
        debug_print(f"[DEBUG] match_track locate error: {e}")
        return None

def is_infirmary_active_adb(button_location):
    """
    Check if the infirmary button is active (bright) or disabled (dark).
    Args:
        button_location: tuple (x, y, w, h) of the button location
    Returns:
        bool: True if button is active (bright), False if disabled (dark)
    """
    try:
        x, y, w, h = button_location
        
        # Take screenshot and crop the button region
        screenshot = take_screenshot()
        button_region = screenshot.crop((x, y, x + w, y + h))
        
        # Convert to grayscale and calculate average brightness
        grayscale = button_region.convert("L")
        stat = ImageStat.Stat(grayscale)
        avg_brightness = stat.mean[0]
        
        # Threshold for active button (same as PC version)
        is_active = avg_brightness > 150
        debug_print(f"[DEBUG] Infirmary brightness: {avg_brightness:.1f} ({'active' if is_active else 'disabled'})")
        
        return is_active
    except Exception as e:
        print(f"[ERROR] Failed to check infirmary button brightness: {e}")
        return False


def claw_machine():
    """Handle claw machine interaction"""
    print("[INFO] Claw machine detected, starting interaction...")
    
    # Wait 2 seconds before interacting
    time.sleep(2)
    
    # Find the claw button location
    claw_location = locate_on_screen("assets/buttons/claw.png", confidence=0.8)
    if not claw_location:
        print("[WARNING] Claw button not found for interaction")
        return False
    
    # Get center coordinates (locate_on_screen returns center coordinates)
    center_x, center_y = claw_location
    
    # Generate random hold duration between 3-4 seconds (in milliseconds)
    hold_duration = random.randint(1000, 3000)
    print(f"[INFO] Holding claw button for {hold_duration}ms...")
    
    # Use ADB long press to hold the claw button
    long_press(center_x, center_y, hold_duration)
    
    print("[INFO] Claw machine interaction completed")
    return True


# Event handling functions moved to core/event_handling.py
def is_racing_available(year):
    """Check if racing is available based on the current year/month"""
    # No races in Pre-Debut
    if is_pre_debut_year(year):
        return False
    # No races in Finale Season (final training period before URA)
    if "Finale Season" in year:
        return False
    year_parts = year.split(" ")
    # No races in July and August (summer break)
    if len(year_parts) > 3 and year_parts[3] in ["Jul", "Aug"]:
        return False
    return True

def click(img, confidence=0.8, minSearch=1, click=1, text="", region=None):
    """Click on image with retry logic"""
    debug_print(f"[DEBUG] Looking for: {img}")
    for attempt in range(int(minSearch)):
        btn = locate_on_screen(img, confidence=confidence, region=region)
        if btn:
            if text:
                print(text)
            debug_print(f"[DEBUG] Clicking {img} at position {btn}")
            tap(btn[0], btn[1])
            return True
        if attempt < int(minSearch) - 1:  # Don't sleep on last attempt
            debug_print(f"[DEBUG] Attempt {attempt + 1}: {img} not found")
            time.sleep(0.05)  # Reduced from 0.1 to 0.05
    debug_print(f"[DEBUG] Failed to find {img} after {minSearch} attempts")
    return False

def go_to_training():
    """Go to training screen"""
    debug_print("[DEBUG] Going to training screen...")
    time.sleep(1)
    return click("assets/buttons/training_btn.png", minSearch=10)

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
        from utils.adb_input import swipe
        # Swipe from button position up 300 pixels with longer duration to simulate holding and moving
        start_x, start_y = coords
        end_x, end_y = start_x, start_y - 300  # Move up 300 pixels
        swipe(start_x, start_y, end_x, end_y, duration_ms=200)  # Longer duration for hover effect
        time.sleep(0.3)  # Wait for hover effect to register
        
        # Step 2: One pass: capture screenshot, evaluate support counts, bond levels, and hint
        screenshot = take_screenshot()
        left, top, right, bottom = SUPPORT_CARD_ICON_REGION
        region_cv = (left, top, right - left, bottom - top)

        # Support counts
        support_counts = check_support_card()
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

        # Hint
        hint_found = check_hint()

        # Calculate score for this training type
        from core.state_adb import calculate_training_score
        score = calculate_training_score(detailed_support, hint_found, key)

        debug_print(f"[DEBUG] Support counts: {support_counts} | hint_found={hint_found} | score={score}")

        debug_print(f"[DEBUG] Checking failure rate for {key.upper()} training...")
        failure_chance, confidence = check_failure(key)
        
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
    click("assets/buttons/back_btn.png")
    
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

def do_rest():
    """Perform rest action"""
    debug_print("[DEBUG] Performing rest action...")
    print("[INFO] Performing rest action...")
    
    # Rest button is in the lobby, not on training screen
    # If we're on training screen, go back to lobby first
    from utils.adb_recognizer import locate_on_screen
    back_btn = locate_on_screen("assets/buttons/back_btn.png", confidence=0.8)
    if back_btn:
        debug_print("[DEBUG] Going back to lobby to find rest button...")
        print("[INFO] Going back to lobby to find rest button...")
        from utils.adb_input import tap
        tap(back_btn[0], back_btn[1])
        time.sleep(1.0)  # Wait for lobby to load
    
    # Now look for rest buttons in the lobby
    rest_btn = locate_on_screen("assets/buttons/rest_btn.png", confidence=0.5)
    rest_summer_btn = locate_on_screen("assets/buttons/rest_summer_btn.png", confidence=0.5)
    
    debug_print(f"[DEBUG] Rest button found: {rest_btn}")
    debug_print(f"[DEBUG] Summer rest button found: {rest_summer_btn}")
    
    if rest_btn:
        debug_print(f"[DEBUG] Clicking rest button at {rest_btn}")
        print(f"[INFO] Clicking rest button at {rest_btn}")
        from utils.adb_input import tap
        tap(rest_btn[0], rest_btn[1])
        debug_print("[DEBUG] Clicked rest button")
        print("[INFO] Rest button clicked")
    elif rest_summer_btn:
        debug_print(f"[DEBUG] Clicking summer rest button at {rest_summer_btn}")
        print(f"[INFO] Clicking summer rest button at {rest_summer_btn}")
        from utils.adb_input import tap
        tap(rest_summer_btn[0], rest_summer_btn[1])
        debug_print("[DEBUG] Clicked summer rest button")
        print("[INFO] Summer rest button clicked")
    else:
        debug_print("[DEBUG] No rest button found in lobby")
        print("[WARNING] No rest button found in lobby")

def do_recreation():
    """Perform recreation action"""
    debug_print("[DEBUG] Performing recreation action...")
    recreation_btn = locate_on_screen("assets/buttons/recreation_btn.png", confidence=0.8)
    recreation_summer_btn = locate_on_screen("assets/buttons/rest_summer_btn.png", confidence=0.8)
    
    if recreation_btn:
        debug_print(f"[DEBUG] Found recreation button at {recreation_btn}")
        tap(recreation_btn[0], recreation_btn[1])
        debug_print("[DEBUG] Clicked recreation button")
    elif recreation_summer_btn:
        debug_print(f"[DEBUG] Found summer recreation button at {recreation_summer_btn}")
        tap(recreation_summer_btn[0], recreation_summer_btn[1])
        debug_print("[DEBUG] Clicked summer recreation button")
    else:
        debug_print("[DEBUG] No recreation button found")

def do_race(prioritize_g1=False):
    """Perform race action"""
    debug_print(f"[DEBUG] Performing race action (G1 priority: {prioritize_g1})...")
    click("assets/buttons/races_btn.png", minSearch=10)
    time.sleep(1.2)
    click("assets/buttons/ok_btn.png", confidence=0.5, minSearch=1)

    found = race_select(prioritize_g1=prioritize_g1)
    if found:
        debug_print("[DEBUG] Race found and selected, proceeding to race preparation")
        race_prep()
        time.sleep(1)
        # If race failed screen appears, handle retry before proceeding
        handle_race_retry_if_failed()
        after_race()
        return True
    else:
        debug_print("[DEBUG] No race found, going back")
        click("assets/buttons/back_btn.png", minSearch=0.7)
        return False

def race_day():
    """Handle race day"""
    # Check skill points cap before race day (if enabled)
    import json
    
    # Load config to check if skill point check is enabled
    with open("config.json", "r", encoding="utf-8") as file:
        config = json.load(file)
    
    enable_skill_check = config.get("enable_skill_point_check", True)
    
    if enable_skill_check:
        print("[INFO] Race Day - Checking skill points cap...")
        check_skill_points_cap()
    
    debug_print("[DEBUG] Clicking race day button...")
    if click("assets/buttons/race_day_btn.png", minSearch=10):
        debug_print("[DEBUG] Race day button clicked, clicking OK button...")
        time.sleep(1.3)
        click("assets/buttons/ok_btn.png", confidence=0.5, minSearch=2)
        time.sleep(1.0)  # Increased wait time
        
        # Try to find and click race button with better error handling
        race_clicked = False
        for attempt in range(3):  # Try up to 3 times
            if click("assets/buttons/race_btn.png", confidence=0.7, minSearch=1):
                debug_print(f"[DEBUG] Race button clicked successfully, attempt {attempt + 1}")
                time.sleep(0.5)  # Wait between clicks
                
                # Click race button twice like in race_select
                for j in range(2):
                    if click("assets/buttons/race_btn.png", confidence=0.7, minSearch=1):
                        debug_print(f"[DEBUG] Race button clicked {j+1} time(s)")
                        time.sleep(0.5)
                    else:
                        debug_print(f"[DEBUG] Failed to click race button {j+1} time(s)")
                
                race_clicked = True
                time.sleep(0.8)  # Wait for UI to respond
                break
            else:
                debug_print(f"[DEBUG] Race button not found, attempt {attempt + 1}")
                time.sleep(0.5)
        
        if not race_clicked:
            debug_print("[ERROR] Failed to click race button after multiple attempts")
            return False
            
        debug_print("[DEBUG] Starting race preparation...")
        race_prep()
        time.sleep(1)
        # If race failed screen appears, handle retry before proceeding
        handle_race_retry_if_failed()
        after_race()
        return True
    return False

def race_select(prioritize_g1=False):
    """Select race"""
    debug_print(f"[DEBUG] Selecting race (G1 priority: {prioritize_g1})...")
    
    
    def find_and_select_race():
        """Helper function to find and select a race (G1 or normal)"""
        # Wait for race list to load before detection
        debug_print("[DEBUG] Waiting for race list to load...")
        time.sleep(1.5)
        
        # Check initial screen first
        if prioritize_g1:
            debug_print("[DEBUG] Looking for G1 race.")
            screenshot = take_screenshot()
            race_cards = match_template(screenshot, "assets/ui/g1_race.png", confidence=0.9)
            debug_print(f"[DEBUG] Initial G1 detection result: {race_cards}")
            
            if race_cards:
                debug_print(f"[DEBUG] Found {len(race_cards)} G1 race card(s), searching for match_track within regions...")
                for x, y, w, h in race_cards:
                    # Search for match_track.png within the race card region
                    region = (x, y, RACE_CARD_REGION[2], RACE_CARD_REGION[3])
                    debug_print(f"[DEBUG] Searching region: {region}")
                    match_aptitude = locate_match_track_with_brightness(confidence=0.6, region=region, brightness_threshold=180.0)
                    if match_aptitude:
                        debug_print(f"[DEBUG] ✅ Match track found at {match_aptitude} in region {region}")
                    else:
                        debug_print(f"[DEBUG] ❌ No match track found in region {region}")
                    if match_aptitude:
                        debug_print(f"[DEBUG] G1 race found at {match_aptitude}")
                        tap(match_aptitude[0], match_aptitude[1])
                        time.sleep(0.2)
                        
                        # Click race button twice like PC version
                        for j in range(2):
                            race_btn = locate_on_screen("assets/buttons/race_btn.png", confidence=0.6)
                            if race_btn:
                                debug_print(f"[DEBUG] Found race button at {race_btn}")
                                tap(race_btn[0], race_btn[1])
                                time.sleep(0.5)
                            else:
                                debug_print("[DEBUG] Race button not found")
                        return True
            else:
                debug_print("[DEBUG] No G1 race cards found on initial screen, will try swiping...")
        else:
            debug_print("[DEBUG] Looking for race.")
            match_aptitude = locate_match_track_with_brightness(confidence=0.6, brightness_threshold=180.0)
            if match_aptitude:
                debug_print(f"[DEBUG] Race found at {match_aptitude}")
                tap(match_aptitude[0], match_aptitude[1])
                time.sleep(0.2)
                
                # Click race button twice like PC version
                for j in range(2):
                    race_btn = locate_on_screen("assets/buttons/race_btn.png", confidence=0.8)
                    if race_btn:
                        debug_print(f"[DEBUG] Found race button at {race_btn}")
                        tap(race_btn[0], race_btn[1])
                        time.sleep(0.5)
                    else:
                        debug_print("[DEBUG] Race button not found")
                return True
        
        # If not found on initial screen, try scrolling up to 4 times
        for scroll in range(4):
            # Use direct swipe instead of scroll_down
            from utils.adb_input import swipe
            debug_print(f"[DEBUG] Swiping from (378,1425) to (378,1106) (attempt {scroll+1}/4)")
            swipe(378, 1425, 378, 1106, duration_ms=500)
            time.sleep(0.2)
            
            # Check for race again after each swipe
            if prioritize_g1:
                screenshot = take_screenshot()
                race_cards = match_template(screenshot, "assets/ui/g1_race.png", confidence=0.9)
                
                if race_cards:
                    debug_print(f"[DEBUG] Found {len(race_cards)} G1 race card(s) after swipe {scroll+1}")
                    for i, (x, y, w, h) in enumerate(race_cards):
                        debug_print(f"[DEBUG] G1 Race Card {i+1}: bbox=({x}, {y}, {w}, {h})")
                        # Search for match_track.png within the race card region
                        region = (x, y, RACE_CARD_REGION[2], RACE_CARD_REGION[3])
                        debug_print(f"[DEBUG] Extended region: {region}")
                        match_aptitude = locate_match_track_with_brightness(confidence=0.6, region=region, brightness_threshold=180.0)
                        if match_aptitude:
                            debug_print(f"[DEBUG] ✅ Match track found at {match_aptitude} in region {region}")
                        else:
                            debug_print(f"[DEBUG] ❌ No match track found in region {region}")
                        if match_aptitude:
                            debug_print(f"[DEBUG] G1 race found at {match_aptitude} after swipe {scroll+1}")
                            tap(match_aptitude[0], match_aptitude[1])
                            time.sleep(0.2)
                            
                            # Click race button twice like PC version
                            for j in range(2):
                                race_btn = locate_on_screen("assets/buttons/race_btn.png", confidence=0.8)
                                if race_btn:
                                    debug_print(f"[DEBUG] Found race button at {race_btn}")
                                    tap(race_btn[0], race_btn[1])
                                    time.sleep(0.5)
                                else:
                                    debug_print("[DEBUG] Race button not found")
                            return True
                else:
                    debug_print(f"[DEBUG] No G1 race cards found after swipe {scroll+1}")
            else:
                debug_print(f"[DEBUG] Looking for any race (non-G1) after swipe {scroll+1}")
                match_aptitude = locate_match_track_with_brightness(confidence=0.6, brightness_threshold=180.0)
                if match_aptitude:
                    debug_print(f"[DEBUG] Race found at {match_aptitude} after swipe {scroll+1}")
                    tap(match_aptitude[0], match_aptitude[1])
                    time.sleep(0.2)
                    
                    # Click race button twice like PC version
                    for j in range(2):
                        race_btn = locate_on_screen("assets/buttons/race_btn.png", confidence=0.8)
                        if race_btn:
                            debug_print(f"[DEBUG] Found race button at {race_btn}")
                            tap(race_btn[0], race_btn[1])
                            time.sleep(0.5)
                        else:
                            debug_print("[DEBUG] Race button not found")
                    return True
                else:
                    debug_print(f"[DEBUG] No races found after swipe {scroll+1}")
        
        return False
    
    # Use the unified race finding logic
    found = find_and_select_race()
    if not found:
        debug_print("[DEBUG] No suitable race found")
    return found

def check_strategy_before_race(region=(660, 974, 378, 120)) -> bool:
    """Check and ensure strategy matches config before race."""
    debug_print("[DEBUG] Checking strategy before race...")
    
    try:
        screenshot = take_screenshot()
        
        templates = {
            "front": "assets/icons/front.png",
            "late": "assets/icons/late.png", 
            "pace": "assets/icons/pace.png",
            "end": "assets/icons/end.png",
        }
        
        # Find brightest strategy using existing project functions
        best_match = None
        best_brightness = 0
        
        for name, path in templates.items():
            try:
                # Use existing match_template function
                matches = match_template(screenshot, path, confidence=0.5, region=region)
                if matches:
                    # Get confidence for best match
                    confidence = max_match_confidence(screenshot, path, region)
                    if confidence:
                        # Check brightness of the matched region
                        x, y, w, h = matches[0]
                        roi = screenshot.convert("L").crop((x, y, x + w, y + h))
                        from PIL import ImageStat
                        bright = float(ImageStat.Stat(roi).mean[0])
                        
                        if bright >= 160 and bright > best_brightness:
                            best_match = (name, matches[0], confidence, bright)
                            best_brightness = bright
            except Exception:
                continue
        
        if not best_match:
            debug_print("[DEBUG] No strategy found with brightness >= 160")
            return False
        
        strategy_name, bbox, conf, bright = best_match
        current_strategy = strategy_name.upper()
        
        # Load expected strategy from config
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            expected_strategy = config.get("strategy", "").upper()
        except Exception:
            debug_print("[DEBUG] Cannot read config.json")
            return False
        
        matches = current_strategy == expected_strategy
        debug_print(f"[DEBUG] Current: {current_strategy}, Expected: {expected_strategy}, Match: {matches}")
        
        if matches:
            debug_print("[DEBUG] Strategy matches config, proceeding with race")
            return True
        
        # Strategy doesn't match, try to change it
        debug_print(f"[DEBUG] Strategy mismatch, changing to {expected_strategy}")
        
        if change_strategy_before_race(expected_strategy):
            # Recheck after change
            new_strategy, new_matches = check_strategy_before_race(region)
            if new_matches:
                debug_print("[DEBUG] Strategy successfully changed")
                return True
            else:
                debug_print("[DEBUG] Strategy change failed")
                return False
        else:
            debug_print("[DEBUG] Failed to change strategy")
            return False
            
    except Exception as e:
        debug_print(f"[DEBUG] Error checking strategy: {e}")
        return False


def change_strategy_before_race(expected_strategy: str) -> bool:
    """Change strategy to the expected one before race."""
    debug_print(f"[DEBUG] Changing strategy to: {expected_strategy}")
    
    # Strategy coordinates mapping
    strategy_coords = {
        "FRONT": (882, 1159),
        "PACE": (645, 1159),
        "LATE": (414, 1159),
        "END": (186, 1162),
    }
    
    if expected_strategy not in strategy_coords:
        debug_print(f"[DEBUG] Unknown strategy: {expected_strategy}")
        return False
    
    try:
        # Step 1: Find and tap strategy_change.png
        debug_print("[DEBUG] Looking for strategy change button...")
        change_btn = wait_for_image("assets/buttons/strategy_change.png", timeout=10, confidence=0.8)
        if not change_btn:
            debug_print("[DEBUG] Strategy change button not found")
            return False
        
        debug_print(f"[DEBUG] Found strategy change button at {change_btn}")
        tap(change_btn[0], change_btn[1])
        debug_print("[DEBUG] Tapped strategy change button")
        
        # Step 2: Wait for confirm.png to appear
        debug_print("[DEBUG] Waiting for confirm button to appear...")
        confirm_btn = wait_for_image("assets/buttons/confirm.png", timeout=10, confidence=0.8)
        if not confirm_btn:
            debug_print("[DEBUG] Confirm button not found after strategy change")
            return False
        
        debug_print(f"[DEBUG] Confirm button appeared at {confirm_btn}")
        
        # Step 3: Tap on the specified coordinate for the right strategy
        target_x, target_y = strategy_coords[expected_strategy]
        debug_print(f"[DEBUG] Tapping strategy position: ({target_x}, {target_y}) for {expected_strategy}")
        tap(target_x, target_y)
        debug_print(f"[DEBUG] Tapped strategy position for {expected_strategy}")
        
        # Step 4: Tap confirm.png from found location
        debug_print("[DEBUG] Confirming strategy change...")
        tap(confirm_btn[0], confirm_btn[1])
        debug_print("[DEBUG] Tapped confirm button")
        
        # Wait a moment for the change to take effect
        time.sleep(2)
        
        debug_print(f"[DEBUG] Strategy change completed for {expected_strategy}")
        return True
        
    except Exception as e:
        debug_print(f"[DEBUG] Error during strategy change: {e}")
        return False


def race_prep():
    """Prepare for race"""
    debug_print("[DEBUG] Preparing for race...")
    
    view_result_btn = wait_for_image("assets/buttons/view_results.png", timeout=20)
        
    # Check and ensure strategy matches config before race
    if not check_strategy_before_race():
        debug_print("[DEBUG] Failed to ensure correct strategy, proceeding anyway...")
    if view_result_btn:
        debug_print(f"[DEBUG] Found view results button at {view_result_btn}")
        tap(view_result_btn[0], view_result_btn[1])
        time.sleep(0.5)
        for i in range(1):
            debug_print(f"[DEBUG] Clicking view results {i + 1}/3")
            triple_click(view_result_btn[0], view_result_btn[1], interval=0.01)
            time.sleep(0.01)
        debug_print("[DEBUG] Race preparation complete")
    else:
        debug_print("[DEBUG] View results button not found")

def handle_race_retry_if_failed():
    """Detect race failure on race day and retry based on config.

    Recognizes failure by detecting `assets/icons/clock.png` on screen.
    If `retry_race` is true in config, taps `assets/buttons/try_again.png`, waits 5s,
    and calls `race_prep()` again. Returns True if a retry was performed, False otherwise.
    """
    try:
        # Check for failure indicator (clock icon)
        clock = locate_on_screen("assets/icons/clock.png", confidence=0.8)
        if not clock:
            return False

        print("[INFO] Race failed detected (clock icon).")

        if not RETRY_RACE:
            print("[INFO] retry_race is disabled. Stopping automation.")
            raise SystemExit(0)

        # Try to click Try Again button
        try_again = locate_on_screen("assets/buttons/try_again.png", confidence=0.8)
        if try_again:
            print("[INFO] Clicking Try Again button.")
            tap(try_again[0], try_again[1])
        else:
            print("[INFO] Try Again button not found. Attempting helper click...")
            # Fallback: attempt generic click using click helper
            click("assets/buttons/try_again.png", confidence=0.8, minSearch=10)

        # Wait before re-prepping the race
        print("[INFO] Waiting 5 seconds before retrying the race...")
        time.sleep(5)
        print("[INFO] Re-preparing race...")
        race_prep()
        return True
    except SystemExit:
        raise
    except Exception as e:
        print(f"[ERROR] handle_race_retry_if_failed error: {e}")
        return False

def after_race():
    """Handle post-race actions"""
    debug_print("[DEBUG] Handling post-race actions...")
    
    # Try to click first next button with fallback mechanism
    if not click("assets/buttons/next_btn.png", confidence=0.7, minSearch=10):
        debug_print("[DEBUG] First next button not found after 10 attempts, clicking middle of screen as fallback...")
        tap(540, 960)  # Click middle of screen (1080x1920 resolution)
        time.sleep(1)
        debug_print("[DEBUG] Retrying next button search after screen tap...")
        click("assets/buttons/next_btn.png", confidence=0.7, minSearch=10)
    
    time.sleep(4)
    
    # Try to click second next button with fallback mechanism
    if not click("assets/buttons/next2_btn.png", confidence=0.7, minSearch=10):
        debug_print("[DEBUG] Second next button not found after 10 attempts, clicking middle of screen as fallback...")
        tap(540, 960)  # Click middle of screen (1080x1920 resolution)
        time.sleep(1)
        debug_print("[DEBUG] Retrying next2 button search after screen tap...")
        click("assets/buttons/next2_btn.png", confidence=0.7, minSearch=10)
    
    debug_print("[DEBUG] Post-race actions complete")

def career_lobby():
    """Main career lobby loop"""
    # Load configuration
    try:
        with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
        MINIMUM_MOOD = config["minimum_mood"]
        PRIORITIZE_G1_RACE = config["prioritize_g1_race"]
    except Exception as e:
        print(f"Error loading config: {e}")
        MINIMUM_MOOD = "GREAT"
        PRIORITIZE_G1_RACE = False

    # Program start
    while True:
        debug_print("\n[DEBUG] ===== Starting new loop iteration =====")
        
        # Batch UI check - take one screenshot and check multiple elements
        debug_print("[DEBUG] Performing batch UI element check...")
        screenshot = take_screenshot()
        
        # Check claw machine first (highest priority)
        debug_print("[DEBUG] Checking for claw machine...")
        claw_matches = match_template(screenshot, "assets/buttons/claw.png", confidence=0.8)
        if claw_matches:
            claw_machine()
            continue
        
        # Check OK button
        debug_print("[DEBUG] Checking for OK button...")
        ok_matches = match_template(screenshot, "assets/buttons/ok_btn.png", confidence=0.7)
        if ok_matches:
            x, y, w, h = ok_matches[0]
            center = (x + w//2, y + h//2)
            print("[INFO] OK button found, clicking it.")
            tap(center[0], center[1])
            continue
        
        # Check for events
        debug_print("[DEBUG] Checking for events...")
        try:
            event_choice_region = (6, 450, 126, 1776)
            event_matches = match_template(screenshot, "assets/icons/event_choice_1.png", confidence=0.45, region=event_choice_region)
            
            if event_matches:
                print("[INFO] Event detected, analyzing choices...")
                choice_number, success, choice_locations = handle_event_choice()
                if success:
                    click_success = click_event_choice(choice_number, choice_locations)
                    if click_success:
                        print(f"[INFO] Successfully selected choice {choice_number}")
                        time.sleep(0.5)
                        continue
                    else:
                        print("[WARNING] Failed to click event choice, falling back to top choice")
                        # Fallback using existing match
                        x, y, w, h = event_matches[0]
                        center = (x + w//2, y + h//2)
                        tap(center[0], center[1])
                        continue
                else:
                    # If no choice locations were returned, skip clicking and continue loop
                    if not choice_locations:
                        debug_print("[DEBUG] Skipping event click due to no visible choices after stabilization")
                        continue
                    print("[WARNING] Event analysis failed, falling back to top choice")
                    # Fallback using existing match
                    x, y, w, h = event_matches[0]
                    center = (x + w//2, y + h//2)
                    tap(center[0], center[1])
                    continue
            else:
                debug_print("[DEBUG] No events found")
        except Exception as e:
            print(f"[ERROR] Event handling error: {e}")

        # Check inspiration button
        debug_print("[DEBUG] Checking for inspiration...")
        inspiration_matches = match_template(screenshot, "assets/buttons/inspiration_btn.png", confidence=0.5)
        if inspiration_matches:
            x, y, w, h = inspiration_matches[0]
            center = (x + w//2, y + h//2)
            print("[INFO] Inspiration found.")
            tap(center[0], center[1])
            continue

        # Check next button
        debug_print("[DEBUG] Checking for next button...")
        next_matches = match_template(screenshot, "assets/buttons/next_btn.png", confidence=0.6)
        if next_matches:
            x, y, w, h = next_matches[0]
            center = (x + w//2, y + h//2)
            debug_print(f"[DEBUG] Clicking next_btn.png at position {center}")
            tap(center[0], center[1])
            continue

        # Check cancel button
        debug_print("[DEBUG] Checking for cancel button...")
        cancel_matches = match_template(screenshot, "assets/buttons/cancel_btn.png", confidence=0.6)
        if cancel_matches:
            x, y, w, h = cancel_matches[0]
            center = (x + w//2, y + h//2)
            debug_print(f"[DEBUG] Clicking cancel_btn.png at position {center}")
            tap(center[0], center[1])
            continue

        # Check if current menu is in career lobby
        debug_print("[DEBUG] Checking if in career lobby...")
        tazuna_hint = locate_on_screen("assets/ui/tazuna_hint.png", confidence=0.8)

        if tazuna_hint is None:
            print("[INFO] Should be in career lobby.")
            continue

        debug_print("[DEBUG] Confirmed in career lobby")
        time.sleep(0.5)

        # Check if there is debuff status
        debug_print("[DEBUG] Checking for debuff status...")
        # Use match_template to get full bounding box for brightness check
        screenshot = take_screenshot()
        infirmary_matches = match_template(screenshot, "assets/buttons/infirmary_btn2.png", confidence=0.9)
        
        if infirmary_matches:
            debuffed_box = infirmary_matches[0]  # Get first match (x, y, w, h)
            x, y, w, h = debuffed_box
            center_x, center_y = x + w//2, y + h//2
            
            # Check if the button is actually active (bright) or just disabled (dark)
            if is_infirmary_active_adb(debuffed_box):
                tap(center_x, center_y)
                print("[INFO] Character has debuff, go to infirmary instead.")
                continue
            else:
                debug_print("[DEBUG] Infirmary button found but is disabled (dark)")
        else:
            debug_print("[DEBUG] No infirmary button detected")

        # Get current state
        debug_print("[DEBUG] Getting current game state...")
        mood = check_mood()
        mood_index = MOOD_LIST.index(mood)
        minimum_mood = MOOD_LIST.index(MINIMUM_MOOD)
        turn = check_turn()
        year = check_current_year()
        goal_data = check_goal_name_with_g1_requirement()
        criteria_text = check_criteria()
        
        print("\n=======================================================================================\n")
        print(f"Year: {year}")
        print(f"Mood: {mood}")
        print(f"Turn: {turn}")
        print(f"Goal Name: {goal_data['text']}")
        print(f"Status: {criteria_text}")
        print(f"G1 Race Requirement: {goal_data['requires_g1_races']}")
        debug_print(f"[DEBUG] Mood index: {mood_index}, Minimum mood index: {minimum_mood}")
        
        # Check energy bar before proceeding with training decisions
        debug_print("[DEBUG] Checking energy bar...")
        energy_percentage = check_energy_bar()
        min_energy = config.get("min_energy", 30)
        
        print(f"Energy: {energy_percentage:.1f}% (Minimum: {min_energy}%)")
        
        # Check if goals criteria are NOT met AND it is not Pre-Debut AND turn is less than 10
        # Prioritize racing when criteria are not met to help achieve goals
        debug_print("[DEBUG] Checking goal criteria...")
        goal_analysis = check_goal_criteria({"text": criteria_text, "requires_g1_races": goal_data['requires_g1_races']}, year, turn)
        
        if goal_analysis["should_prioritize_racing"]:
            if goal_analysis["should_prioritize_g1_races"]:
                print(f"Decision: Criteria not met - Prioritizing G1 races to meet goals")
                race_found = do_race(prioritize_g1=True)
                if race_found:
                    print("Race Result: Found G1 Race")
                    continue
                else:
                    print("Race Result: No G1 Race Found")
                    # If there is no G1 race found, go back and do training instead
                    click("assets/buttons/back_btn.png", text="[INFO] G1 race not found. Proceeding to training.")
                    time.sleep(0.5)
            else:
                print(f"Decision: Criteria not met - Prioritizing normal races to meet goals")
                race_found = do_race()
                if race_found:
                    print("Race Result: Found Race")
                    continue
                else:
                    print("Race Result: No Race Found")
                    # If there is no race found, go back and do training instead
                    click("assets/buttons/back_btn.png", text="[INFO] Race not found. Proceeding to training.")
                    time.sleep(0.5)
        else:
            print("Decision: Criteria met or conditions not suitable for racing")
            debug_print(f"[DEBUG] Racing not prioritized - Criteria met: {goal_analysis['criteria_met']}, Pre-debut: {goal_analysis['is_pre_debut']}, Turn < 10: {goal_analysis['turn_less_than_10']}")
        
        print("")

        # URA SCENARIO
        debug_print("[DEBUG] Checking for URA scenario...")
        if year == "Finale Season" and turn == "Race Day":
            print("[INFO] URA Finale")
            
            # Check skill points cap before URA race day (if enabled)
            enable_skill_check = config.get("enable_skill_point_check", True)
            
            if enable_skill_check:
                print("[INFO] URA Finale Race Day - Checking skill points cap...")
                check_skill_points_cap()
            
            # URA race logic would go here
            debug_print("[DEBUG] Starting URA race...")
            if click("assets/buttons/race_ura.png", minSearch=10):
                time.sleep(0.5)
                # Click race button 2 times after entering race menu
                for i in range(2):
                    if click("assets/buttons/race_btn.png", minSearch=2):
                        debug_print(f"[DEBUG] Successfully clicked race button {i+1}/2")
                        time.sleep(1)
                    else:
                        debug_print(f"[DEBUG] Race button not found on attempt {i+1}/2")
            
            race_prep()
            time.sleep(1)
            # If race failed screen appears, handle retry before proceeding
            handle_race_retry_if_failed()
            after_race()
            continue
        else:
            debug_print("[DEBUG] Not URA scenario")

        # If calendar is race day, do race
        debug_print("[DEBUG] Checking for race day...")
        if turn == "Race Day" and year != "Finale Season":
            print("[INFO] Race Day.")
            race_day()
            continue
        else:
            debug_print("[DEBUG] Not race day")

        # Mood check
        debug_print("[DEBUG] Checking mood...")
        if mood_index < minimum_mood:
            # Check if energy is too high (>90%) before doing recreation
            if energy_percentage > 90:
                debug_print(f"[DEBUG] Mood too low ({mood_index} < {minimum_mood}) but energy too high ({energy_percentage:.1f}% > 90%), skipping recreation")
                print(f"[INFO] Mood is low but energy is too high ({energy_percentage:.1f}% > 90%), skipping recreation")
            else:
                debug_print(f"[DEBUG] Mood too low ({mood_index} < {minimum_mood}), doing recreation")
                print("[INFO] Mood is low, trying recreation to increase mood")
                do_recreation()
                continue
        else:
            debug_print(f"[DEBUG] Mood is good ({mood_index} >= {minimum_mood})")

        # If Prioritize G1 Race is true, check G1 race every turn
        debug_print(f"[DEBUG] Checking G1 race priority: {PRIORITIZE_G1_RACE}")
        if PRIORITIZE_G1_RACE and not is_pre_debut_year(year) and is_racing_available(year):
            print("G1 Race Check: Looking for G1 race...")
            g1_race_found = do_race(PRIORITIZE_G1_RACE)
            if g1_race_found:
                print("G1 Race Result: Found G1 Race")
                continue
            else:
                print("G1 Race Result: No G1 Race Found")
                # If there is no G1 race, go back and do training instead
                click("assets/buttons/back_btn.png", text="[INFO] G1 race not found. Proceeding to training.")
                time.sleep(0.5)
        else:
            debug_print("[DEBUG] G1 race priority disabled or conditions not met")
        
        # Check training button
        debug_print("[DEBUG] Going to training...")
        
        # Check energy before proceeding with training
        if energy_percentage < min_energy:
            print(f"[INFO] Energy too low ({energy_percentage:.1f}% < {min_energy}%), skipping training and going to rest")
            do_rest()
            continue
            
        if not go_to_training():
            print("[INFO] Training button is not found.")
            continue

        # Last, do training
        debug_print("[DEBUG] Analyzing training options...")
        time.sleep(0.5)
        results_training = check_training()
        
        debug_print("[DEBUG] Deciding best training action using scoring algorithm...")
        
        # Load config for scoring thresholds
        try:
            with open("config.json", "r", encoding="utf-8") as file:
                training_config = json.load(file)
        except Exception as e:
            print(f"Error loading config: {e}")
            training_config = {"maximum_failure": 15, "min_score": 1.0, "min_wit_score": 1.0, "priority_stat": ["spd", "sta", "wit", "pwr", "guts"]}
        
        # Use new scoring algorithm to choose best training
        from core.state_adb import choose_best_training
        best_training = choose_best_training(results_training, training_config)
        
        if best_training:
            debug_print(f"[DEBUG] Scoring algorithm selected: {best_training.upper()} training")
            print(f"[INFO] Selected {best_training.upper()} training based on scoring algorithm")
            do_train(best_training)
        else:
            debug_print("[DEBUG] No suitable training found based on scoring criteria")
            print("[INFO] No suitable training found based on scoring criteria.")
            
            # Check if we should prioritize racing when no good training is available
            do_race_when_bad_training = training_config.get("do_race_when_bad_training", True)
            
            if do_race_when_bad_training:
                # Check if all training options have failure rates above maximum
                from core.logic import all_training_unsafe
                max_failure = training_config.get('maximum_failure', 15)
                debug_print(f"[DEBUG] Checking if all training options have failure rate > {max_failure}%")
                debug_print(f"[DEBUG] Training results: {[(k, v['failure']) for k, v in results_training.items()]}")
                
                if all_training_unsafe(results_training, max_failure):
                    debug_print(f"[DEBUG] All training options have failure rate > {max_failure}%")
                    print(f"[INFO] All training options have failure rate > {max_failure}%. Skipping race and choosing to rest.")
                    do_rest()
                else:
                    # Check if racing is available (no races in July/August)
                    if not is_racing_available(year):
                        debug_print("[DEBUG] Racing not available (summer break)")
                        print("[INFO] July/August detected. No races available during summer break. Choosing to rest.")
                        do_rest()
                    else:
                        print("[INFO] Prioritizing race due to insufficient training scores.")
                        print("Training Race Check: Looking for race due to insufficient training scores...")
                        race_found = do_race()
                        if race_found:
                            print("Training Race Result: Found Race")
                            continue
                        else:
                            print("Training Race Result: No Race Found")
                            # If no race found, go back and rest
                            click("assets/buttons/back_btn.png", text="[INFO] Race not found. Proceeding to rest.")
                            time.sleep(0.5)
                            do_rest()
            else:
                print("[INFO] Race prioritization disabled. Choosing to rest.")
                do_rest()
        
        debug_print("[DEBUG] Waiting before next iteration...")
        time.sleep(1)

def is_pre_debut_year(year):
    return ("Pre-Debut" in year or "PreDebut" in year or 
            "PreeDebut" in year or "Pre" in year)

def check_goal_criteria(criteria_data, year, turn):
    """
    Check if goal criteria are met and determine if racing should be prioritized.
    
    Args:
        criteria_data (dict): The criteria data from OCR with text and G1 race requirements
        year (str): Current year text
        turn (str/int): Current turn number or text
    
    Returns:
        dict: Dictionary containing criteria analysis and decision
    """
    # Extract criteria text and G1 race requirements
    criteria_text = criteria_data.get("text", "")
    requires_g1_races = criteria_data.get("requires_g1_races", False)
    
    # Check if goals criteria are met
    criteria_met = (criteria_text.split(" ")[0] == "criteria" or 
                    "criteria met" in criteria_text.lower() or 
                    "goal achieved" in criteria_text.lower())
    
    # Check if it's pre-debut year
    is_pre_debut = is_pre_debut_year(year)
    
    # Check if turn is a number before comparing
    turn_is_number = isinstance(turn, int) or (isinstance(turn, str) and turn.isdigit())
    turn_less_than_10 = turn < 10 if turn_is_number else False
    
    # Determine if racing should be prioritized (when criteria not met, not pre-debut, turn < 10)
    should_prioritize_racing = not criteria_met and not is_pre_debut and turn_less_than_10
    
    # Determine if G1 races should be prioritized (when racing should be prioritized AND G1 races are required)
    should_prioritize_g1_races = should_prioritize_racing and requires_g1_races
    
    debug_print(f"[DEBUG] Year: '{year}', Criteria met: {criteria_met}, Pre-debut: {is_pre_debut}, Turn < 10: {turn_less_than_10}")
    debug_print(f"[DEBUG] G1 races required: {requires_g1_races}, Should prioritize G1: {should_prioritize_g1_races}")
    
    return {
        "criteria_met": criteria_met,
        "is_pre_debut": is_pre_debut,
        "turn_less_than_10": turn_less_than_10,
        "should_prioritize_racing": should_prioritize_racing,
        "requires_g1_races": requires_g1_races,
        "should_prioritize_g1_races": should_prioritize_g1_races
    } 