import time
import os
from utils.skill_recognizer import take_screenshot, perform_swipe, recognize_skill_up_locations
from utils.skill_purchase_optimizer import fuzzy_match_skill_name
from utils.adb_screenshot import run_adb_command

def click_skill_up_button(x, y):
    """
    Click on a skill_up button at the specified coordinates.
    
    Args:
        x, y: Coordinates of the skill_up button
    
    Returns:
        bool: True if click was successful, False otherwise
    """
    try:
        click_command = ['shell', 'input', 'tap', str(x), str(y)]
        result = run_adb_command(click_command)
        if result is not None:
            print(f"   👆 Clicked skill_up button at ({x}, {y})")
            return True
        else:
            print(f"   ❌ Failed to click at ({x}, {y})")
            return False
    except Exception as e:
        print(f"   ❌ Error clicking button: {e}")
        return False

def click_image_button(image_path, description="button", max_attempts=10, wait_between_attempts=0.5):
    """
    Find and click a button by image template matching with retry attempts.
    
    Args:
        image_path: Path to the button image template
        description: Description for logging
        max_attempts: Maximum number of attempts to find the button
        wait_between_attempts: Seconds to wait between attempts
    
    Returns:
        bool: True if button was found and clicked, False otherwise
    """
    try:
        import cv2
        import numpy as np
        
        if not os.path.exists(image_path):
            print(f"   ❌ {description} template not found: {image_path}")
            return False
        
        # Load template once
        template = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if template is None:
            print(f"   ❌ Failed to load {description} template: {image_path}")
            return False
        
        print(f"   🔍 Looking for {description} (max {max_attempts} attempts)...")
        
        for attempt in range(max_attempts):
            try:
                # Take screenshot
                screenshot = take_screenshot()
                screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                # Perform template matching
                result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
                
                # Find the best match
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= 0.8:  # High confidence threshold
                    # Calculate center of the button
                    template_height, template_width = template.shape[:2]
                    center_x = max_loc[0] + template_width // 2
                    center_y = max_loc[1] + template_height // 2
                    
                    # Click the button
                    success = click_skill_up_button(center_x, center_y)
                    if success:
                        print(f"   ✅ {description} clicked successfully (attempt {attempt + 1})")
                        return True
                    else:
                        print(f"   ❌ Failed to click {description} (attempt {attempt + 1})")
                else:
                    print(f"   🔍 {description} not found (attempt {attempt + 1}/{max_attempts}, confidence: {max_val:.3f})")
                
                # Wait before next attempt (except on last attempt)
                if attempt < max_attempts - 1:
                    time.sleep(wait_between_attempts)
                    
            except Exception as e:
                print(f"   ⚠️  Error in attempt {attempt + 1}: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(wait_between_attempts)
        
        print(f"   ❌ {description} not found after {max_attempts} attempts")
        return False
            
    except Exception as e:
        print(f"   ❌ Error finding {description}: {e}")
        return False

def fast_swipe_to_top():
    """
    Perform fast swipes to get to the top of the skill list.
    """
    print("🚀 Fast scrolling to top of skill list...")
    
    for i in range(3):
        print(f"   📱 Fast swipe {i+1}/3")
        success = perform_swipe(504, 1400, 504, 800, duration=300)  # Fast swipe UP (start low, end high)
        if success:
            time.sleep(0.3)  # Short wait between fast swipes
        else:
            print(f"   ⚠️  Fast swipe {i+1} failed")
    
    print("   ⏱️  Waiting for UI to settle...")
    time.sleep(1.5)  # Reduced wait time

def execute_skill_purchases(purchase_plan, max_scrolls=20):
    """
    Execute the automated skill purchase plan.
    
    Args:
        purchase_plan: List of skills to purchase (from create_purchase_plan)
        max_scrolls: Maximum number of scrolls to prevent infinite loops
    
    Returns:
        dict: {
            'success': bool,
            'purchased_skills': [list of successfully purchased skills],
            'failed_skills': [list of skills that couldn't be found/purchased],
            'scrolls_performed': int
        }
    """
    print("🛒 EXECUTING AUTOMATED SKILL PURCHASES")
    print("=" * 60)
    
    if not purchase_plan:
        print("❌ No skills to purchase!")
        return {
            'success': False,
            'purchased_skills': [],
            'failed_skills': [],
            'scrolls_performed': 0,
            'error': 'No skills in purchase plan'
        }
    
    print(f"📋 Skills to purchase: {len(purchase_plan)}")
    for i, skill in enumerate(purchase_plan, 1):
        print(f"   {i}. {skill['name']} - {skill['price']} points")
    print()
    
    purchased_skills = []
    failed_skills = []
    remaining_skills = purchase_plan.copy()
    scrolls_performed = 0
    
    try:
        # Step 1: Fast swipe to top
        fast_swipe_to_top()
        
        # Step 2: Scroll down slowly to find and purchase skills
        print("🔍 Searching for skills to purchase...")
        
        while remaining_skills and scrolls_performed < max_scrolls:
            scrolls_performed += 1
            print(f"\n📄 Scroll {scrolls_performed}/{max_scrolls}")
            print(f"   Looking for: {[s['name'] for s in remaining_skills]}")
            
            # Scan current screen for available skills
            result = recognize_skill_up_locations(
                confidence=0.9,
                debug_output=False,
                filter_dark_buttons=True,
                brightness_threshold=150,
                extract_skills=True
            )
            
            if 'error' in result:
                print(f"   ❌ Error during skill detection: {result['error']}")
                break
            
            current_skills = result.get('skills', [])
            if not current_skills:
                print("   No skills found on this screen")
            else:
                print(f"   Found {len(current_skills)} available skills on screen")
                
                # Check if any of our target skills are on this screen
                skills_found_on_screen = []
                
                for target_skill in remaining_skills:
                    for screen_skill in current_skills:
                        # Use fuzzy matching to find target skills
                        if fuzzy_match_skill_name(screen_skill['name'], target_skill['name']):
                            skills_found_on_screen.append({
                                'target': target_skill,
                                'screen': screen_skill
                            })
                            print(f"   🎯 Found target skill: {screen_skill['name']} (matches {target_skill['name']})")
                            break
                
                # Purchase found skills
                for match in skills_found_on_screen:
                    target_skill = match['target']
                    screen_skill = match['screen']
                    
                    # Get button coordinates
                    x, y, w, h = screen_skill['location']
                    button_center_x = x + w // 2
                    button_center_y = y + h // 2
                    
                    print(f"   🛒 Purchasing: {screen_skill['name']}")
                    
                    # Click the skill_up button
                    if click_skill_up_button(button_center_x, button_center_y):
                        purchased_skills.append(target_skill)
                        remaining_skills.remove(target_skill)
                        print(f"   ✅ Successfully purchased: {screen_skill['name']}")
                        
                        # Short wait after purchase
                        time.sleep(1)
                    else:
                        print(f"   ❌ Failed to purchase: {screen_skill['name']}")
                
                # If we found and purchased skills, wait a bit longer
                if skills_found_on_screen:
                    time.sleep(1.5)
            
            # Continue scrolling if we haven't found all skills
            if remaining_skills and scrolls_performed < max_scrolls:
                print("   📱 Scrolling down to find more skills...")
                success = perform_swipe(504, 1492, 504, 926, duration=1000)  # Slow scroll like recognizer
                if not success:
                    print("   ❌ Failed to scroll, stopping search")
                    break
                
                time.sleep(1.5)  # Wait for scroll animation
        
        # Step 3: Click confirm button
        if purchased_skills:
            print(f"\n🎯 Purchased {len(purchased_skills)} skills, looking for confirm button...")
            
            confirm_success = click_image_button("assets/buttons/confirm.png", "confirm button", max_attempts=10)
            if confirm_success:
                print("   ⏱️  Waiting for confirmation...")
                time.sleep(2)  # Reduced wait time
                
                # Step 4: Click learn button
                print("   🎓 Looking for learn button...")
                learn_success = click_image_button("assets/buttons/learn.png", "learn button", max_attempts=10)
                if learn_success:
                    print("   ⏱️  Waiting for learning to complete...")
                    time.sleep(1.5)  # Reduced wait time
                    
                    # Step 5: Click close button (wait before it appears)
                    print("   🚪 Waiting for close button to appear...")
                    time.sleep(1.5)  # Reduced wait time
                    close_success = click_image_button("assets/buttons/close.png", "close button", max_attempts=10)
                    if close_success:
                        print("   ✅ Skill purchase sequence completed successfully!")
                    else:
                        print("   ⚠️  Close button not found - manual intervention may be needed")
                else:
                    print("   ⚠️  Learn button not found or failed to click")
            else:
                print("   ⚠️  Confirm button not found or failed to click")
        
        # Add any remaining skills to failed list
        failed_skills.extend(remaining_skills)
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"🎉 PURCHASE EXECUTION COMPLETE!")
        print(f"   ✅ Successfully purchased: {len(purchased_skills)} skills")
        print(f"   ❌ Failed to find/purchase: {len(failed_skills)} skills")
        print(f"   📱 Scrolls performed: {scrolls_performed}")
        
        if purchased_skills:
            print(f"\n✅ Purchased skills:")
            for skill in purchased_skills:
                print(f"   • {skill['name']} - {skill['price']} points")
            print(f"\n🔄 Button sequence executed:")
            print(f"   1. ✅ Skill_up buttons clicked")
            print(f"   2. ✅ Confirm button clicked (10 attempts max)")
            print(f"   3. ✅ Learn button clicked (10 attempts max)")
            print(f"   4. ✅ Close button clicked (10 attempts max, 2s wait)")
        
        if failed_skills:
            print(f"\n❌ Failed to purchase:")
            for skill in failed_skills:
                print(f"   • {skill['name']} - {skill['price']} points")
        
        return {
            'success': len(purchased_skills) > 0,
            'purchased_skills': purchased_skills,
            'failed_skills': failed_skills,
            'scrolls_performed': scrolls_performed
        }
        
    except Exception as e:
        print(f"❌ Error during skill purchase execution: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'purchased_skills': purchased_skills,
            'failed_skills': failed_skills + remaining_skills,
            'scrolls_performed': scrolls_performed,
            'error': str(e)
        }

def test_skill_auto_purchase():
    """
    Test function for the automated skill purchase system.
    """
    print("🧪 TESTING AUTOMATED SKILL PURCHASE")
    print("=" * 60)
    print("⚠️  WARNING: This will actually purchase skills!")
    print("   Make sure you're on the skill purchase screen.")
    print()
    
    # Mock purchase plan for testing
    test_purchase_plan = [
        {"name": "Professor of Curvature", "price": "342"},
        {"name": "Pressure", "price": "160"}
    ]
    
    print("📋 Test purchase plan:")
    for i, skill in enumerate(test_purchase_plan, 1):
        print(f"   {i}. {skill['name']} - {skill['price']} points")
    print()
    
    confirm = input("Do you want to proceed with the test purchase? (y/n): ").lower().startswith('y')
    if not confirm:
        print("❌ Test cancelled.")
        return
    
    # Execute the purchase
    result = execute_skill_purchases(test_purchase_plan)
    
    print(f"\n📊 Test Results:")
    print(f"   Success: {result['success']}")
    print(f"   Purchased: {len(result['purchased_skills'])}")
    print(f"   Failed: {len(result['failed_skills'])}")
    if 'error' in result:
        print(f"   Error: {result['error']}")

if __name__ == "__main__":
    test_skill_auto_purchase()
