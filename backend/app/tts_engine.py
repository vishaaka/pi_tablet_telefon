import os
import hashlib
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import Contact


AUDIO_DIR = Path(__file__).resolve().parents[1] / "generated_audio"


@dataclass
class TtsResult:
    audio_url: str | None
    provider: str | None
    error: str | None = None


_hf_client = None
_piper_lock = threading.Lock()
VOICE_CACHE_VERSION = "v2"
VOICE_PROFILES = {
    "soft_female": {"pitch": 3, "tempo": 0.97, "filters": ["highpass=f=120", "equalizer=f=3000:t=q:w=1:g=2"]},
    "warm_male": {"pitch": -4, "tempo": 1.04, "filters": ["equalizer=f=180:t=q:w=1:g=3", "equalizer=f=3200:t=q:w=1:g=-2"]},
    "bright_female": {"pitch": 6, "tempo": 1.08, "filters": ["highpass=f=150", "equalizer=f=4200:t=q:w=1:g=4"]},
    "deep_male": {"pitch": -7, "tempo": 0.92, "filters": ["equalizer=f=120:t=q:w=1:g=5", "equalizer=f=2800:t=q:w=1:g=-3"]},
    "calm_female": {"pitch": 1, "tempo": 0.90, "filters": ["highpass=f=100", "equalizer=f=900:t=q:w=1:g=2"]},
    "clear_male": {"pitch": -2, "tempo": 1.00, "filters": ["highpass=f=90", "equalizer=f=2500:t=q:w=1:g=4"]},
    "default": {"pitch": 0, "tempo": 1.0, "filters": []},
}


def tts_status() -> dict:
    provider = _tts_provider()
    piper_model = Path(os.getenv("PI_PIPER_MODEL", "/opt/pi-tablet-ai/piper/tr_TR-dfki-medium.onnx"))
    return {
        "enabled": _tts_enabled(),
        "provider": provider,
        "space": os.getenv("HF_TTS_SPACE", "innoai/Edge-TTS-Text-to-Speech"),
        "api_name": os.getenv("HF_TTS_API_NAME", "/tts_interface"),
        "model": str(piper_model) if provider == "piper" else None,
        "configured": (
            provider in {"disabled", "none", "hf_space"}
            or (provider == "piper" and piper_model.is_file() and piper_model.with_suffix(".onnx.json").is_file())
        ),
    }


def synthesize_for_contact(call_id: str, contact: Contact, text: str) -> TtsResult:
    if not _tts_enabled():
        return TtsResult(audio_url=None, provider=None)

    try:
        provider = _tts_provider()
        if provider == "hf_space":
            return _hf_space_tts(call_id, contact, text)
        if provider == "piper":
            return _piper_tts(call_id, contact, text)
        return TtsResult(audio_url=None, provider=None, error=f"Unsupported TTS provider: {provider}")
    except Exception as error:
        return TtsResult(audio_url=None, provider=_tts_provider(), error=str(error))


def _tts_enabled() -> bool:
    value = os.getenv("PI_TTS_ENABLED_OVERRIDE") or os.getenv("PI_TTS_ENABLED", "false")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _tts_provider() -> str:
    return (os.getenv("PI_TTS_PROVIDER_OVERRIDE") or os.getenv("PI_TTS_PROVIDER", "disabled")).strip().lower()


def _hf_space_tts(call_id: str, contact: Contact, text: str) -> TtsResult:
    client = _get_hf_client()
    api_name = os.getenv("HF_TTS_API_NAME", "/tts_interface")
    voice = contact.tts_voice or os.getenv("HF_TTS_DEFAULT_VOICE", "tr-TR-EmelNeural - tr-TR (Female)")
    rate = int(os.getenv("HF_TTS_RATE", str(contact.tts_rate)))
    pitch = int(os.getenv("HF_TTS_PITCH", str(contact.tts_pitch)))

    result = client.predict(
        text=text[:900],
        voice=voice,
        rate=rate,
        pitch=pitch,
        api_name=api_name,
    )
    source = _find_audio_source(result)
    if not source:
        raise RuntimeError(f"TTS audio not found in result: {result!r}")

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(str(source).split("?")[0]).suffix or ".mp3"
    target = AUDIO_DIR / f"{int(time.time())}_{call_id[:8]}{suffix}"

    if str(source).startswith("http://") or str(source).startswith("https://"):
        urllib.request.urlretrieve(str(source), target)
    else:
        shutil.copyfile(str(source), target)

    _boost_audio_file(target)
    return TtsResult(audio_url=f"/audio/{target.name}", provider="hf_space")


def _piper_tts(call_id: str, contact: Contact, text: str) -> TtsResult:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.sha256(
        f"{VOICE_CACHE_VERSION}|{contact.voice}|{contact.tts_rate}|{contact.tts_pitch}|{text}".encode("utf-8")
    ).hexdigest()[:20]
    cached_target = AUDIO_DIR / f"cache_{cache_key}.mp3"
    if cached_target.is_file():
        return TtsResult(audio_url=f"/audio/{cached_target.name}", provider="piper-cache")

    stem = f"{int(time.time())}_{call_id[:8]}"
    source = AUDIO_DIR / f"{stem}.piper.wav"
    target = cached_target
    rate = max(-8, min(8, contact.tts_rate))
    model = os.getenv("PI_PIPER_MODEL", "/opt/pi-tablet-ai/piper/tr_TR-dfki-medium.onnx")
    command = [
        sys.executable,
        "-m",
        "piper",
        "-m",
        model,
        "-f",
        str(source),
        "--length-scale",
        str(max(0.78, min(1.25, 1.0 - (rate * 0.025)))),
        "--volume",
        os.getenv("PI_PIPER_VOLUME", "1.0"),
        "--",
        text[:900],
    ]
    with _piper_lock:
        if target.is_file():
            return TtsResult(audio_url=f"/audio/{target.name}", provider="piper-cache")
        try:
            subprocess.run(command, check=True, timeout=60)
            _convert_piper_audio(source, target, contact)
        finally:
            source.unlink(missing_ok=True)
    return TtsResult(audio_url=f"/audio/{target.name}", provider="piper")


def _convert_piper_audio(source: Path, target: Path, contact: Contact) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required for local Piper MP3 output")

    profile = VOICE_PROFILES.get(contact.voice, VOICE_PROFILES["default"])
    pitch = max(-10, min(10, contact.tts_pitch + int(profile["pitch"])))
    factor = 2 ** (pitch / 12)
    sample_rate = 22050
    gain_db = os.getenv("PI_TTS_GAIN_DB", "6").strip()
    filters = []
    if pitch != 0:
        filters.append(f"asetrate={sample_rate}*{factor:.6f}")
        filters.append(f"aresample={sample_rate}")
        filters.append(f"atempo={1 / factor:.6f}")
    filters.append(f"atempo={profile['tempo']}")
    filters.extend(profile["filters"])
    filters.extend([f"volume={gain_db}dB", "alimiter=limit=0.95"])
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-af",
        ",".join(filters),
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "96k",
        str(target),
    ]
    subprocess.run(command, check=True, timeout=45)


def _get_hf_client():
    global _hf_client
    if _hf_client is None:
        from gradio_client import Client

        space = os.getenv("HF_TTS_SPACE", "innoai/Edge-TTS-Text-to-Speech")
        token = os.getenv("HF_TOKEN") or None
        _hf_client = Client(space, token=token)
    return _hf_client


def _find_audio_source(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        if value.startswith(("http://", "https://")) or Path(value).exists():
            return value
        return None
    if isinstance(value, dict):
        for key in ("path", "name", "url"):
            found = _find_audio_source(value.get(key))
            if found:
                return found
    if isinstance(value, (list, tuple)):
        for item in value:
            found = _find_audio_source(item)
            if found:
                return found
    return None


def _boost_audio_file(path: Path) -> None:
    if os.getenv("PI_TTS_AUDIO_BOOST", "true").strip().lower() not in {"1", "true", "yes", "on"}:
        return
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return

    gain_db = os.getenv("PI_TTS_GAIN_DB", "8").strip()
    temp = path.with_name(f"{path.stem}.boost{path.suffix}")
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-af",
        f"volume={gain_db}dB,alimiter=limit=0.95",
        str(temp),
    ]
    try:
        subprocess.run(command, check=True, timeout=45)
        temp.replace(path)
    except Exception:
        if temp.exists():
            temp.unlink(missing_ok=True)
