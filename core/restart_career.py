#!/usr/bin/env python3
"""
Restart Career functionality for Uma Musume Emulator Auto Train.
Handles career completion and auto-restart based on configuration.
"""

import sys
import os
import json
import time
from typing import Dict, Any, Optional, Tuple

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.adb_recognizer import match_template
from utils.adb_screenshot import take_screenshot
from utils.input import tap
from core.skill_auto_purchase import click_image_button
from core.ocr import extract_text, extract_number


def load_restart_config() -> Dict[str, Any]:
    """Load restart career configuration from config.json"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get('restart_career', {})
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}


def check_complete_career_screen(screenshot=None) -> bool:
    """Check if Complete Career screen is visible"""
    if screenshot is None:
        screenshot = take_screenshot()
    matches = match_template(screenshot, "assets/buttons/complete_career.png", confidence=0.8)
    if matches:
        print("✓ Complete Career screen detected")
        return True
    else:
        print("✗ Complete Career screen not detected")
        return False


def extract_total_fans(screenshot) -> int:
    """Extract total fans from the Complete Career screen"""
    region = (735, 335, 939, 401)
    cropped = screenshot.crop(region)
    text = extract_text(cropped)
    cleaned_text = ''.join(char for char in text if char.isdigit())
    
    try:
        fans = int(cleaned_text) if cleaned_text else 0
        print(f"Total Fans acquired this run: {fans}")
        return fans
    except ValueError:
        print("Could not parse total fans, defaulting to 0")
        return 0


def extract_skill_points(screenshot) -> int:
    """Extract skill points from the Complete Career screen"""
    region = (327, 1609, 441, 1651)
    cropped = screenshot.crop(region)
    number = extract_number(cropped)
    
    try:
        points = int(number) if number and number.isdigit() else 0
        print(f"Skill Points available: {points}")
        return points
    except ValueError:
        print("Could not parse skill points, defaulting to 0")
        return 0


def should_continue_restarting(current_restart_count: int, max_restart_times: int, 
                              total_fans_acquired: int, total_fans_requirement: int) -> Tuple[bool, str]:
    """Check if we should continue restarting based on config limits"""
    # Check restart count limit
    if current_restart_count >= max_restart_times:
        return False, f"Reached maximum restart limit ({max_restart_times})"
    
    # Check total fans requirement
    if total_fans_requirement > 0 and total_fans_acquired >= total_fans_requirement:
        return False, f"Reached total fans requirement ({total_fans_acquired}/{total_fans_requirement})"
    
    return True, "Continue restarting"


def execute_skill_purchase_workflow(available_points: int):
    """Execute the skill purchase workflow"""
    print("=== Auto Skill Purchase Workflow ===")
    
    # Import here to avoid circular imports
    from core.skill_auto_purchase import click_image_button
    from core.skill_recognizer import scan_all_skills_with_scroll
    from core.skill_purchase_optimizer import load_skill_config, create_purchase_plan, filter_affordable_skills
    from core.skill_auto_purchase import execute_skill_purchases
    from core.skill_recognizer import deduplicate_skills
    
    # Tap end skill button
    if not click_image_button("assets/buttons/end_skill.png", "end skill button", max_attempts=5):
        print("Failed to tap end skill button")
        return
    
    time.sleep(2)
    
    # Scan for available skills
    scan_result = scan_all_skills_with_scroll(confidence=0.9, brightness_threshold=150, max_scrolls=20)
    all_available_skills = scan_result.get('all_skills', [])
    
    if all_available_skills:
        # Deduplicate and optimize skill purchase
        deduplicated_skills = deduplicate_skills(all_available_skills, similarity_threshold=0.8)
        config = load_skill_config()
        purchase_plan = create_purchase_plan(deduplicated_skills, config)
        
        if purchase_plan:
            affordable_skills, total_cost, remaining_points = filter_affordable_skills(purchase_plan, available_points)
            if affordable_skills:
                execute_skill_purchases(affordable_skills)
    
    # Return to complete career screen
    return_to_complete_career_screen()


def return_to_complete_career_screen():
    """Return to the complete career screen after skill purchase"""
    back_success = click_image_button("assets/buttons/back_btn.png", "back button", max_attempts=5)
    if back_success:
        time.sleep(1.5)
        return check_complete_career_screen()
    return False


def finish_career_completion() -> bool:
    """Complete the career and navigate through completion screens"""
    print("=== Completing Career ===")
    
    # Click complete career button
    if not click_image_button("assets/buttons/complete_career.png", "complete career button", max_attempts=5):
        print("Failed to click complete career button")
        return False
    
    time.sleep(0.5)
    
    # Click finish button
    if not click_image_button("assets/buttons/finish.png", "finish button", max_attempts=5):
        print("Failed to click finish button")
        return False
    
    time.sleep(0.5)
    
    # Navigate through completion screens
    max_total_taps = 15
    total_taps = 0
    
    while total_taps < max_total_taps:
        # Try next button
        if click_image_button("assets/buttons/next_btn.png", "next button", max_attempts=3):
            total_taps += 1
            time.sleep(0.5)
            continue
        
        # Try close button
        if click_image_button("assets/buttons/close.png", "close button", max_attempts=3):
            total_taps += 1
            time.sleep(0.5)
            continue
        
        # Check for to_home button
        screenshot = take_screenshot()
        to_home_matches = match_template(screenshot, "assets/buttons/to_home.png", confidence=0.8)
        if to_home_matches:
            if click_image_button("assets/buttons/to_home.png", "to_home button", max_attempts=3):
                time.sleep(0.5)
                
                # Wait for career home screen
                max_wait_attempts = 30
                wait_attempts = 0
                
                while wait_attempts < max_wait_attempts:
                    screenshot = take_screenshot()
                    career_home_matches = match_template(screenshot, "assets/buttons/Career_Home.png", confidence=0.8)
                    if career_home_matches:
                        print("✓ Career Home screen detected - Career completion successful")
                        return True
                    time.sleep(1.0)
                    wait_attempts += 1
                
                print("Timeout waiting for Career Home screen")
                return False
        
        time.sleep(1.0)
    
    print("Failed to complete career navigation")
    return False


def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}


from utils.template_matching import wait_for_image


def filter_support():
    """Filter support cards based on configuration."""
    print("Filtering support cards...")
    
    config = load_config()
    auto_start_career = config.get('auto_start_career', {})
    support_speciality = auto_start_career.get('support_speciality', 'SPEED')
    support_rarity = auto_start_career.get('support_rarity', 'SSR')
    
    # Tap filter button
    tap(696, 1621)
    time.sleep(0.5)
    
    # Tap additional filter coordinate
    tap(774, 206)
    time.sleep(0.5)

    # Reset filter
    screenshot = take_screenshot()
    reset_filter_matches = match_template(screenshot, "assets/buttons/reset_filter.png", confidence=0.8)
    if reset_filter_matches:
        x, y, w, h = reset_filter_matches[0]
        center = (x + w//2, y + h//2)
        tap(center[0], center[1])
        time.sleep(0.5)
    
    # Set support speciality
    support_speciality_coords = {
        "SPD": (102, 627),
        "STA": (444, 623),
        "PWR": (786, 618),
        "GUTS": (109, 741),
        "WIT": (442, 732),
        "PAL": (777, 731),
    }
    
    if support_speciality in support_speciality_coords:
        x, y = support_speciality_coords[support_speciality]
        tap(x, y)
        time.sleep(0.5)
    
    # Set support rarity
    support_rarity_coords = {
        "R": (102, 408),
        "SR": (437, 414),
        "SSR": (777, 410),
    }
    
    if support_rarity in support_rarity_coords:
        x, y = support_rarity_coords[support_rarity]
        tap(x, y)
        time.sleep(0.5)
    
    # OK button after filter selection
    ok_matches = match_template(screenshot, "assets/buttons/ok_btn.png", confidence=0.6)
    if ok_matches:
        x, y, w, h = ok_matches[0]
        center = (x + w//2, y + h//2)
        tap(center[0], center[1])
        time.sleep(0.5)
    
    # Select first following card
    time.sleep(1)
    screenshot = take_screenshot()
    following_matches = match_template(screenshot, "assets/icons/following.png", confidence=0.8)
    
    if following_matches:
        following_matches.sort(key=lambda match: match[1])
        x, y, w, h = following_matches[0]
        center = (x + w//2, y + h//2)
        tap(center[0], center[1])
        time.sleep(0.5)


def skip_check():
    """Check which skip button is on screen and adjust accordingly."""
    print("Checking skip button...")
    
    screenshot = take_screenshot()
    
    skip_variants = [
        ("assets/buttons/skip_off.png", "Skip Off"),
        ("assets/buttons/skip_x1.png", "Skip x1"),
        ("assets/buttons/skip_x2.png", "Skip x2")
    ]
    
    best_match = None
    best_confidence = 0
    
    for template_path, variant_name in skip_variants:
        if os.path.exists(template_path):
            from utils.adb_recognizer import max_match_confidence
            confidence = max_match_confidence(screenshot, template_path)
            if confidence and confidence > best_confidence:
                best_confidence = confidence
                best_match = template_path
    
    if best_match and best_confidence > 0.7:
        if "skip_off" in best_match:
            matches = match_template(screenshot, best_match, confidence=0.7)
            if matches:
                x, y, w, h = matches[0]
                center = (x + w//2, y + h//2)
                tap(center[0], center[1])
                time.sleep(0.1)
                tap(center[0], center[1])
        elif "skip_x1" in best_match:
            matches = match_template(screenshot, best_match, confidence=0.7)
            if matches:
                x, y, w, h = matches[0]
                center = (x + w//2, y + h//2)
                tap(center[0], center[1])


def start_career() -> bool:
    """Start a new career using the existing start_career logic"""
    print("=== Starting New Career ===")
    
    config = load_config()
    auto_start_career = config.get('auto_start_career', {})
    include_guests_legacy = auto_start_career.get('include_guests_legacy', False)
    
    try:
        # Step 1: Tap Career Home and wait 10s
        career_home_matches = match_template(take_screenshot(), "assets/buttons/Career_Home.png", confidence=0.8)
        if career_home_matches:
            x, y, w, h = career_home_matches[0]
            center = (x + w//2, y + h//2)
            tap(center[0], center[1])
            time.sleep(10)
        else:
            print("Career Home not found")
            return False
        
        # Step 2: Tap Next button twice
        for i in range(2):
            next_matches = match_template(take_screenshot(), "assets/buttons/next_btn.png", confidence=0.8)
            if next_matches:
                x, y, w, h = next_matches[0]
                center = (x + w//2, y + h//2)
                tap(center[0], center[1])
                time.sleep(1)
            else:
                return False
        
        # Step 3: Tap Auto Select
        print("Auto Select...")
        auto_select_matches = match_template(take_screenshot(), "assets/buttons/auto_select.png", confidence=0.8)
        if auto_select_matches:
            x, y, w, h = auto_select_matches[0]
            center = (x + w//2, y + h//2)
            tap(center[0], center[1])
            time.sleep(1)
        else:
            return False
        
        # Step 4: Conditional check
        if include_guests_legacy:
            tap(420, 1030)
            time.sleep(0.5)
        
        # Step 5: Tap OK button
        ok_matches = match_template(take_screenshot(), "assets/buttons/ok_btn.png", confidence=0.6)
        if ok_matches:
            x, y, w, h = ok_matches[0]
            center = (x + w//2, y + h//2)
            tap(center[0], center[1])
            time.sleep(0.5)
        else:
            return False
        
        # Step 6: Tap Next button
        next_matches = match_template(take_screenshot(), "assets/buttons/next_btn.png", confidence=0.8)
        if next_matches:
            x, y, w, h = next_matches[0]
            center = (x + w//2, y + h//2)
            tap(center[0], center[1])
            time.sleep(1)
        else:
            return False
        
        # Step 7: Tap Friend Support Choose
        print("Friend Support...")
        friend_support_matches = match_template(take_screenshot(), "assets/buttons/Friend_support_choose.png", confidence=0.8)
        if friend_support_matches:
            x, y, w, h = friend_support_matches[0]
            center = (x + w//2, y + h//2)
            tap(center[0], center[1])
            time.sleep(0.5)
        else:
            return False
        
        # Step 8: Filter support
        print("Filtering...")
        filter_support()
        time.sleep(1)
        
        # Step 9: Start Career 1
        start_career_1_matches = match_template(take_screenshot(), "assets/buttons/start_career_1.png", confidence=0.8)
        if start_career_1_matches:
            x, y, w, h = start_career_1_matches[0]
            center = (x + w//2, y + h//2)
            tap(center[0], center[1])
            time.sleep(0.5)
        else:
            return False
        
        # Step 10: Start Career 2
        start_career_2_matches = match_template(take_screenshot(), "assets/buttons/start_career_2.png", confidence=0.8)
        if start_career_2_matches:
            x, y, w, h = start_career_2_matches[0]
            center = (x + w//2, y + h//2)
            tap(center[0], center[1])
        else:
            return False
        
        # Step 11: Wait for skip button and double tap
        print("Skip button...")
        skip_matches = wait_for_image("assets/buttons/skip_btn.png", timeout=30, confidence=0.8)
        if skip_matches:
            tap(skip_matches[0], skip_matches[1])
            time.sleep(0.1)
            tap(skip_matches[0], skip_matches[1])
            time.sleep(0.5)
        else:
            return False
        
        # Step 12: Wait for confirm button
        print("Confirm button...")
        confirm_matches = wait_for_image("assets/buttons/confirm.png", timeout=30, confidence=0.8)
        if not confirm_matches:
            return False
        
        # Step 13: Tap coordinates
        tap(213, 939)
        time.sleep(0.5)
        
        # Step 14: Skip check
        skip_check()
        time.sleep(0.5)
        
        # Step 15: Tap confirm
        confirm_matches = match_template(take_screenshot(), "assets/buttons/confirm.png", confidence=0.8)
        if confirm_matches:
            x, y, w, h = confirm_matches[0]
            center = (x + w//2, y + h//2)
            tap(center[0], center[1])
        else:
            return False
        
        # Step 16: Wait for Tazuna hint
        tazuna_hint_matches = wait_for_image("assets/ui/tazuna_hint.png", timeout=60, confidence=0.8)
        if tazuna_hint_matches:
            print("Career start completed!")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False


def complete_career(current_restart_count: int, max_restart_times: int, 
                   total_fans_acquired: int, total_fans_requirement: int) -> Tuple[bool, int, int]:
    """Execute the complete career workflow including skill purchase"""
    print("=== Executing Complete Career Workflow ===")
    
    # Extract fans and skill points first
    screenshot = take_screenshot()
    run_fans = extract_total_fans(screenshot)
    skill_points = extract_skill_points(screenshot)
    
    # Add fans to total
    total_fans_acquired += run_fans
    print(f"Total fans acquired so far: {total_fans_acquired}")
    
    # Check if we should continue
    should_continue, reason = should_continue_restarting(
        current_restart_count, max_restart_times, total_fans_acquired, total_fans_requirement
    )
    if not should_continue:
        print(f"Career completion criteria met: {reason}")
        return False, current_restart_count, total_fans_acquired
    
    # Increment restart count
    current_restart_count += 1
    print(f"Restart count: {current_restart_count}/{max_restart_times}")
    
    # Execute skill purchase workflow (if skill points available)
    if skill_points > 0:
        execute_skill_purchase_workflow(skill_points)
    
    # Complete the career
    success = finish_career_completion()
    return success, current_restart_count, total_fans_acquired


def execute_restart_cycle(current_restart_count: int, max_restart_times: int, 
                         total_fans_acquired: int, total_fans_requirement: int) -> Tuple[bool, int, int]:
    """Execute one complete restart cycle"""
    print(f"\n=== Restart Cycle {current_restart_count + 1}/{max_restart_times} ===")
    
    # Complete the current career
    success, new_restart_count, new_total_fans = complete_career(
        current_restart_count, max_restart_times, total_fans_acquired, total_fans_requirement
    )
    
    if not success:
        # Check if we reached completion criteria
        should_continue, reason = should_continue_restarting(
            new_restart_count, max_restart_times, new_total_fans, total_fans_requirement
        )
        if not should_continue:
            print(f"Career completion criteria met: {reason}")
            return False, new_restart_count, new_total_fans
        else:
            print("Failed to complete career")
            return False, current_restart_count, total_fans_acquired
    
    # Start new career
    if not start_career():
        print("Failed to start new career")
        return False, new_restart_count, new_total_fans
    
    print(f"✓ Restart cycle {new_restart_count} completed successfully")
    return True, new_restart_count, new_total_fans


def run_restart_workflow() -> bool:
    """Main restart workflow - continues until criteria are met"""
    print("=== Starting Career Restart Workflow ===")
    
    # Load configuration
    restart_config = load_restart_config()
    restart_enabled = restart_config.get('restart_enabled', False)
    max_restart_times = restart_config.get('restart_times', 5)
    total_fans_requirement = restart_config.get('total_fans_requirement', 0)
    
    print(f"Restart enabled: {restart_enabled}")
    print(f"Max restarts: {max_restart_times}")
    print(f"Total fans requirement: {total_fans_requirement}")
    
    if not restart_enabled:
        print("Restart is disabled in config")
        return False
    
    # Runtime state - managed in function scope
    current_restart_count = 0
    total_fans_acquired = 0
    
    # Continue restarting until criteria are met
    while True:
        should_continue, reason = should_continue_restarting(
            current_restart_count, max_restart_times, total_fans_acquired, total_fans_requirement
        )
        if not should_continue:
            print(f"Restart criteria met: {reason}")
            break
        
        success, new_restart_count, new_total_fans = execute_restart_cycle(
            current_restart_count, max_restart_times, total_fans_acquired, total_fans_requirement
        )
        
        if not success:
            # Check if we reached completion criteria
            should_continue, reason = should_continue_restarting(
                new_restart_count, max_restart_times, new_total_fans, total_fans_requirement
            )
            if not should_continue:
                print(f"Career completion criteria met: {reason}")
                break
            else:
                print("Restart cycle failed")
                break
        
        # Update state for next iteration
        current_restart_count = new_restart_count
        total_fans_acquired = new_total_fans
    
    print("=== Career Restart Workflow Complete ===")
    print(f"Total restarts completed: {current_restart_count}")
    print(f"Total fans acquired: {total_fans_acquired}")
    
    return True


def career_lobby_check(screenshot=None) -> bool:
    """Check if we should restart career from career lobby"""
    # Load configuration
    restart_config = load_restart_config()
    restart_enabled = restart_config.get('restart_enabled', False)
    
    if not restart_enabled:
        print("Restart is disabled - stopping bot")
        return False
    
    # Check if complete career screen is visible
    if check_complete_career_screen(screenshot):
        print("Complete Career screen detected - starting restart workflow")
        return run_restart_workflow()
    
    return True  # Continue with normal career lobby


def main():
    """Main function for testing"""
    print("=== Career Restart Manager Test ===")
    
    if check_complete_career_screen():
        print("Complete Career screen found - executing restart workflow")
        success = run_restart_workflow()
        if success:
            print("✓ Restart workflow completed successfully")
        else:
            print("✗ Restart workflow failed or completed early")
    else:
        print("No Complete Career screen found")


if __name__ == "__main__":
    main()
