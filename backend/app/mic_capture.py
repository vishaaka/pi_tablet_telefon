import os
import subprocess
import time
from pathlib import Path


RECORDING_DIR = Path(__file__).resolve().parents[1] / "recordings"


def capture_call_audio(call_id: str, seconds: int = 5) -> Path:
    RECORDING_DIR.mkdir(parents=True, exist_ok=True)
    duration = max(2, min(seconds, 10))
    target = RECORDING_DIR / f"{int(time.time())}_{call_id[:8]}.wav"
    device = os.getenv("PI_MIC_DEVICE", "plughw:2,0")
    rate = os.getenv("PI_MIC_RATE", "16000")

    command = [
        "arecord",
        "-D",
        device,
        "-f",
        "S16_LE",
        "-r",
        rate,
        "-c",
        "1",
        "-d",
        str(duration),
        str(target),
    ]
    subprocess.run(command, check=True, timeout=duration + 8)
    return target
