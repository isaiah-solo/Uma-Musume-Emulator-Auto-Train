import os
import sys
from typing import List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _install_static_screenshot(image_path: str):
    from PIL import Image
    import utils.screenshot as adb_shot

    def take_screenshot_stub():
        return Image.open(image_path).convert("RGBA")

    adb_shot.take_screenshot = take_screenshot_stub  # type: ignore


def main():
    test_image = os.path.join(PROJECT_ROOT, "Speed_Test", "energy_test_2.png")
    if not os.path.exists(test_image):
        # Support alternative filename in case of typo
        alt = os.path.join(PROJECT_ROOT, "Speed_Test", "energy_test_2.png")
        test_image = test_image if os.path.exists(test_image) else alt
    if not os.path.exists(test_image):
        print(f"[ERROR] Test image not found: {test_image}")
        sys.exit(1)

    _install_static_screenshot(test_image)

    from core.state import check_energy_bar

    results: List[float] = []
    successes = 0
    total_runs = 100

    for i in range(1, total_runs + 1):
        value = check_energy_bar()
        results.append(value)
        rounded = round(value, 1)
        ok = (rounded == 100.0)
        if ok:
            successes += 1
        print(f"[RUN {i:03d}] energy={value:.2f}% (rounded={rounded:.1f}%) -> {ok}")

    accuracy = (successes / total_runs) * 100.0
    print(f"\n[RESULT] Accuracy: {accuracy:.2f}% ({successes}/{total_runs})")


if __name__ == "__main__":
    main()



