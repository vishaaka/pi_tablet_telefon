import shutil
import subprocess
import time
from pathlib import Path


class HailoRuntime:
    """Host-side Hailo status and capability detection."""

    def __init__(self) -> None:
        self._cache: tuple[float, dict] | None = None

    def status(self) -> dict:
        now = time.monotonic()
        if self._cache and now - self._cache[0] < 15:
            return self._cache[1]

        hailortcli = shutil.which("hailortcli")
        device_nodes = sorted(str(path) for path in Path("/dev").glob("hailo*"))
        lspci = _run(["lspci"])
        identify = _run([hailortcli, "fw-control", "identify"]) if hailortcli else _Result(False, "hailortcli not found")
        rpicam_assets = _existing_assets(
            [
                "/usr/share/rpi-camera-assets/hailo_yolov8_inference.json",
                "/usr/share/rpi-camera-assets/hailo_yolov6_inference.json",
                "/usr/share/rpi-camera-assets/hailo_yolox_inference.json",
            ]
        )
        hailo_visible = "hailo" in lspci.output.lower() or bool(device_nodes)
        enabled = bool(hailortcli and device_nodes and identify.ok)
        status = {
            "enabled": enabled,
            "hardware_visible": hailo_visible,
            "device_nodes": device_nodes,
            "hailortcli": hailortcli,
            "identify_ok": identify.ok,
            "board": _first_matching_line(identify.output, ("Board Name", "Device Architecture", "Firmware Version")),
            "rpicam_hailo_assets": rpicam_assets,
            "can_offload": {
                "vision": enabled and bool(rpicam_assets),
                "llm": False,
                "stt": False,
                "tts": False,
            },
            "recommended_use": "Use Hailo for camera vision inference; keep chat, STT and TTS on CPU/services.",
            "note": "Hailo-8/8L accelerates compiled neural-network inference, mainly vision pipelines on this project.",
        }
        self._cache = (now, status)
        return status


class _Result:
    def __init__(self, ok: bool, output: str) -> None:
        self.ok = ok
        self.output = output


def _run(command: list[str | None], timeout: float = 4) -> _Result:
    if not command[0]:
        return _Result(False, "")
    try:
        completed = subprocess.run(
            [str(part) for part in command if part],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        return _Result(completed.returncode == 0, completed.stdout.strip())
    except Exception as error:
        return _Result(False, str(error))


def _existing_assets(paths: list[str]) -> list[str]:
    return [path for path in paths if Path(path).is_file()]


def _first_matching_line(output: str, prefixes: tuple[str, ...]) -> str | None:
    for line in output.splitlines():
        if any(line.strip().startswith(prefix) for prefix in prefixes):
            return line.strip()
    return None


hailo_runtime = HailoRuntime()
