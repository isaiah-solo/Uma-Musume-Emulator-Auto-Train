import os
import sys
import time
from typing import Dict, Tuple, Any


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def _load_status_image() -> "Image.Image":
    from PIL import Image

    image_path = os.path.join(_project_root(), "Speed_Test", "Status_tets.png")
    if not os.path.exists(image_path):
        print(f"[ERROR] Test image not found: {image_path}")
        sys.exit(1)
    return Image.open(image_path).convert("RGBA")


def _now() -> float:
    return time.perf_counter()


def _print_timing(title: str, secs: float):
    print(f"[TIME] {title}: {secs*1000:.2f} ms")


def _run_stats_check_with_timings(img: "Image.Image") -> Tuple[Dict[str, int], Dict[str, Dict[str, float]]]:
    """
    Standalone copy of the current stats OCR flow with detailed step timings.

    Returns:
        (stats, timings_per_stat)
    """
    # Local copy of regions (kept in sync with utils/constants_phone.py)
    SPD_REGION = (108, 1284, 204, 1326)
    STA_REGION = (273, 1284, 375, 1329)
    PWR_REGION = (444, 1284, 543, 1326)
    GUTS_REGION = (621, 1281, 711, 1323)
    WIT_REGION = (780, 1284, 876, 1323)

    from PIL import Image
    import pytesseract
    import re

    stats: Dict[str, int] = {}
    timings: Dict[str, Dict[str, float]] = {}

    stat_regions = {
        "spd": SPD_REGION,
        "sta": STA_REGION,
        "pwr": PWR_REGION,
        "guts": GUTS_REGION,
        "wit": WIT_REGION,
    }

    for name, region in stat_regions.items():
        step_times: Dict[str, float] = {}

        t0 = _now()
        # emulate take_screenshot() + crop
        t_crop0 = _now()
        stat_img = img.crop(region)
        step_times["crop"] = _now() - t_crop0

        # cheap grayscale (improves digit separation with minimal cost)
        t_gray0 = _now()
        stat_img = stat_img.convert("L")
        step_times["grayscale"] = _now() - t_gray0

        # ocr (fast & accurate for single numbers): prefer legacy+psm8; fallback to LSTM if legacy not installed
        t_ocr0 = _now()
        try:
            stat_text = pytesseract.image_to_string(
                stat_img,
                config='--oem 0 --psm 8 -c tessedit_char_whitelist=0123456789',
            ).strip()
        except Exception:
            stat_text = pytesseract.image_to_string(
                stat_img,
                config='--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789',
            ).strip()
        step_times["tesseract"] = _now() - t_ocr0

        # parse
        t_parse0 = _now()
        if stat_text:
            m = re.search(r"(\d+)", stat_text)
            value = int(m.group(1)) if m else 0
        else:
            value = 0
        step_times["parse_regex"] = _now() - t_parse0

        step_times["total"] = _now() - t0
        stats[name] = value
        timings[name] = step_times

    return stats, timings


def main():
    print("[INFO] Running standalone stats check on Status_tets.png")
    img = _load_status_image()

    t0 = _now()
    stats, timings = _run_stats_check_with_timings(img)
    total = _now() - t0

    # Print stats
    print("\n[RESULT] Current stats:")
    print("  " + ", ".join([f"{k.upper()}: {v}" for k, v in stats.items()]))

    # Print timings per stat
    print("\n[DETAIL] Timings per stat (ms):")
    for name in ["spd", "sta", "pwr", "guts", "wit"]:
        t = timings.get(name, {})
        if not t:
            continue
        print(f"- {name.upper()} -> total={t.get('total', 0.0)*1000:.2f}")
        for key in ["crop", "resize2x", "grayscale", "contrast2.0", "tesseract", "parse_regex"]:
            if key in t:
                _print_timing(f"{name}.{key}", t[key])

    _print_timing("ALL_STATS.total", total)


if __name__ == "__main__":
    main()


