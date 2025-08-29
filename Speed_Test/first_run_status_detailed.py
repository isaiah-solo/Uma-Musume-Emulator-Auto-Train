import os
import sys
import time
from typing import Any, Callable, Dict, List, Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class TimingRegistry:
    def __init__(self):
        self.events: List[Tuple[str, float]] = []

    def record(self, name: str, secs: float):
        self.events.append((name, secs))

    def clear(self):
        self.events.clear()

    def total(self) -> float:
        return sum(d for _, d in self.events)


REGISTRY = TimingRegistry()


def _wrap_func(target, attr: str, label: str):
    orig = getattr(target, attr)

    def wrapped(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            return orig(*args, **kwargs)
        finally:
            REGISTRY.record(label, time.perf_counter() - t0)

    setattr(target, attr, wrapped)


def _install_static_screenshot(image_path: str):
    from PIL import Image
    import utils.screenshot as adb_shot

    def take_screenshot_stub():
        t0 = time.perf_counter()
        img = Image.open(image_path).convert("RGBA")
        REGISTRY.record("take_screenshot(static_png)", time.perf_counter() - t0)
        return img

    adb_shot.take_screenshot = take_screenshot_stub  # type: ignore


def _install_profilers():
    # screenshot helpers
    import utils.screenshot as shot
    if hasattr(shot, "enhanced_screenshot"):
        _wrap_func(shot, "enhanced_screenshot", "screenshot.enhanced_screenshot")
    if hasattr(shot, "capture_region"):
        _wrap_func(shot, "capture_region", "screenshot.capture_region")
    if hasattr(shot, "enhanced_screenshot_for_year"):
        _wrap_func(shot, "enhanced_screenshot_for_year", "screenshot.enhanced_screenshot_for_year")
    if hasattr(shot, "enhanced_screenshot_for_failure"):
        _wrap_func(shot, "enhanced_screenshot_for_failure", "screenshot.enhanced_screenshot_for_failure")

    # recognizer + OCR
    import utils.recognizer as recog
    if hasattr(recog, "match_template"):
        _wrap_func(recog, "match_template", "recognizer.match_template")

    # core OCR helpers
    import core.ocr as ocr
    for fn in [
        "extract_text",
        "extract_number",
        "extract_turn_number",
        "extract_mood_text",
        "extract_failure_text",
        "extract_failure_text_with_confidence",
    ]:
        if hasattr(ocr, fn):
            _wrap_func(ocr, fn, f"core.ocr.{fn}")

    # pytesseract wrappers (optional)
    try:
        import pytesseract as pt
        if hasattr(pt, "image_to_string"):
            _wrap_func(pt, "image_to_string", "pytesseract.image_to_string")
        if hasattr(pt, "image_to_data"):
            _wrap_func(pt, "image_to_data", "pytesseract.image_to_data")
    except Exception:
        pass

    # PIL Image operations commonly used in processing
    try:
        from PIL import Image as PILImage

        def wrap_image_method(name: str):
            orig = getattr(PILImage.Image, name)

            def wrapped(self, *args, **kwargs):
                t0 = time.perf_counter()
                try:
                    return orig(self, *args, **kwargs)
                finally:
                    REGISTRY.record(f"PIL.Image.{name}", time.perf_counter() - t0)

            setattr(PILImage.Image, name, wrapped)

        for meth in ["crop", "resize", "convert", "save"]:
            if hasattr(PILImage.Image, meth):
                wrap_image_method(meth)
    except Exception:
        pass

    # ImageEnhance ops
    try:
        from PIL import ImageEnhance as IE
        for enhancer in ["Contrast", "Sharpness"]:
            if hasattr(IE, enhancer):
                cls = getattr(IE, enhancer)
                if hasattr(cls, "enhance"):
                    orig_enhance = cls.enhance

                    def enhance_wrapped(self, *args, **kwargs):
                        t0 = time.perf_counter()
                        try:
                            return orig_enhance(self, *args, **kwargs)
                        finally:
                            REGISTRY.record(f"PIL.ImageEnhance.{enhancer}.enhance", time.perf_counter() - t0)

                    cls.enhance = enhance_wrapped
    except Exception:
        pass


def _run_check(fn: Callable[[], Any], name: str) -> Dict[str, Any]:
    REGISTRY.clear()
    t0 = time.perf_counter()
    value = fn()
    total = time.perf_counter() - t0
    steps = list(REGISTRY.events)
    return {"name": name, "value": value, "steps": steps, "total": total}


def main():
    test_image = os.path.join(PROJECT_ROOT, "Speed_Test", "Status_tets.png")
    if not os.path.exists(test_image):
        print(f"[ERROR] Test image not found: {test_image}")
        sys.exit(1)

    _install_static_screenshot(test_image)
    _install_profilers()

    # Import after patching
    from core.state import (
        check_mood,
        check_turn,
        check_current_year,
        check_goal_name_with_g1_requirement,
        check_criteria,
        check_energy_bar,
        check_current_stats,
    )

    checks: List[Tuple[str, Callable[[], Any]]] = [
        ("check_mood", check_mood),
        ("check_turn", check_turn),
        ("check_current_year", check_current_year),
        ("check_goal_name_with_g1_requirement", check_goal_name_with_g1_requirement),
        ("check_criteria", check_criteria),
        ("check_energy_bar", check_energy_bar),
        ("check_current_stats", check_current_stats),
    ]

    results = []
    grand_t0 = time.perf_counter()
    for name, fn in checks:
        results.append(_run_check(fn, name))
    grand_total = time.perf_counter() - grand_t0

    # Pretty print
    print("[INFO] === Detailed first-run timings ===")
    for res in results:
        print(f"\n[INFO] {res['name']} -> total {res['total']*1000:.2f} ms; value={res['value']}")
        # group identical step labels and sum times
        agg: Dict[str, float] = {}
        for label, secs in res["steps"]:
            agg[label] = agg.get(label, 0.0) + secs
        for label, secs in agg.items():
            print(f"  - {label}: {secs*1000:.2f} ms")

    print(f"\n[INFO] === Total time across all checks: {grand_total*1000:.2f} ms ===")


if __name__ == "__main__":
    main()


