import os
import subprocess
import time
import wave
from collections import deque
from pathlib import Path


RECORDING_DIR = Path(__file__).resolve().parents[1] / "recordings"


def capture_call_audio(call_id: str, seconds: int = 30) -> Path:
    RECORDING_DIR.mkdir(parents=True, exist_ok=True)
    target = RECORDING_DIR / f"{int(time.time())}_{call_id[:8]}.wav"
    device = os.getenv("PI_MIC_DEVICE", "plughw:2,0")
    rate = int(os.getenv("PI_MIC_RATE", "16000"))
    wait_seconds = float(os.getenv("PI_MIC_WAIT_SECONDS", "30"))
    max_seconds = float(os.getenv("PI_MIC_MAX_SECONDS", str(seconds)))
    min_seconds = float(os.getenv("PI_MIC_MIN_SECONDS", "0.8"))
    silence_seconds = float(os.getenv("PI_MIC_SILENCE_SECONDS", "2.0"))
    start_threshold = int(os.getenv("PI_MIC_START_THRESHOLD", "700"))
    silence_threshold = int(os.getenv("PI_MIC_SILENCE_THRESHOLD", "420"))
    chunk_ms = int(os.getenv("PI_MIC_CHUNK_MS", "100"))
    chunk_bytes = int(rate * 2 * chunk_ms / 1000)
    preroll_chunks = max(1, int(500 / chunk_ms))

    command = [
        "arecord",
        "-D",
        device,
        "-f",
        "S16_LE",
        "-r",
        str(rate),
        "-c",
        "1",
        "-t",
        "raw",
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    recorded = bytearray()
    preroll: deque[bytes] = deque(maxlen=preroll_chunks)
    started = False
    started_at = 0.0
    last_voice_at = 0.0
    begin = time.monotonic()

    try:
        if process.stdout is None:
            raise RuntimeError("arecord stdout unavailable")
        while True:
            now = time.monotonic()
            if not started and now - begin > wait_seconds:
                raise RuntimeError("Konusma algilanmadi")
            if started and now - started_at > max_seconds:
                break

            chunk = process.stdout.read(chunk_bytes)
            if not chunk:
                break
            level = _pcm16_rms(chunk)

            if not started:
                preroll.append(chunk)
                if level >= start_threshold:
                    started = True
                    started_at = now
                    last_voice_at = now
                    for old_chunk in preroll:
                        recorded.extend(old_chunk)
                    preroll.clear()
                continue

            recorded.extend(chunk)
            if level >= silence_threshold:
                last_voice_at = now
            if now - started_at >= min_seconds and now - last_voice_at >= silence_seconds:
                break
    finally:
        process.terminate()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()

    if len(recorded) < rate:
        raise RuntimeError("Ses kaydi cok kisa")

    with wave.open(str(target), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(bytes(recorded))
    return target


def _pcm16_rms(chunk: bytes) -> int:
    if not chunk:
        return 0
    total = 0
    count = len(chunk) // 2
    for index in range(0, len(chunk) - 1, 2):
        sample = int.from_bytes(chunk[index:index + 2], "little", signed=True)
        total += sample * sample
    return int((total / max(count, 1)) ** 0.5)
