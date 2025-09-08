import time
import json
import os
import random
import sys
from PIL import ImageStat

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

from utils.recognizer import locate_on_screen, locate_all_on_screen, is_image_on_screen, match_template, max_match_confidence
from utils.input import tap, triple_click, long_press, tap_on_image
from utils.screenshot import take_screenshot, enhanced_screenshot, capture_region
from utils.constants_phone import (
    MOOD_LIST, EVENT_REGION, RACE_CARD_REGION, SUPPORT_CARD_ICON_REGION
)

# Import ADB state and logic modules
from core.state import check_turn, check_mood, check_current_year, check_criteria, check_skill_points_cap, check_goal_name, check_current_stats, check_energy_bar

# Import event handling functions
from core.event_handling import count_event_choices, load_event_priorities, analyze_event_options, generate_event_variations, search_events, handle_event_choice, click_event_choice

# Import training handling functions
from core.training_handling import go_to_training, check_training, do_train, check_support_card, check_failure, check_hint, choose_best_training, calculate_training_score

# Import race handling functions
from core.races_handling import (
    find_and_do_race, do_custom_race, race_day,check_strategy_before_race,
    change_strategy_before_race, race_prep, handle_race_retry_if_failed,
    after_race, is_racing_available, is_pre_debut_year,
)

# Load config and check debug mode
with open("config.json", "r", encoding="utf-8") as config_file:
    config = json.load(config_file)
    DEBUG_MODE = config.get("debug_mode", False)
    RETRY_RACE = config.get("retry_race", True)

from utils.log import debug_print
from utils.template_matching import deduplicated_matches, wait_for_image

def is_infirmary_active_adb(button_location, screenshot=None):
    """
    Check if the infirmary button is active (bright) or disabled (dark).
    Args:
        button_location: tuple (x, y, w, h) of the button location
        screenshot: Optional PIL Image. If None, takes a new screenshot.
    Returns:
        bool: True if button is active (bright), False if disabled (dark)
    """
    try:
        x, y, w, h = button_location
        
        # Use provided screenshot or take new one if not provided
        if screenshot is None:
            from utils.screenshot import take_screenshot
            screenshot = take_screenshot()
        
        # Crop the button region from the screenshot
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
    time.sleep(1)
    
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

def do_rest():
    """Perform rest action"""
    debug_print("[DEBUG] Performing rest action...")
    print("[INFO] Performing rest action...")
    
    # Rest button is in the lobby, not on training screen
    # If we're on training screen, go back to lobby first
    from utils.recognizer import locate_on_screen
    back_btn = locate_on_screen("assets/buttons/back_btn.png", confidence=0.8)
    if back_btn:
        debug_print("[DEBUG] Going back to lobby to find rest button...")
        print("[INFO] Going back to lobby to find rest button...")
        from utils.input import tap
        tap(back_btn[0], back_btn[1])
        time.sleep(1.0)  # Wait for lobby to load
    tazuna_hint = locate_on_screen("assets/ui/tazuna_hint.png", confidence=0.7)
    if not tazuna_hint:
        debug_print("[DEBUG] tazuna_hint.png not found, taking screenshot again to ensure we are in the lobby...")
        time.sleep(0.7)
        # Take a new screenshot and try again
        from utils.screenshot import take_screenshot
        take_screenshot()
        tazuna_hint = locate_on_screen("assets/ui/tazuna_hint.png", confidence=0.7)
        if not tazuna_hint:
            debug_print("[WARNING] Still not in lobby after retrying screenshot. Rest button search may fail.")
    # Now look for rest buttons in the lobby
    rest_btn = locate_on_screen("assets/buttons/rest_btn.png", confidence=0.5)
    rest_summer_btn = locate_on_screen("assets/buttons/rest_summer_btn.png", confidence=0.5)
    
    debug_print(f"[DEBUG] Rest button found: {rest_btn}")
    debug_print(f"[DEBUG] Summer rest button found: {rest_summer_btn}")
    
    if rest_btn:
        debug_print(f"[DEBUG] Clicking rest button at {rest_btn}")
        print(f"[INFO] Clicking rest button at {rest_btn}")
        from utils.input import tap
        tap(rest_btn[0], rest_btn[1])
        debug_print("[DEBUG] Clicked rest button")
        print("[INFO] Rest button clicked")
    elif rest_summer_btn:
        debug_print(f"[DEBUG] Clicking summer rest button at {rest_summer_btn}")
        print(f"[INFO] Clicking summer rest button at {rest_summer_btn}")
        from utils.input import tap
        tap(rest_summer_btn[0], rest_summer_btn[1])
        debug_print("[DEBUG] Clicked summer rest button")
        print("[INFO] Summer rest button clicked")
    else:
        debug_print("[DEBUG] No rest button found in lobby")
        print("[WARNING] No rest button found in lobby")
    time.sleep(3)

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

def career_lobby():
    """Main career lobby loop"""
    # Use existing config loaded at module level
    MINIMUM_MOOD = config.get("minimum_mood", "GREAT")

    # Program start
    while True:
        debug_print("\n[DEBUG] ===== Starting new loop iteration =====")
        
        # Take screenshot first for all checks
        debug_print("[DEBUG] Taking screenshot for UI element checks...")
        screenshot = take_screenshot()
        
        # Check for career restart first (highest priority) - quick check only
        debug_print("[DEBUG] Quick check for Complete Career screen...")
        try:
            # Quick check for Complete Career button without importing full module
            complete_career_matches = match_template(screenshot, "assets/buttons/complete_career.png", confidence=0.8)
            if complete_career_matches:
                print("[INFO] Complete Career screen detected - starting restart workflow")
                from core.restart_career import career_lobby_check
                should_continue = career_lobby_check(screenshot)
                if not should_continue:
                    print("[INFO] Career restart workflow completed - stopping bot")
                    return False
        except Exception as e:
            print(f"[ERROR] Career restart check failed: {e}")
        
        # Batch UI check - use existing screenshot for multiple elements
        debug_print("[DEBUG] Performing batch UI element check...")
        
        # Check claw machine first (highest priority)
        debug_print("[DEBUG] Checking for claw machine...")
        claw_matches = match_template(screenshot, "assets/buttons/claw.png", confidence=0.8)
        if claw_matches:
            claw_machine()
            continue
        
        # Check OK button
        debug_print("[DEBUG] Checking for OK button...")
        ok_matches = match_template(screenshot, "assets/buttons/ok_btn.png", confidence=0.8)
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
            event_matches = match_template(screenshot, "assets/icons/event_choice_1.png", confidence=0.7, region=event_choice_region)
            
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

        # Check cancel button
        debug_print("[DEBUG] Checking for cancel button...")
        cancel_matches = match_template(screenshot, "assets/buttons/cancel_lobby.png", confidence=0.8)
        if cancel_matches:
            x, y, w, h = cancel_matches[0]
            center = (x + w//2, y + h//2)
            debug_print(f"[DEBUG] Clicking cancel_btn.png at position {center}")
            tap(center[0], center[1])
            continue

        # Check next button
        debug_print("[DEBUG] Checking for next button...")
        next_matches = match_template(screenshot, "assets/buttons/next_btn.png", confidence=0.8)
        if next_matches:
            x, y, w, h = next_matches[0]
            center = (x + w//2, y + h//2)
            debug_print(f"[DEBUG] Clicking next_btn.png at position {center}")
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
        # Take a fresh screenshot after confirming lobby to ensure stable UI state
        debug_print("[DEBUG] Taking fresh screenshot after lobby confirmation...")
        screenshot = take_screenshot()

        # Check if there is debuff status
        debug_print("[DEBUG] Checking for debuff status...")
        # Use match_template to get full bounding box for brightness check
        infirmary_matches = match_template(screenshot, "assets/buttons/infirmary_btn2.png", confidence=0.9)
        
        if infirmary_matches:
            debuffed_box = infirmary_matches[0]  # Get first match (x, y, w, h)
            x, y, w, h = debuffed_box
            center_x, center_y = x + w//2, y + h//2
            
            # Check if the button is actually active (bright) or just disabled (dark)
            if is_infirmary_active_adb(debuffed_box, screenshot):
                tap(center_x, center_y)
                print("[INFO] Character has debuff, go to infirmary instead.")
                continue
            else:
                debug_print("[DEBUG] Infirmary button found but is disabled (dark)")
        else:
            debug_print("[DEBUG] No infirmary button detected")

        # Get current state
        debug_print("[DEBUG] Getting current game state...")
        mood = check_mood(screenshot)
        mood_index = MOOD_LIST.index(mood)
        minimum_mood = MOOD_LIST.index(MINIMUM_MOOD)
        turn = check_turn(screenshot)
        year = check_current_year(screenshot)
        goal_data = check_goal_name(screenshot)
        criteria_text = check_criteria(screenshot)
        
        log_and_flush("", "INFO")
        log_and_flush("=== GAME STATUS ===", "INFO")
        log_and_flush(f"Year: {year}", "INFO")
        log_and_flush(f"Mood: {mood}", "INFO")
        log_and_flush(f"Turn: {turn}", "INFO")
        log_and_flush(f"Goal Name: {goal_data}", "INFO")
        log_and_flush(f"Status: {criteria_text}", "INFO")

        debug_print(f"[DEBUG] Mood index: {mood_index}, Minimum mood index: {minimum_mood}")
        
        # Check energy bar before proceeding with training decisions
        debug_print("[DEBUG] Checking energy bar...")
        energy_percentage = check_energy_bar(screenshot)
        min_energy = config.get("min_energy", 30)
        
        log_and_flush(f"Energy: {energy_percentage:.1f}% (Minimum: {min_energy}%)", "INFO")
        
        # Get and display current stats
        try:
            from core.state import check_current_stats
            current_stats = check_current_stats(screenshot)
            stats_str = f"SPD: {current_stats.get('spd', 0)}, STA: {current_stats.get('sta', 0)}, PWR: {current_stats.get('pwr', 0)}, GUTS: {current_stats.get('guts', 0)}, WIT: {current_stats.get('wit', 0)}"
            log_and_flush(f"Current stats: {stats_str}", "INFO")
        except Exception as e:
            debug_print(f"[DEBUG] Could not get current stats: {e}")
        
        # Check if goals criteria are NOT met AND it is not Pre-Debut AND turn is less than 10
        # Prioritize racing when criteria are not met to help achieve goals
        debug_print("[DEBUG] Checking goal criteria...")
        goal_analysis = check_goal_criteria({"text": criteria_text}, year, turn)
        
        if goal_analysis["should_prioritize_racing"]:
            print(f"Decision: Criteria not met - Prioritizing races to meet goals")
            race_found = find_and_do_race()
            if race_found:
                print("Race Result: Found Race")
                continue
            else:
                print("Race Result: No Race Found")
                # If there is no race found, go back and do training instead
                tap_on_image("assets/buttons/back_btn.png", text="[INFO] Race not found. Proceeding to training.")
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
                check_skill_points_cap(screenshot)
            
            # URA race logic would go here
            debug_print("[DEBUG] Starting URA race...")
            if tap_on_image("assets/buttons/race_ura.png", min_search=10):
                time.sleep(0.5)
                # Click race button 2 times after entering race menu
                for i in range(2):
                    if tap_on_image("assets/buttons/race_btn.png", min_search=2):
                        debug_print(f"[DEBUG] Successfully clicked race button {i+1}/2")
                        time.sleep(0.5)
                    else:
                        debug_print(f"[DEBUG] Race button not found on attempt {i+1}/2")
            
            race_prep()
            # time.sleep(1)
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

        # Check for custom race (bypasses all criteria) - only if enabled in config
        debug_print("[DEBUG] Checking if custom race is enabled...")
        do_custom_race_enabled = config.get("do_custom_race", False)
        
        if do_custom_race_enabled:
            debug_print("[DEBUG] Custom race is enabled, checking for custom race...")
            custom_race_found = do_custom_race()
            if custom_race_found:
                print("[INFO] Custom race executed successfully")
                continue
            else:
                debug_print("[DEBUG] No custom race found or executed")
        else:
            debug_print("[DEBUG] Custom race is disabled in config")

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

        # Check training button
        debug_print("[DEBUG] Going to training...")
        
        # Check energy before proceeding with training
        if energy_percentage < min_energy:
            log_and_flush(f"Energy too low ({energy_percentage:.1f}% < {min_energy}%), skipping training and going to rest", "WARNING")
            do_rest()
            continue
            
        if not go_to_training():
            log_and_flush("Training button is not found.", "WARNING")
            continue

        # Last, do training
        debug_print("[DEBUG] Analyzing training options...")
        time.sleep(0.5)
        results_training = check_training()
        
        debug_print("[DEBUG] Deciding best training action using scoring algorithm...")
        
        # Use existing config for scoring thresholds
        training_config = {
            "maximum_failure": config.get("maximum_failure", 15),
            "min_score": config.get("min_score", 1.0),
            "min_wit_score": config.get("min_wit_score", 1.0),
            "priority_stat": config.get("priority_stat", ["spd", "sta", "wit", "pwr", "guts"])
        }

        # If race fallback is disabled, ignore min_score entirely from the start
        do_race_when_bad_training_flag = config.get("do_race_when_bad_training", True)
        if not do_race_when_bad_training_flag:
            training_config["min_score"] = 0.0
        
        # Use new scoring algorithm to choose best training (with stat cap filtering)
        debug_print(f"[DEBUG] Choosing best training with stat cap filtering. Current stats: {current_stats}")
        best_training = choose_best_training(results_training, training_config, current_stats)
        
        if best_training:
            debug_print(f"[DEBUG] Scoring algorithm selected: {best_training.upper()} training")
            print(f"[INFO] Selected {best_training.upper()} training based on scoring algorithm")
            do_train(best_training)
        else:
            debug_print("[DEBUG] No suitable training found based on scoring criteria")
            print("[INFO] No suitable training found based on scoring criteria.")
            
            # Check if we should prioritize racing when no good training is available
            do_race_when_bad_training = do_race_when_bad_training_flag
            
            if do_race_when_bad_training:
                # Check if all training options have failure rates above maximum
                from core.logic import all_training_unsafe
                max_failure = training_config.get('maximum_failure', 15)
                debug_print(f"[DEBUG] Checking if all training options have failure rate > {max_failure}%")
                debug_print(f"[DEBUG] Training results: {[(k, v['failure']) for k, v in results_training.items()]}")
                
                if all_training_unsafe(results_training, max_failure):
                    debug_print(f"[DEBUG] All training options have failure rate > {max_failure}%")
                    # If all trainings are unsafe AND wit score is low, rest; otherwise try a relaxed training
                    wit_score = results_training.get('wit', {}).get('score', 0)
                    if wit_score < 1.0:
                        print(f"[INFO] All training options unsafe and WIT score < 1.0. Choosing to rest.")
                        do_rest()
                        continue
                    else:
                        # Try to pick a training with relaxed thresholds despite high failure context
                        relaxed_config = dict(training_config)
                        relaxed_config.update({
                            'min_score': 0.0,
                            'min_wit_score': 0.0
                        })
                        fallback_training = choose_best_training(results_training, relaxed_config, current_stats)
                        if fallback_training:
                            print(f"[INFO] Proceeding with training ({fallback_training.upper()}) despite poor options (relaxed selection)")
                            do_train(fallback_training)
                            continue
                        else:
                            print("[INFO] No viable training even after relaxed selection. Choosing to rest.")
                            do_rest()
                            continue
                else:
                    # Check if racing is available (no races in July/August)
                    if not is_racing_available(year):
                        debug_print("[DEBUG] Racing not available (summer break)")
                        print("[INFO] July/August detected. No races available during summer break. Trying training instead.")
                        # Try training with relaxed thresholds
                        relaxed_config = dict(training_config)
                        relaxed_config.update({
                            'min_score': 0.0,
                            'min_wit_score': 0.0
                        })
                        fallback_training = choose_best_training(results_training, relaxed_config, current_stats)
                        if fallback_training:
                            print(f"[INFO] Proceeding with training ({fallback_training.upper()}) due to no races")
                            do_train(fallback_training)
                            continue
                        else:
                            # If even relaxed cannot find, decide rest only if WIT score < 1.0, else do_rest as last resort
                            wit_score = results_training.get('wit', {}).get('score', 0)
                            if wit_score < 1.0:
                                print("[INFO] No viable training after relaxation and no races. Choosing to rest.")
                                do_rest()
                            else:
                                print("[INFO] No training selected after relaxation. Choosing to rest.")
                                do_rest()
                        
                    else:
                        print("[INFO] Prioritizing race due to insufficient training scores.")
                        print("Training Race Check: Looking for race due to insufficient training scores...")
                        race_found = find_and_do_race()
                        if race_found:
                            print("Training Race Result: Found Race")
                            continue
                        else:
                            print("Training Race Result: No Race Found")
                            # If no race found, go back and try training instead of resting by default
                            tap_on_image("assets/buttons/back_btn.png", text="[INFO] Race not found. Trying training instead.")
                            time.sleep(0.5)
                            # Try training with relaxed thresholds
                            relaxed_config = dict(training_config)
                            relaxed_config.update({
                                'min_score': 0.0,
                                'min_wit_score': 0.0
                            })
                            fallback_training = choose_best_training(results_training, relaxed_config, current_stats)
                            if fallback_training:
                                print(f"[INFO] Proceeding with training ({fallback_training.upper()}) after race not found")
                                do_train(fallback_training)
                                continue
                            else:
                                wit_score = results_training.get('wit', {}).get('score', 0)
                                if wit_score < 1.0:
                                    print("[INFO] No viable training after relaxation and race not found. Choosing to rest.")
                                    do_rest()
                                else:
                                    print("[INFO] No training selected after relaxation. Choosing to rest.")
                                    do_rest()
            else:
                # Race prioritization disabled: min_score already 0 at initial selection,
                # so if no training was chosen here, rest (still enforcing failure and min_wit_score)
                print("[INFO] Race prioritization disabled and no valid training found (min_score ignored). Choosing to rest.")
                do_rest()
        
        debug_print("[DEBUG] Waiting before next iteration...")
        time.sleep(1)

def check_goal_criteria(criteria_data, year, turn):
    """
    Check if goal criteria are met and determine if racing should be prioritized.
    
    Args:
        criteria_data (dict): The criteria data from OCR with text
        year (str): Current year text
        turn (str/int): Current turn number or text
    
    Returns:
        dict: Dictionary containing criteria analysis and decision
    """
    # Extract criteria text
    criteria_text = criteria_data.get("text", "")
    
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
    should_prioritize_racing = not criteria_met and not is_pre_debut 
    # and turn_less_than_10 (Temporarily disabled)
    
    debug_print(f"[DEBUG] Year: '{year}', Criteria met: {criteria_met}, Pre-debut: {is_pre_debut}, Turn < 10: {turn_less_than_10}")
    
    return {
        "criteria_met": criteria_met,
        "is_pre_debut": is_pre_debut,
        "turn_less_than_10": turn_less_than_10,
        "should_prioritize_racing": should_prioritize_racing
    } 

def log_and_flush(message, level="INFO"):
    """Log message and flush immediately for real-time GUI capture"""
    print(f"[{level}] {message}")
    sys.stdout.flush() 