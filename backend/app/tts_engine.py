import os
import shutil
import subprocess
import threading
import time
import urllib.request
import wave
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
_piper_voice = None
_piper_voice_path = None
_piper_lock = threading.Lock()


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
    from piper.config import SynthesisConfig

    voice = _get_piper_voice()
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    target = AUDIO_DIR / f"{int(time.time())}_{call_id[:8]}.wav"
    rate = max(-8, min(8, contact.tts_rate))
    syn_config = SynthesisConfig(
        length_scale=max(0.78, min(1.25, 1.0 - (rate * 0.025))),
        volume=float(os.getenv("PI_PIPER_VOLUME", "1.15")),
        normalize_audio=True,
    )
    with _piper_lock, wave.open(str(target), "wb") as wav_file:
        voice.synthesize_wav(text[:900], wav_file, syn_config=syn_config)

    _shape_piper_voice(target, contact.tts_pitch)
    _boost_audio_file(target)
    return TtsResult(audio_url=f"/audio/{target.name}", provider="piper")


def _get_piper_voice():
    global _piper_voice, _piper_voice_path
    from piper import PiperVoice

    model_path = os.getenv("PI_PIPER_MODEL", "/opt/pi-tablet-ai/piper/tr_TR-dfki-medium.onnx")
    if _piper_voice is None or _piper_voice_path != model_path:
        with _piper_lock:
            if _piper_voice is None or _piper_voice_path != model_path:
                _piper_voice = PiperVoice.load(model_path)
                _piper_voice_path = model_path
    return _piper_voice


def _shape_piper_voice(path: Path, pitch: int) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or pitch == 0:
        return

    pitch = max(-6, min(6, pitch))
    factor = 2 ** (pitch / 24)
    sample_rate = 22050
    temp = path.with_name(f"{path.stem}.voice{path.suffix}")
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-af",
        f"asetrate={sample_rate}*{factor:.6f},aresample={sample_rate},atempo={1 / factor:.6f}",
        str(temp),
    ]
    try:
        subprocess.run(command, check=True, timeout=45)
        temp.replace(path)
    except Exception:
        temp.unlink(missing_ok=True)


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
