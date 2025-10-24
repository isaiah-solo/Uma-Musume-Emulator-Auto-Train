import time
from PIL import ImageStat

from core.screens.claw_machine_adb import do_claw_machine, is_on_claw_machine_screen
from core.screens.race_adb import after_race, do_race, handle_race_retry_if_failed, is_g1_racing_available, race_day, race_prep
from utils.adb_recognizer import locate_on_screen, match_template
from utils.adb_input import tap, triple_click
from utils.adb_screenshot import take_screenshot
from utils.constants_phone import (
    MOOD_LIST, SUPPORT_CARD_ICON_REGION
)
from core.config import Config

# Import ADB state and logic modules
from core.state_adb import check_support_card, check_failure, check_turn, check_mood, check_current_year, check_criteria, check_skill_points_cap, check_skills_are_available, check_goal_name, check_goal_name_with_g1_requirement, check_hint, calculate_training_score, choose_best_training, check_current_stats, check_energy_bar

# Import event handling functions
from core.event_handling import click, handle_event_choice, click_event_choice

# Load config and check debug mode
config = Config.load()
DEBUG_MODE = Config.get("debug_mode", False)
RETRY_RACE = Config.get("retry_race", True)

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

def is_infirmary_active_adb(screenshot, button_location):
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

def go_to_training():
    """Go to training screen"""
    debug_print("[DEBUG] Going to training screen...")
    time.sleep(1)
    return click("assets/buttons/training_btn.png", minSearch=10)

def check_training():
    """Check training results using fixed coordinates, collecting support counts,
    bond levels and hint presence in one hover pass before computing failure rates."""
    debug_print("[DEBUG] Checking training options...")

    # Check skill points cap before race day (if enabled)
    config = Config.load()
    
    # Fixed coordinates for each training type
    training_coords_base = {
        "spd": (165, 1557),
        "sta": (357, 1563),
        "pwr": (546, 1557),
        "guts": (735, 1566),
        "wit": (936, 1572)
    }

    training_coords = {}
    for training in config.get('priority_stat'):
        training_coords[training] = training_coords_base[training]

    results = {}
    high_score_found = False

    for key, coords in training_coords.items():
        if high_score_found:
            results[key] = {
                "support": 0,
                "support_detail": {},
                "hint": False,
                "total_support": 0,
                "failure": 100,
                "confidence": 0.0,
                "score": 0
            }
            print(f"[INFO] Skipping {key.upper()} because high training score found")
            continue
            
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

        if score >= 2.0:
            high_score_found = True
        
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

def do_rest(main_screenshot):
    """Perform rest action"""
    debug_print("[DEBUG] Performing rest action...")
    print("[INFO] Performing rest action...")
    
    # Rest button is in the lobby, not on training screen
    # If we're on training screen, go back to lobby first
    back_btn = locate_on_screen(main_screenshot, "assets/buttons/back_btn.png", confidence=0.8)
    if back_btn:
        debug_print("[DEBUG] Going back to lobby to find rest button...")
        print("[INFO] Going back to lobby to find rest button...")
        from utils.adb_input import tap
        tap(back_btn[0], back_btn[1])
        time.sleep(1.0)  # Wait for lobby to load

    screenshot = take_screenshot()
    
    # Now look for rest buttons in the lobby
    rest_btn = locate_on_screen(screenshot, "assets/buttons/rest_btn.png", confidence=0.5)
    rest_summer_btn = locate_on_screen(screenshot, "assets/buttons/rest_summer_btn.png", confidence=0.5)
    
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

def do_recreation(screenshot):
    """Perform recreation action"""
    debug_print("[DEBUG] Performing recreation action...")
    recreation_btn = locate_on_screen(screenshot, "assets/buttons/recreation_btn.png", confidence=0.8)
    recreation_summer_btn = locate_on_screen(screenshot, "assets/buttons/rest_summer_btn.png", confidence=0.8)
    
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

def career_lobby():
    """Main career lobby loop"""
    # Load configuration
    config = Config.load()
    MINIMUM_MOOD = config["minimum_mood"]
    PRIORITIZE_G1_RACE = config["prioritize_g1_race"]

    # Global state
    bought_skills = {}

    # Program start
    while True:
        debug_print("\n[DEBUG] ===== Starting new loop iteration =====")
        
        # Batch UI check - take one screenshot and check multiple elements
        debug_print("[DEBUG] Performing batch UI element check...")
        screenshot = take_screenshot()
        
        # Check claw machine first (highest priority)
        debug_print("[DEBUG] Checking for claw machine...")
        if is_on_claw_machine_screen(screenshot):
            do_claw_machine(screenshot)
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
        tazuna_hint = locate_on_screen(screenshot, "assets/ui/tazuna_hint.png", confidence=0.8)

        if tazuna_hint is None:
            print("[INFO] Should be in career lobby.")
            continue

        debug_print("[DEBUG] Confirmed in career lobby")

        # Check if there is debuff status
        debug_print("[DEBUG] Checking for debuff status...")
        # Use match_template to get full bounding box for brightness check
        infirmary_matches = match_template(screenshot, "assets/buttons/infirmary_btn2.png", confidence=0.9)
        
        if infirmary_matches:
            debuffed_box = infirmary_matches[0]  # Get first match (x, y, w, h)
            x, y, w, h = debuffed_box
            center_x, center_y = x + w//2, y + h//2
            
            # Check if the button is actually active (bright) or just disabled (dark)
            if is_infirmary_active_adb(screenshot, debuffed_box):
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
                race_found = do_race(year, prioritize_g1=True)
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
                race_found = do_race(year)
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
                check_skill_points_cap(bought_skills)
            
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
            race_screenshot = take_screenshot()
            # If race failed screen appears, handle retry before proceeding
            handle_race_retry_if_failed(race_screenshot)
            after_race()
            continue
        else:
            debug_print("[DEBUG] Not URA scenario")

        # If calendar is race day, do race
        debug_print("[DEBUG] Checking for race day...")
        if turn == "Race Day" and year != "Finale Season":
            print("[INFO] Race Day.")
            race_day(bought_skills)
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
                do_recreation(screenshot)
                continue
        else:
            debug_print(f"[DEBUG] Mood is good ({mood_index} >= {minimum_mood})")

        # If Prioritize G1 Race is true, check G1 race every turn
        debug_print(f"[DEBUG] Checking G1 race priority: {PRIORITIZE_G1_RACE}")
        if PRIORITIZE_G1_RACE and not is_pre_debut_year(year) and is_racing_available(year) and is_g1_racing_available(year):
            print("G1 Race Check: Looking for G1 race...")
            g1_race_found = do_race(year, PRIORITIZE_G1_RACE)
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
            do_rest(screenshot)
            continue
            
        if not go_to_training():
            print("[INFO] Training button is not found.")
            continue

        # Last, do training
        debug_print("[DEBUG] Analyzing training options...")
        time.sleep(0.5)
        results_training = check_training()
        
        # Load config for scoring thresholds
        training_config = Config.load()
        
        debug_print("[DEBUG] Deciding best training action using scoring algorithm...")
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

            debug_print("[DEBUG] Going back from training screen...")
            click("assets/buttons/back_btn.png")
            
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
                    do_rest(screenshot)
                else:
                    # Check if racing is available (no races in July/August)
                    if not is_racing_available(year):
                        debug_print("[DEBUG] Racing not available (summer break)")
                        print("[INFO] July/August detected. No races available during summer break. Choosing to rest.")
                        do_rest(screenshot)
                    else:
                        print("[INFO] Prioritizing race due to insufficient training scores.")
                        print("Training Race Check: Looking for race due to insufficient training scores...")
                        race_found = do_race(year)
                        if race_found:
                            print("Training Race Result: Found Race")
                            continue
                        else:
                            print("Training Race Result: No Race Found")
                            # If no race found, go back and rest
                            click("assets/buttons/back_btn.png", text="[INFO] Race not found. Proceeding to rest.")
                            time.sleep(0.5)
                            do_rest(screenshot)
            else:
                print("[INFO] Race prioritization disabled. Choosing to rest.")
                do_rest(screenshot)
        
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