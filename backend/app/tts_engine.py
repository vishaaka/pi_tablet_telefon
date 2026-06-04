import os
import shutil
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


def tts_status() -> dict:
    provider = os.getenv("PI_TTS_PROVIDER", "disabled").strip().lower()
    return {
        "enabled": _tts_enabled(),
        "provider": provider,
        "space": os.getenv("HF_TTS_SPACE", "innoai/Edge-TTS-Text-to-Speech"),
        "api_name": os.getenv("HF_TTS_API_NAME", "/tts_interface"),
        "configured": provider in {"disabled", "none"} or provider == "hf_space",
    }


def synthesize_for_contact(call_id: str, contact: Contact, text: str) -> TtsResult:
    if not _tts_enabled():
        return TtsResult(audio_url=None, provider=None)

    provider = os.getenv("PI_TTS_PROVIDER", "hf_space").strip().lower()
    if provider != "hf_space":
        return TtsResult(audio_url=None, provider=None, error=f"Unsupported TTS provider: {provider}")

    try:
        return _hf_space_tts(call_id, contact, text)
    except Exception as error:
        return TtsResult(audio_url=None, provider="hf_space", error=str(error))


def _tts_enabled() -> bool:
    return os.getenv("PI_TTS_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


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

    return TtsResult(audio_url=f"/audio/{target.name}", provider="hf_space")


def _get_hf_client():
    global _hf_client
    if _hf_client is None:
        from gradio_client import Client

        space = os.getenv("HF_TTS_SPACE", "innoai/Edge-TTS-Text-to-Speech")
        token = os.getenv("HF_TOKEN") or None
        _hf_client = Client(space, hf_token=token)
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
