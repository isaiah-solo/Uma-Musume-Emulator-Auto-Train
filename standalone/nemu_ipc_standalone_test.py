import os
import sys
import time
import statistics

import cv2
import numpy as np


# ======================
# Editable settings
# ======================
# Absolute path to MuMuPlayer-12.0 installation folder (where 'shell' directory resides)
MUMU_FOLDER = r"J:\MuMuPlayerGlobal"

# Either set SERIAL to derive instance id automatically
#   Examples: '127.0.0.1:16384', '127.0.0.1:16416', '127.0.0.1:7555' (classic)
SERIAL = "127.0.0.1:16480"

# Or set INSTANCE_ID explicitly (0-based). If not None, this overrides SERIAL-derived id.
INSTANCE_ID = 2

# Display ID, usually 0
DISPLAY_ID = 0

# Benchmark settings
FRAMES = 100
WARMUP = 5
TIMEOUT = 1.0  # seconds per IPC call
SLEEP_INTERVAL = None  # e.g., 0.2 to simulate production cadence

# Image output (a processed PNG will always be saved here)
OUTPUT_IMAGE = os.path.join(os.path.dirname(__file__), "nemu_ipc_sample.png")

# Postprocess controls (match runtime behavior in Alas)
DO_FLIP = True            # vertically flip
CONVERT_TO_RGB = True     # BGRA -> RGB


def _ensure_repo_root_on_path():
    # Allow running from repo root or this file's directory
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if root not in sys.path:
        sys.path.insert(0, root)


_ensure_repo_root_on_path()

# Standalone minimal Nemu IPC wrapper (no project imports)
import ctypes  # noqa: E402
from concurrent.futures import ThreadPoolExecutor, TimeoutError  # noqa: E402


class NemuIpcIncompatible(Exception):
    pass


class NemuIpcError(Exception):
    pass


class StandaloneNemuIpc:
    def __init__(self, nemu_folder: str, instance_id: int, display_id: int = 0):
        self.nemu_folder = nemu_folder
        self.instance_id = instance_id
        self.display_id = display_id
        self.connect_id = 0
        self.width = 0
        self.height = 0

        # Try to load DLL from possible locations
        candidates = [
            os.path.abspath(os.path.join(nemu_folder, './shell/sdk/external_renderer_ipc.dll')),
            os.path.abspath(os.path.join(nemu_folder, './nx_device/12.0/shell/sdk/external_renderer_ipc.dll')),
        ]
        self.lib = None
        last_err = None
        for dll in candidates:
            if not os.path.exists(dll):
                continue
            try:
                self.lib = ctypes.CDLL(dll)
                break
            except OSError as e:
                last_err = e
                continue
        if self.lib is None:
            raise NemuIpcIncompatible(
                f'Cannot load external_renderer_ipc.dll. Tried: {candidates}. Last error: {last_err}'
            )

        # Function prototypes: keep loose for nemu_connect to mimic project behavior
        # Do not set argtypes for nemu_connect; pass Python str directly
        try:
            self.lib.nemu_connect.restype = ctypes.c_int
        except Exception:
            pass
        try:
            self.lib.nemu_disconnect.argtypes = [ctypes.c_int]
            self.lib.nemu_disconnect.restype = ctypes.c_int
        except Exception:
            pass
        # int nemu_capture_display(int connect_id, int display_id, int length, int* w, int* h, unsigned char* pixels)
        self.lib.nemu_capture_display.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.c_void_p
        ]
        self.lib.nemu_capture_display.restype = ctypes.c_int

        self._executor = ThreadPoolExecutor(max_workers=1)

    @staticmethod
    def serial_to_id(serial: str):
        try:
            port = int(serial.split(':')[1])
        except (IndexError, ValueError):
            return None
        index, offset = divmod(port - 16384 + 16, 32)
        offset -= 16
        if 0 <= index < 32 and offset in [-2, -1, 0, 1, 2]:
            return index
        return None

    def _run_with_timeout(self, func, *args, timeout: float | None = None):
        if timeout is None:
            return func(*args)
        fut = self._executor.submit(func, *args)
        try:
            return fut.result(timeout=timeout)
        except TimeoutError:
            fut.cancel()
            raise NemuIpcError('IPC call timeout')

    def connect(self, timeout: float | None = None):
        if self.connect_id:
            return
        # Call on main thread without threadpool first, passing Python str
        cid = self.lib.nemu_connect(self.nemu_folder, int(self.instance_id))
        # If still zero and timeout provided, try once via thread with bytes
        if cid == 0 and timeout is not None:
            folder_bytes = os.fsencode(self.nemu_folder)
            cid = self._run_with_timeout(self.lib.nemu_connect, folder_bytes, int(self.instance_id), timeout=timeout)
        if cid == 0:
            raise NemuIpcError('nemu_connect failed. Check folder path and that emulator is running')
        self.connect_id = int(cid)

    def disconnect(self):
        if not self.connect_id:
            return
        try:
            self.lib.nemu_disconnect(int(self.connect_id))
        finally:
            self.connect_id = 0

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def get_resolution(self, timeout: float | None = None):
        if not self.connect_id:
            self.connect(timeout=timeout)
        w_ptr = ctypes.pointer(ctypes.c_int(0))
        h_ptr = ctypes.pointer(ctypes.c_int(0))
        null = ctypes.c_void_p()
        ret = self._run_with_timeout(
            self.lib.nemu_capture_display,
            int(self.connect_id), int(self.display_id), 0, w_ptr, h_ptr, null,
            timeout=timeout,
        )
        if int(ret) > 0:
            raise NemuIpcError('nemu_capture_display failed in get_resolution')
        self.width = w_ptr.contents.value
        self.height = h_ptr.contents.value

    def screenshot(self, timeout: float | None = None) -> np.ndarray:
        if not self.connect_id:
            self.connect(timeout=timeout)
        if self.width == 0 or self.height == 0:
            self.get_resolution(timeout=timeout)
        w_ptr = ctypes.pointer(ctypes.c_int(int(self.width)))
        h_ptr = ctypes.pointer(ctypes.c_int(int(self.height)))
        length = int(self.width * self.height * 4)
        pixels = (ctypes.c_ubyte * length)()
        ret = self._run_with_timeout(
            self.lib.nemu_capture_display,
            int(self.connect_id), int(self.display_id), length, w_ptr, h_ptr, ctypes.byref(pixels),
            timeout=timeout,
        )
        if int(ret) > 0:
            raise NemuIpcError('nemu_capture_display failed in screenshot')
        # Build numpy array from ctypes buffer
        arr = np.frombuffer(pixels, dtype=np.uint8)
        arr = arr.reshape((int(self.height), int(self.width), 4))
        return arr


def _derive_instance_id(serial: str):
    if not serial:
        return None
    return StandaloneNemuIpc.serial_to_id(serial)


def _convert_image(bg_ra: np.ndarray, flip: bool = True, to_rgb: bool = True) -> np.ndarray:
    image = bg_ra
    if to_rgb:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
    if flip:
        image = cv2.flip(image, 0)
    return image


def run_benchmark(folder: str, instance_id: int, display_id: int, frames: int, warmup: int, timeout: float,
                  sleep_interval: float | None, save_one: str, flip: bool, to_rgb: bool):
    print(f"Nemu IPC benchmark: folder='{folder}', instance_id={instance_id}, display_id={display_id}")
    print(f"Frames={frames}, Warmup={warmup}, Timeout={timeout}s, SleepInterval={sleep_interval}")

    impl = StandaloneNemuIpc(nemu_folder=folder, instance_id=instance_id, display_id=display_id)
    with impl:
        # Prime resolution to avoid first-call cost in stats
        impl.get_resolution()

        # Warmup
        for _ in range(max(0, warmup)):
            _ = impl.screenshot(timeout=timeout)
            if sleep_interval:
                time.sleep(sleep_interval)

        # Measure total time per screenshot call
        times = []
        post_times = []
        saved = False
        for _ in range(frames):
            t0 = time.perf_counter()
            bgra = impl.screenshot(timeout=timeout)
            t1 = time.perf_counter()
            img = _convert_image(bgra, flip=flip, to_rgb=to_rgb)
            t2 = time.perf_counter()

            times.append(t1 - t0)
            post_times.append(t2 - t1)

            if not saved and save_one:
                os.makedirs(os.path.dirname(os.path.abspath(save_one)) or '.', exist_ok=True)
                cv2.imwrite(save_one, img)
                print(f"Saved sample frame to: {os.path.abspath(save_one)}")
                saved = True

            if sleep_interval:
                time.sleep(sleep_interval)

    def stats(xs):
        return {
            "min": min(xs),
            "mean": sum(xs) / len(xs),
            "median": statistics.median(xs),
            "p95": statistics.quantiles(xs, n=100)[94],
            "max": max(xs),
        }

    icp = stats(times)
    post = stats(post_times)
    per_frame_total = [a + b for a, b in zip(times, post_times)]
    total = stats(per_frame_total)
    fps = len(per_frame_total) / sum(per_frame_total)

    def fmt(s):
        return (
            f"min={s['min']*1000:.1f}ms, avg={s['mean']*1000:.1f}ms, "
            f"med={s['median']*1000:.1f}ms, p95={s['p95']*1000:.1f}ms, max={s['max']*1000:.1f}ms"
        )

    print("\nResults:")
    print(f"- IPC call (impl.screenshot): {fmt(icp)}")
    print(f"- Postprocess (convert+flip): {fmt(post)}")
    print(f"- Total per frame: {fmt(total)}  |  FPS≈{fps:.1f}")


def main():
    folder = MUMU_FOLDER
    instance_id = INSTANCE_ID if INSTANCE_ID is not None else _derive_instance_id(SERIAL)
    if instance_id is None:
        print("Error: Unable to derive instance id from SERIAL. Set INSTANCE_ID explicitly.")
        return 2

    try:
        run_benchmark(
            folder=folder,
            instance_id=instance_id,
            display_id=DISPLAY_ID,
            frames=FRAMES,
            warmup=WARMUP,
            timeout=TIMEOUT,
            sleep_interval=SLEEP_INTERVAL,
            save_one=OUTPUT_IMAGE,
            flip=DO_FLIP,
            to_rgb=CONVERT_TO_RGB,
        )
        return 0
    except (NemuIpcIncompatible, NemuIpcError) as e:
        print(f"nemu_ipc error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())


