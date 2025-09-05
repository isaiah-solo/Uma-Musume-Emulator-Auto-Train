import os
import sys
import time
from statistics import mean
from typing import Callable, Dict, Any, Tuple

# Ensure project root is on sys.path so we can use existing functions
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _install_static_screenshot(image_path: str):
    """Monkey-patch utils.screenshot.take_screenshot to return a fixed image.

    All other helpers (enhanced_screenshot, capture_region, etc.) call take_screenshot
    internally, so this is sufficient to make the rest of the code operate on the
    provided PNG without using ADB.
    """
    from PIL import Image  # Local import to avoid leaking at module import time

    import utils.screenshot as adb_shot

    def take_screenshot_stub():
        img = Image.open(image_path).convert("RGBA")
        return img

    adb_shot.take_screenshot = take_screenshot_stub  # type: ignore


def _status_checks() -> Dict[str, Tuple[Any, float]]:
    """Run the same status getters used at the start of career_lobby() once.

    Returns a dict mapping name -> (value, elapsed_seconds).
    """
    from utils.constants_phone import MOOD_LIST
    from core.state import (
        check_mood,
        check_turn,
        check_current_year,
        check_goal_name,
        check_criteria,
        check_energy_bar,
        check_current_stats,
    )

    def timed(fn: Callable[[], Any]) -> Tuple[Any, float]:
        t0 = time.perf_counter()
        val = fn()
        t1 = time.perf_counter()
        return val, (t1 - t0)

    results: Dict[str, Tuple[Any, float]] = {}

    mood, t_mood = timed(check_mood)
    results["mood"] = (mood, t_mood)

    turn, t_turn = timed(check_turn)
    results["turn"] = (turn, t_turn)

    year, t_year = timed(check_current_year)
    results["year"] = (year, t_year)

    goal_data, t_goal = timed(check_goal_name)
    results["goal_name_with_g1"] = (goal_data, t_goal)

    criteria, t_criteria = timed(check_criteria)
    results["criteria"] = (criteria, t_criteria)

    energy, t_energy = timed(check_energy_bar)
    results["energy_percentage"] = (energy, t_energy)

    stats, t_stats = timed(check_current_stats)
    results["current_stats"] = (stats, t_stats)

    # also provide derived fields as career_lobby() logs them
    if isinstance(mood, str):
        try:
            from utils.constants_phone import MOOD_LIST as _MOODS
            results["mood_index"] = (_MOODS.index(mood), 0.0)
        except Exception:
            results["mood_index"] = (-1, 0.0)

    return results


def _print_first_run(results: Dict[str, Tuple[Any, float]], total_time: float):
    # Mirror the status print layout used in career_lobby()
    goal_data = results["goal_name_with_g1"][0]
    energy = results["energy_percentage"][0]
    stats = results["current_stats"][0]

    print("[INFO] === GAME STATUS ===")
    print(f"[INFO] Year: {results['year'][0]}")
    print(f"[INFO] Mood: {results['mood'][0]}")
    print(f"[INFO] Turn: {results['turn'][0]}")
    print(f"[INFO] Goal Name: {goal_data['text'] if isinstance(goal_data, dict) else goal_data}")

    print(f"[INFO] Status: {results['criteria'][0]}")
    print(f"[INFO] Energy: {energy:.1f}%")
    print(
        f"[INFO] Current stats: SPD: {stats.get('spd', 0)}, STA: {stats.get('sta', 0)}, "
        f"PWR: {stats.get('pwr', 0)}, GUTS: {stats.get('guts', 0)}, WIT: {stats.get('wit', 0)}"
    )

    print("\n[INFO] === Timings (first run) ===")
    for key in [
        "mood",
        "turn",
        "year",
        "goal_name_with_g1",
        "criteria",
        "energy_percentage",
        "current_stats",
    ]:
        print(f"[INFO] {key}: {results[key][1]*1000:.2f} ms")
    print(f"[INFO] Total: {total_time*1000:.2f} ms")


def main():
    test_image = os.path.join(PROJECT_ROOT, "Speed_Test", "Status_tets.png")
    if not os.path.exists(test_image):
        print(f"[ERROR] Test image not found: {test_image}")
        sys.exit(1)

    _install_static_screenshot(test_image)

    # First run
    t0 = time.perf_counter()
    first_results = _status_checks()
    t1 = time.perf_counter()
    _print_first_run(first_results, t1 - t0)

    # Subsequent runs for average timing (10 runs total excluding the first one)
    run_times = []
    parts: Dict[str, list] = {
        "mood": [],
        "turn": [],
        "year": [],
        "goal_name_with_g1": [],
        "criteria": [],
        "energy_percentage": [],
        "current_stats": [],
    }

    for _ in range(100):
        t_run0 = time.perf_counter()
        r = _status_checks()
        t_run1 = time.perf_counter()
        run_times.append(t_run1 - t_run0)
        for k in parts.keys():
            parts[k].append(r[k][1])

    print("\n[INFO] === Average timings over 100 runs ===")
    for k, arr in parts.items():
        print(f"[INFO] {k}: {mean(arr)*1000:.2f} ms")
    print(f"[INFO] Total average: {mean(run_times)*1000:.2f} ms")


if __name__ == "__main__":
    main()



