import os
import sys
import time
import statistics
import subprocess

import cv2
import numpy as np


# ======================
# Editable settings
# ======================
# MuMu install root (where 'shell' or 'nx_device/12.0/shell' lives)
MUMU_FOLDER = r"J:\\MuMuPlayerGlobal"

# ADB serial of the same instance you are testing
# Examples for MuMu12: 127.0.0.1:16384, 16416, 16448, 16480, ...
SERIAL = "127.0.0.1:7555 "

# Instance and display ids for nemu_ipc
INSTANCE_ID = 2
DISPLAY_ID = 0  # try 0 or 1 if you see the wrong screen

# Benchmark settings
FRAMES = 60
WARMUP = 5
NEMU_TIMEOUT = 1.0  # seconds per IPC call
ADB_INTERVAL = None  # e.g., 0.2 sleep between ADB frames

# ADB binary (leave as 'adb' if in PATH)
ADB_PATH = "adb"

# Output images
OUTPUT_NEMU = os.path.join(os.path.dirname(__file__), "nemu_ipc_sample.png")
OUTPUT_ADB = os.path.join(os.path.dirname(__file__), "adb_sample.png")

# Postprocess controls for nemu_ipc image (match runtime behavior)
DO_FLIP = True            # vertically flip
CONVERT_TO_BGR = True     # BGRA -> BGR


def _ensure_repo_root_on_path():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if root not in sys.path:
        sys.path.insert(0, root)


_ensure_repo_root_on_path()


# Minimal standalone Nemu IPC wrapper (copied from standalone test)
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

        try:
            self.lib.nemu_connect.restype = ctypes.c_int
        except Exception:
            pass
        try:
            self.lib.nemu_disconnect.argtypes = [ctypes.c_int]
            self.lib.nemu_disconnect.restype = ctypes.c_int
        except Exception:
            pass
        try:
            self.lib.nemu_capture_display.argtypes = [
                ctypes.c_int, ctypes.c_int, ctypes.c_int,
                ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.c_void_p
            ]
            self.lib.nemu_capture_display.restype = ctypes.c_int
        except Exception:
            pass

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
        cid = self.lib.nemu_connect(self.nemu_folder, int(self.instance_id))
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
        arr = np.frombuffer(pixels, dtype=np.uint8).reshape((int(self.height), int(self.width), 4))
        return arr


def _convert_image(bg_ra: np.ndarray, flip: bool = True, to_bgr: bool = True) -> np.ndarray:
    image = bg_ra
    if to_bgr:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    if flip:
        image = cv2.flip(image, 0)
    return image


def benchmark_nemu(folder: str, instance_id: int, display_id: int, frames: int, warmup: int, timeout: float,
                   save_one: str):
    print(f"[nemu_ipc] folder='{folder}', instance_id={instance_id}, display_id={display_id}")
    impl = StandaloneNemuIpc(nemu_folder=folder, instance_id=instance_id, display_id=display_id)
    with impl:
        impl.get_resolution(timeout=timeout)
        for _ in range(max(0, warmup)):
            _ = impl.screenshot(timeout=timeout)
        times = []
        post_times = []
        saved = False
        for _ in range(frames):
            t0 = time.perf_counter()
            bgra = impl.screenshot(timeout=timeout)
            t1 = time.perf_counter()
            img = _convert_image(bgra, flip=DO_FLIP, to_bgr=CONVERT_TO_BGR)
            t2 = time.perf_counter()
            times.append(t1 - t0)
            post_times.append(t2 - t1)
            if not saved and save_one:
                cv2.imwrite(save_one, img)
                print(f"[nemu_ipc] saved: {os.path.abspath(save_one)}")
                saved = True
    return times, post_times


def adb_exec_out_screencap_png(serial: str) -> np.ndarray:
    proc = subprocess.run([ADB_PATH, '-s', serial, 'exec-out', 'screencap', '-p'],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0 or not proc.stdout:
        raise RuntimeError(proc.stderr.decode('utf-8', errors='ignore'))
    data = np.frombuffer(proc.stdout, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError('Failed to decode PNG from adb screencap')
    return img


def benchmark_adb(serial: str, frames: int, warmup: int, interval: float | None, save_one: str):
    print(f"[adb] serial='{serial}'")
    for _ in range(max(0, warmup)):
        _ = adb_exec_out_screencap_png(serial)
        if interval:
            time.sleep(interval)
    times = []
    saved = False
    for _ in range(frames):
        t0 = time.perf_counter()
        img = adb_exec_out_screencap_png(serial)
        t1 = time.perf_counter()
        times.append(t1 - t0)
        if not saved and save_one:
            cv2.imwrite(save_one, img)
            print(f"[adb] saved: {os.path.abspath(save_one)}")
            saved = True
        if interval:
            time.sleep(interval)
    return times


def _stats(xs):
    return {
        "min": min(xs),
        "mean": sum(xs) / len(xs),
        "median": statistics.median(xs),
        "p95": statistics.quantiles(xs, n=100)[94] if len(xs) >= 100 else max(xs),
        "max": max(xs),
    }


def _fmt(s):
    return (
        f"min={s['min']*1000:.1f}ms, avg={s['mean']*1000:.1f}ms, "
        f"med={s['median']*1000:.1f}ms, p95={s['p95']*1000:.1f}ms, max={s['max']*1000:.1f}ms"
    )


def main():
    print("==== Compare: nemu_ipc vs ADB ====")
    try:
        n_times, n_post = benchmark_nemu(
            folder=MUMU_FOLDER,
            instance_id=INSTANCE_ID,
            display_id=DISPLAY_ID,
            frames=FRAMES,
            warmup=WARMUP,
            timeout=NEMU_TIMEOUT,
            save_one=OUTPUT_NEMU,
        )
        n_total = [a + b for a, b in zip(n_times, n_post)]
        print("[nemu_ipc] call:   ", _fmt(_stats(n_times)))
        print("[nemu_ipc] post:   ", _fmt(_stats(n_post)))
        print("[nemu_ipc] total:  ", _fmt(_stats(n_total)))
        print(f"[nemu_ipc] FPS≈{len(n_total) / sum(n_total):.1f}")
    except Exception as e:
        print(f"[nemu_ipc] error: {e}")

    try:
        a_times = benchmark_adb(
            serial=SERIAL,
            frames=FRAMES,
            warmup=WARMUP,
            interval=ADB_INTERVAL,
            save_one=OUTPUT_ADB,
        )
        print("[ADB] total:      ", _fmt(_stats(a_times)))
        print(f"[ADB] FPS≈{len(a_times) / sum(a_times):.1f}")
    except Exception as e:
        print(f"[ADB] error: {e}")


if __name__ == "__main__":
    sys.exit(main())


