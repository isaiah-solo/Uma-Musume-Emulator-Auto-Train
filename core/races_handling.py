import time
import json
import random
from PIL import ImageStat

from utils.adb_recognizer import locate_on_screen, match_template
from utils.adb_input import tap, triple_click, long_press, tap_on_image
from utils.adb_screenshot import take_screenshot
from utils.template_matching import wait_for_image
from utils.log import debug_print

# Load config for RETRY_RACE
try:
    with open("config.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
        RETRY_RACE = config.get("retry_race", True)
except Exception:
    RETRY_RACE = True

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

def is_pre_debut_year(year):
    return ("Pre-Debut" in year or "PreDebut" in year or 
            "PreeDebut" in year or "Pre" in year)

def do_race(prioritize_g1=False):
    """Perform race action"""
    debug_print(f"[DEBUG] Performing race action (G1 priority: {prioritize_g1})...")
    tap_on_image("assets/buttons/races_btn.png", min_search=10)
    time.sleep(1.2)
    tap_on_image("assets/buttons/ok_btn.png", confidence=0.5, min_search=1)

    found = race_select(prioritize_g1=prioritize_g1)
    if found:
        debug_print("[DEBUG] Race found and selected, proceeding to race preparation")
        race_prep()
        time.sleep(1)
        after_race()
        return True
    else:
        debug_print("[DEBUG] No race found, going back")
        tap_on_image("assets/buttons/back_btn.png", min_search=0.7)
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
    if tap_on_image("assets/buttons/race_day_btn.png", min_search=10):
        debug_print("[DEBUG] Race day button clicked, clicking OK button...")
        time.sleep(1.3)
        tap_on_image("assets/buttons/ok_btn.png", confidence=0.5, min_search=2)
        time.sleep(1.0)  # Increased wait time
        
        # Try to find and click race button with better error handling
        race_clicked = False
        for attempt in range(3):  # Try up to 3 times
            if tap_on_image("assets/buttons/race_btn.png", confidence=0.7, min_search=1):
                debug_print(f"[DEBUG] Race button clicked successfully, attempt {attempt + 1}")
                time.sleep(0.5)  # Wait between clicks
                
                # Click race button twice like in race_select
                for j in range(2):
                    if tap_on_image("assets/buttons/race_btn.png", confidence=0.7, min_search=1):
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
            debug_print("[DEBUG] Failed to click race button after all attempts")
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
                    region = (x, y, w, h)
                    match_aptitude = locate_match_track_with_brightness(confidence=0.6, region=region, brightness_threshold=180.0)
                    if match_aptitude:
                        debug_print(f"[DEBUG] G1 race found at {match_aptitude}")
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
            debug_print(f"[DEBUG] Swiping up to find races (attempt {scroll+1}/4)...")
            swipe(540, 1500, 540, 500, duration_ms=500)
            time.sleep(1.0)
            
            if prioritize_g1:
                debug_print(f"[DEBUG] Looking for G1 race after swipe {scroll+1}")
                screenshot = take_screenshot()
                race_cards = match_template(screenshot, "assets/ui/g1_race.png", confidence=0.9)
                if race_cards:
                    debug_print(f"[DEBUG] Found {len(race_cards)} G1 race card(s) after swipe {scroll+1}")
                    for x, y, w, h in race_cards:
                        region = (x, y, w, h)
                        match_aptitude = locate_match_track_with_brightness(confidence=0.6, region=region, brightness_threshold=180.0)
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
    try:
        # Load config to get expected strategy
        with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
        
        expected_strategy = config.get("race_strategy", "Front")
        debug_print(f"[DEBUG] Expected race strategy: {expected_strategy}")
        
        # Take screenshot and crop the strategy region
        screenshot = take_screenshot()
        strategy_region = screenshot.crop(region)
        
        # Use OCR to read the current strategy
        import pytesseract
        import numpy as np
        
        # Convert PIL image to numpy array for OCR
        strategy_img = np.array(strategy_region)
        
        # Use OCR to extract text
        strategy_text = pytesseract.image_to_string(strategy_img, config='--oem 3 --psm 6').strip()
        debug_print(f"[DEBUG] Current race strategy: '{strategy_text}'")
        
        # Check if the current strategy matches the expected strategy
        if expected_strategy.lower() in strategy_text.lower():
            debug_print(f"[DEBUG] Race strategy is already correct: {strategy_text}")
            return True
        else:
            debug_print(f"[DEBUG] Race strategy mismatch. Expected: {expected_strategy}, Current: {strategy_text}")
            # Try to change the strategy
            return change_strategy_before_race(expected_strategy)
            
    except Exception as e:
        debug_print(f"[DEBUG] Error during strategy check: {e}")
        return False

def change_strategy_before_race(expected_strategy: str) -> bool:
    """Change race strategy to match config before race."""
    try:
        debug_print(f"[DEBUG] Attempting to change race strategy to: {expected_strategy}")
        
        # Strategy button coordinates (approximate)
        strategy_btn = (660, 974)
        
        # Click the strategy button to open strategy selection
        tap(strategy_btn[0], strategy_btn[1])
        time.sleep(1.0)
        
        # Strategy option coordinates based on expected strategy
        strategy_coords = {
            "Front": (660, 800),
            "Middle": (660, 900),
            "Back": (660, 1000),
            "Front Runner": (660, 800),
            "Stalker": (660, 900),
            "Closer": (660, 1000)
        }
        
        if expected_strategy in strategy_coords:
            target_coords = strategy_coords[expected_strategy]
            debug_print(f"[DEBUG] Clicking strategy option at {target_coords}")
            tap(target_coords[0], target_coords[1])
            time.sleep(0.5)
            
            # Verify the strategy was changed
            return check_strategy_before_race()
        else:
            debug_print(f"[DEBUG] Unknown strategy: {expected_strategy}")
            return False
            
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
    """
    Handle race failures and retries.
    
    Recognizes failure by detecting `assets/icons/clock.png` on screen.
    If `retry_race` is true in config, continuously taps `assets/buttons/try_again.png`, waits 5s,
    and calls `race_prep()` again until success.
    Returns True if retries were performed, False otherwise.
    """
    try:
        if not RETRY_RACE:
            print("[INFO] retry_race is disabled. Stopping automation.")
            raise SystemExit(0)

        retry_count = 0
        
        while True:
            # Check for failure indicator (clock icon)
            clock = locate_on_screen("assets/icons/clock.png", confidence=0.8)
            # Check for success indicator (next button)
            next_btn = locate_on_screen("assets/buttons/next_btn.png", confidence=0.8)
            
            if next_btn:
                if retry_count > 0:
                    print(f"[INFO] Race succeeded after {retry_count} retry attempts!")
                else:
                    print("[INFO] Race succeeded on first attempt!")
                return retry_count > 0
                
            if not clock:
                # No clock and no next button - wait a bit and check again
                time.sleep(1)
                continue

            retry_count += 1
            print(f"[INFO] Race failed detected (clock icon). Retry attempt {retry_count}")

            # Try to click Try Again button
            try_again = locate_on_screen("assets/buttons/try_again.png", confidence=0.8)
            if try_again:
                print(f"[INFO] Clicking Try Again button for retry {retry_count}")
                tap(try_again[0], try_again[1])
                time.sleep(5)  # Wait 5 seconds for retry
                
                # Call race_prep() again for the retry
                race_prep()
                time.sleep(1)
            else:
                print("[WARNING] Try Again button not found, cannot retry")
                return False
                
    except Exception as e:
        print(f"[ERROR] Error during race retry handling: {e}")
        return False

def after_race():
    """Handle post-race actions"""
    debug_print("[DEBUG] Handling post-race actions...")
    
    # Try to click first next button with fallback mechanism
    if not tap_on_image("assets/buttons/next_btn.png", confidence=0.7, min_search=10):
        debug_print("[DEBUG] First next button not found after 10 attempts, clicking middle of screen as fallback...")
        tap(540, 960)  # Click middle of screen (1080x1920 resolution)
        time.sleep(1)
        debug_print("[DEBUG] Retrying next button search after screen tap...")
        tap_on_image("assets/buttons/next_btn.png", confidence=0.7, min_search=10)
        time.sleep(1)
    
    time.sleep(4)
    
    # Try to click second next button with fallback mechanism
    if not tap_on_image("assets/buttons/next2_btn.png", confidence=0.7, min_search=10):
        time.sleep(1)
        debug_print("[DEBUG] Retrying next2 button search after screen tap...")
        tap_on_image("assets/buttons/next2_btn.png", confidence=0.7, min_search=10)
    
    debug_print("[DEBUG] Post-race actions complete")

# check_skill_points_cap is imported from core.state_adb

def swipe(start_x, start_y, end_x, end_y, duration_ms=500):
    """Perform swipe gesture"""
    from utils.adb_input import swipe as adb_swipe
    adb_swipe(start_x, start_y, end_x, end_y, duration_ms)
