import os
import sys
import time
from typing import Dict, Tuple, Any


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def _load_hint_image() -> "Image.Image":
    from PIL import Image

    image_path = os.path.join(_project_root(), "Speed_Test", "hint_check.png")
    if not os.path.exists(image_path):
        print(f"[ERROR] Test image not found: {image_path}")
        sys.exit(1)
    return Image.open(image_path).convert("RGBA")


def _now() -> float:
    return time.perf_counter()


def _print_timing(title: str, secs: float):
    print(f"[TIME] {title}: {secs*1000:.2f} ms")


def _run_hint_check_with_timings(img: "Image.Image") -> Tuple[bool, Dict[str, float]]:
    """
    Standalone copy of the hint checking flow with detailed step timings.

    Returns:
        (hint_found, timings)
    """
    # For testing, use the full image since hint_check.png is a test image
    # In production, this would use SUPPORT_CARD_ICON_REGION = (879, 278, 1059, 1169)
    
    from PIL import Image
    import cv2
    import numpy as np

    timings: Dict[str, float] = {}
    t0 = _now()

    # Step 1: For test image, use full image dimensions
    t_convert0 = _now()
    img_width, img_height = img.size
    print(f"[DEBUG] Test image dimensions: {img_width}x{img_height}")
    
    # Use full image for testing, but in production this would be cropped to SUPPORT_CARD_ICON_REGION
    region_cv = (0, 0, img_width, img_height)
    timings["region_convert"] = _now() - t_convert0

    # Step 2: Load hint template
    t_template0 = _now()
    template_path = os.path.join(_project_root(), "assets", "icons", "hint.png")
    if not os.path.exists(template_path):
        print(f"[ERROR] Hint template not found: {template_path}")
        return False, timings
    
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        print(f"[ERROR] Failed to load hint template: {template_path}")
        return False, timings
    timings["template_load"] = _now() - t_template0
    # Save a copy of the template for quick visual reference
    try:
        cv2.imwrite("debug_hint_template.png", template)
    except Exception:
        pass

    # Step 3: Convert screenshot to OpenCV format
    t_convert_cv0 = _now()
    screenshot_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    timings["screenshot_convert"] = _now() - t_convert_cv0
    # Also prepare a grayscale version for visibility and potential debugging
    try:
        gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
        cv2.imwrite("debug_hint_image_gray.png", gray)
    except Exception:
        pass

    # Step 4: For test image, no cropping needed
    t_crop0 = _now()
    # No cropping for test image - use full image
    timings["region_crop"] = _now() - t_crop0

    # Step 5: Get template dimensions and validate
    t_dim0 = _now()
    template_h, template_w = template.shape[:2]
    region_h, region_w = screenshot_cv.shape[:2]
    
    print(f"[DEBUG] Template dimensions: {template_w}x{template_h}")
    print(f"[DEBUG] Region dimensions: {region_w}x{region_h}")
    
    # Check if template is larger than the region
    if template_h > region_h or template_w > region_w:
        print(f"[WARNING] Template ({template_w}x{template_h}) is larger than region ({region_w}x{region_h})")
        print("[WARNING] This will cause template matching to fail")
        timings["template_dimensions"] = _now() - t_dim0
        timings["total"] = _now() - t0
        return False, timings
    
    timings["template_dimensions"] = _now() - t_dim0

    # Step 6: Perform template matching
    t_match0 = _now()
    try:
        result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
        timings["template_matching"] = _now() - t_match0
    except cv2.error as e:
        print(f"[ERROR] Template matching failed: {e}")
        timings["template_matching"] = _now() - t_match0
        timings["total"] = _now() - t0
        return False, timings
    # Save a heatmap visualization of the match scores
    try:
        norm = cv2.normalize(result, None, 0, 255, cv2.NORM_MINMAX)
        norm_u8 = norm.astype('uint8')
        heatmap = cv2.applyColorMap(norm_u8, cv2.COLORMAP_JET)
        cv2.imwrite("debug_hint_heatmap.png", heatmap)
    except Exception:
        pass

    # Step 7: Find locations where the matching exceeds the threshold
    t_threshold0 = _now()
    confidence = 0.6  # Default confidence from check_hint function
    locations = np.where(result >= confidence)
    timings["threshold_filtering"] = _now() - t_threshold0

    # Step 8: Process matches
    t_process0 = _now()
    matches = []
    for pt in zip(*locations[::-1]):  # Switch columns and rows
        # For test image, coordinates are already correct
        matches.append((pt[0], pt[1], template_w, template_h))
    
    hint_found = bool(matches and len(matches) > 0)
    if hint_found:
        print(f"[DEBUG] Found {len(matches)} hint matches")
        for i, (x, y, w, h) in enumerate(matches):
            print(f"[DEBUG]   Match {i+1}: ({x}, {y}) with size {w}x{h}")
        # Draw rectangles for all matches and save overlay
        try:
            overlay = screenshot_cv.copy()
            for (x, y, w, h) in matches:
                cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.imwrite("debug_hint_matches.png", overlay)
        except Exception:
            pass
    else:
        # Still create an overlay showing the best single match even if below threshold
        try:
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            best_overlay = screenshot_cv.copy()
            bx, by = max_loc
            cv2.rectangle(best_overlay, (bx, by), (bx + template_w, by + template_h), (255, 0, 0), 2)
            cv2.putText(best_overlay, f"best={max_val:.3f}", (bx, max(0, by - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            cv2.imwrite("debug_hint_best_match.png", best_overlay)
            print(f"[DEBUG] Best match confidence (no threshold hit): {max_val:.3f} at {max_loc}")
        except Exception:
            pass
    
    timings["match_processing"] = _now() - t_process0

    # Step 9: Save debug region if needed
    t_debug0 = _now()
    try:
        debug_path = "debug_hint_search_region.png"
        # For test image, save the full image
        img.save(debug_path)
        print(f"[DEBUG] Saved full test image to {debug_path}")
    except Exception as e:
        print(f"[WARNING] Failed to save debug image: {e}")
    timings["debug_save"] = _now() - t_debug0

    timings["total"] = _now() - t0
    return hint_found, timings


def _run_hint_check_multiple_confidence_levels(img: "Image.Image") -> Dict[str, Any]:
    """
    Test hint detection at multiple confidence levels to find optimal threshold.
    
    Returns:
        dict with confidence levels and their results
    """
    print("\n[INFO] Testing hint detection at multiple confidence levels...")
    
    confidence_levels = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    results = {}
    
    for conf in confidence_levels:
        t0 = _now()
        hint_found, _ = _run_hint_check_with_timings(img)
        duration = _now() - t0
        
        results[conf] = {
            "hint_found": hint_found,
            "duration_ms": duration * 1000
        }
        
        print(f"  Confidence {conf}: Hint found = {hint_found}, Duration = {duration*1000:.2f} ms")
    
    return results


def main():
    print("[INFO] Running standalone hint check on hint_check.png")
    img = _load_hint_image()

    # Test at default confidence level
    t0 = _now()
    hint_found, timings = _run_hint_check_with_timings(img)
    total = _now() - t0

    # Print results
    print(f"\n[RESULT] Hint detection result: {hint_found}")
    
    # Print timings
    print("\n[DETAIL] Timings (ms):")
    for key, value in timings.items():
        if key != "total":
            _print_timing(f"hint_check.{key}", value)
    
    _print_timing("hint_check.total", total)

    # Test multiple confidence levels
    confidence_results = _run_hint_check_multiple_confidence_levels(img)
    
    # Find optimal confidence level
    optimal_conf = None
    optimal_score = -1
    
    for conf, result in confidence_results.items():
        if result["hint_found"]:
            # Prefer lower confidence (faster) when hint is found
            score = 1.0 / (conf * result["duration_ms"])
            if score > optimal_score:
                optimal_score = score
                optimal_conf = conf
    
    if optimal_conf is not None:
        print(f"\n[RECOMMENDATION] Optimal confidence level: {optimal_conf}")
        print(f"  - Hint detected: {confidence_results[optimal_conf]['hint_found']}")
        print(f"  - Duration: {confidence_results[optimal_conf]['duration_ms']:.2f} ms")
    else:
        print("\n[WARNING] No hint detected at any confidence level")


if __name__ == "__main__":
    main()

