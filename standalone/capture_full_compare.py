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
# General
FRAMES = 60
WARMUP = 5

# Toggle methods
ENABLE_NEMU_IPC = True
ENABLE_ADB = True
ENABLE_UIAUTOMATOR2 = True      # requires: pip install uiautomator2
ENABLE_DROIDCAST_HTTP = True    # requires: pip install requests; and APK in ./bin/DroidCast/
# Experimental: If your DroidCast provides another endpoint for raw frames, set URL below and enable
ENABLE_DROIDCAST_RAW = False

# MuMu / nemu_ipc
MUMU_FOLDER = r"J:\\MuMuPlayerGlobal"
INSTANCE_ID = 2
DISPLAY_ID = 0
NEMU_TIMEOUT = 1.0

# ADB
ADB_PATH = "adb"
SERIAL = "127.0.0.1:7555"
ADB_INTERVAL = None

# DroidCast (HTTP)
DROIDCAST_APK = os.path.join(os.path.dirname(__file__), '..', 'bin', 'DroidCast', 'DroidCast_raw-release-1.0.apk')
DROIDCAST_REMOTE_PORT = 53516
DROIDCAST_LOCAL_PORT = 20694
DROIDCAST_WIDTH = 1080
DROIDCAST_HEIGHT = 1920

# Output images
OUT_DIR = os.path.dirname(__file__)
OUT_NEMU = os.path.join(OUT_DIR, 'nemu_ipc_sample.png')
OUT_ADB = os.path.join(OUT_DIR, 'adb_sample.png')
OUT_U2 = os.path.join(OUT_DIR, 'uiautomator2_sample.png')
OUT_DROIDCAST = os.path.join(OUT_DIR, 'droidcast_sample.jpg')
OUT_DROIDCAST_RAW = os.path.join(OUT_DIR, 'droidcast_raw_sample.jpg')

# nemu_ipc postprocess
DO_FLIP = True
CONVERT_TO_BGR = True


def _ensure_repo_root_on_path():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if root not in sys.path:
        sys.path.insert(0, root)


_ensure_repo_root_on_path()


# Minimal standalone Nemu IPC wrapper
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


def _table_row(method: str, stats: dict, fps: float) -> str:
    return f"| {method} | {stats['mean']*1000:.1f} | {stats['median']*1000:.1f} | {stats['p95']*1000:.1f} | {fps:.1f} |"


def bench_nemu_ipc(save_one: str):
    print(f"[nemu_ipc] folder='{MUMU_FOLDER}', instance_id={INSTANCE_ID}, display_id={DISPLAY_ID}")
    impl = StandaloneNemuIpc(nemu_folder=MUMU_FOLDER, instance_id=INSTANCE_ID, display_id=DISPLAY_ID)
    with impl:
        impl.get_resolution(timeout=NEMU_TIMEOUT)
        for _ in range(max(0, WARMUP)):
            _ = impl.screenshot(timeout=NEMU_TIMEOUT)
        times = []
        post_times = []
        saved = False
        for _ in range(FRAMES):
            t0 = time.perf_counter()
            bgra = impl.screenshot(timeout=NEMU_TIMEOUT)
            t1 = time.perf_counter()
            img = _convert_image(bgra, flip=DO_FLIP, to_bgr=CONVERT_TO_BGR)
            t2 = time.perf_counter()
            times.append(t1 - t0)
            post_times.append(t2 - t1)
            if not saved and save_one:
                cv2.imwrite(save_one, img)
                print(f"[nemu_ipc] saved: {os.path.abspath(save_one)}")
                saved = True
    total = [a + b for a, b in zip(times, post_times)]
    stats_call = _stats(times)
    stats_post = _stats(post_times)
    stats_total = _stats(total)
    fps = len(total) / sum(total)
    print("[nemu_ipc] call:   ", _fmt(stats_call))
    print("[nemu_ipc] post:   ", _fmt(stats_post))
    print("[nemu_ipc] total:  ", _fmt(stats_total))
    print(f"[nemu_ipc] FPS≈{fps:.1f}")
    return (stats_total, fps)


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


def bench_adb(save_one: str):
    print(f"[adb] serial='{SERIAL}'")
    for _ in range(max(0, WARMUP)):
        _ = adb_exec_out_screencap_png(SERIAL)
        if ADB_INTERVAL:
            time.sleep(ADB_INTERVAL)
    times = []
    saved = False
    for _ in range(FRAMES):
        t0 = time.perf_counter()
        img = adb_exec_out_screencap_png(SERIAL)
        t1 = time.perf_counter()
        times.append(t1 - t0)
        if not saved and save_one:
            cv2.imwrite(save_one, img)
            print(f"[adb] saved: {os.path.abspath(save_one)}")
            saved = True
        if ADB_INTERVAL:
            time.sleep(ADB_INTERVAL)
    stats_total = _stats(times)
    fps = len(times) / sum(times)
    print("[ADB] total:      ", _fmt(stats_total))
    print(f"[ADB] FPS≈{fps:.1f}")
    return (stats_total, fps)


def bench_uiautomator2(save_one: str):
    print("[uiautomator2] starting")
    try:
        import uiautomator2 as u2
    except Exception as e:
        print(f"[uiautomator2] import error: {e}")
        return
    d = u2.connect(SERIAL)
    # Warmup
    for _ in range(max(0, WARMUP)):
        _ = d.screenshot(format='opencv')
    times = []
    saved = False
    for _ in range(FRAMES):
        t0 = time.perf_counter()
        img = d.screenshot(format='opencv')
        t1 = time.perf_counter()
        times.append(t1 - t0)
        if not saved and save_one:
            cv2.imwrite(save_one, img)
            print(f"[uiautomator2] saved: {os.path.abspath(save_one)}")
            saved = True
    stats_total = _stats(times)
    fps = len(times) / sum(times)
    print("[uiautomator2] total:", _fmt(stats_total))
    print(f"[uiautomator2] FPS≈{fps:.1f}")
    return (stats_total, fps)


def adb_forward(local: int, remote: int):
    subprocess.run([ADB_PATH, '-s', SERIAL, 'forward', f'tcp:{local}', f'tcp:{remote}'], check=False,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def start_droidcast():
    # Push APK if present, then start via app_process (raw variant works for HTTP too)
    if os.path.exists(DROIDCAST_APK):
        subprocess.run([ADB_PATH, '-s', SERIAL, 'push', DROIDCAST_APK, '/data/local/tmp/DroidCast_raw.apk'],
                       check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        # Start in background to avoid blocking
        cmd = "sh -c 'CLASSPATH=/data/local/tmp/DroidCast_raw.apk app_process / ink.mol.droidcast_raw.Main >/dev/null 2>&1 &'"
        try:
            subprocess.run([ADB_PATH, '-s', SERIAL, 'shell', cmd], check=False,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
        except subprocess.TimeoutExpired:
            # Background start may return slowly; proceed
            pass
    adb_forward(DROIDCAST_LOCAL_PORT, DROIDCAST_REMOTE_PORT)


def bench_droidcast_http(save_one: str):
    print("[DroidCast] HTTP mode")
    try:
        import requests
    except Exception as e:
        print(f"[DroidCast] requests module missing: {e}")
        return
    start_droidcast()
    base = f"http://127.0.0.1:{DROIDCAST_LOCAL_PORT}"
    url = f"{base}/preview?width={DROIDCAST_WIDTH}&height={DROIDCAST_HEIGHT}"
    # Wait until ready
    ready = False
    for _ in range(10):
        try:
            r = requests.get(url, timeout=1.5)
            if r.ok and r.content:
                ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)
    if not ready:
        print("[DroidCast] not ready after retries; skipping")
        return
    # Warmup
    for _ in range(max(0, WARMUP)):
        r = requests.get(url, timeout=3)
        _ = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
    times = []
    saved = False
    for _ in range(FRAMES):
        t0 = time.perf_counter()
        r = requests.get(url, timeout=3)
        img = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
        t1 = time.perf_counter()
        times.append(t1 - t0)
        if not saved and save_one:
            cv2.imwrite(save_one, img)
            print(f"[DroidCast] saved: {os.path.abspath(save_one)}")
            saved = True
    stats_total = _stats(times)
    fps = len(times) / sum(times)
    print("[DroidCast] total:", _fmt(stats_total))
    print(f"[DroidCast] FPS≈{fps:.1f}")
    return (stats_total, fps)


def bench_droidcast_raw_http(save_one: str):
    # Experimental: use same HTTP endpoint but labeled as raw; adjust if your server exposes a raw frame URL
    try:
        import requests
    except Exception as e:
        print(f"[DroidCast_raw] requests module missing: {e}")
        return None
    base = f"http://127.0.0.1:{DROIDCAST_LOCAL_PORT}"
    # If your server has a different path for raw frames, change below
    url = f"{base}/preview?width={DROIDCAST_WIDTH}&height={DROIDCAST_HEIGHT}"
    # Warmup
    for _ in range(max(0, WARMUP)):
        r = requests.get(url, timeout=3)
        _ = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
    times = []
    saved = False
    for _ in range(FRAMES):
        t0 = time.perf_counter()
        r = requests.get(url, timeout=3)
        img = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
        t1 = time.perf_counter()
        times.append(t1 - t0)
        if not saved and save_one:
            cv2.imwrite(save_one, img)
            print(f"[DroidCast_raw] saved: {os.path.abspath(save_one)}")
            saved = True
    stats_total = _stats(times)
    fps = len(times) / sum(times)
    print("[DroidCast_raw] total:", _fmt(stats_total))
    print(f"[DroidCast_raw] FPS≈{fps:.1f}")
    return (stats_total, fps)


def main():
    print("==== Full capture compare ====")
    rows = []
    if ENABLE_NEMU_IPC:
        try:
            stats, fps = bench_nemu_ipc(OUT_NEMU)
            rows.append(("nemu_ipc", stats, fps))
        except Exception as e:
            print(f"[nemu_ipc] error: {e}")
    if ENABLE_ADB:
        try:
            stats, fps = bench_adb(OUT_ADB)
            rows.append(("ADB", stats, fps))
        except Exception as e:
            print(f"[ADB] error: {e}")
    if ENABLE_UIAUTOMATOR2:
        try:
            stats, fps = bench_uiautomator2(OUT_U2)
            rows.append(("uiautomator2", stats, fps))
        except Exception as e:
            print(f"[uiautomator2] error: {e}")
    if ENABLE_DROIDCAST_HTTP:
        try:
            stats, fps = bench_droidcast_http(OUT_DROIDCAST)
            rows.append(("DroidCast", stats, fps))
        except Exception as e:
            print(f"[DroidCast] error: {e}")
    if ENABLE_DROIDCAST_RAW:
        try:
            stats, fps = bench_droidcast_raw_http(OUT_DROIDCAST_RAW)
            if stats:
                rows.append(("DroidCast_raw", stats, fps))
        except Exception as e:
            print(f"[DroidCast_raw] error: {e}")

    if rows:
        print("\n==== Summary Table ====")
        print("| Method | Avg (ms) | Median (ms) | P95 (ms) | FPS |")
        print("|---|---:|---:|---:|---:|")
        for name, stats, fps in rows:
            print(_table_row(name, stats, fps))


if __name__ == "__main__":
    sys.exit(main())


