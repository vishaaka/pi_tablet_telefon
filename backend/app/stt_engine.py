import os
import subprocess
from pathlib import Path


def stt_status() -> dict:
    command = Path(os.getenv("PI_STT_COMMAND", "/opt/pi-tablet-ai/whisper.cpp/build/bin/whisper-cli"))
    model = Path(os.getenv("PI_STT_MODEL", "/opt/pi-tablet-ai/whisper.cpp/models/ggml-tiny.bin"))
    return {
        "provider": "whisper_cpp",
        "configured": command.is_file() and model.is_file(),
        "language": os.getenv("PI_STT_LANGUAGE", "tr"),
        "model": str(model),
    }


def transcribe_audio(audio_path: str) -> str:
    command = os.getenv("PI_STT_COMMAND", "/opt/pi-tablet-ai/whisper.cpp/build/bin/whisper-cli")
    model = os.getenv("PI_STT_MODEL", "/opt/pi-tablet-ai/whisper.cpp/models/ggml-tiny.bin")
    language = os.getenv("PI_STT_LANGUAGE", "tr")
    threads = os.getenv("PI_STT_THREADS", "3")
    output_base = f"{audio_path}.transcript"
    output_path = Path(f"{output_base}.txt")

    if not Path(command).is_file():
        raise RuntimeError(f"whisper-cli bulunamadi: {command}")
    if not Path(model).is_file():
        raise RuntimeError(f"Whisper modeli bulunamadi: {model}")

    try:
        subprocess.run(
            [
                command,
                "-m",
                model,
                "-f",
                audio_path,
                "-l",
                language,
                "-t",
                threads,
                "-nt",
                "-otxt",
                "-of",
                output_base,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=float(os.getenv("PI_STT_TIMEOUT_SECONDS", "35")),
        )
        transcript = output_path.read_text(encoding="utf-8").strip()
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or "").strip()
        raise RuntimeError(f"Whisper transkripsiyon hatasi: {detail[-240:]}") from error
    finally:
        output_path.unlink(missing_ok=True)

    transcript = " ".join(transcript.split())
    if not transcript:
        raise RuntimeError("Insan sesi algilandi ancak konusma anlasilamadi")
    return transcript
