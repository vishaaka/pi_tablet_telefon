import base64
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from .fast_chat import scripted_reply
from .models import Contact


CHILD_SAFE_PROMPT = (
    "Kullanici bir cocuk olabilir. Yasina uygun, sade, temiz ve sakin Turkce kullan. "
    "Kisa, net, sevecen ve ogretici cevap ver. Korkutucu, yetiskinlere uygun, kufurlu, cinsel, "
    "siddetli veya tehlikeli icerige girme. Tehlikeli bir istek olursa nazikce reddet ve guvenli "
    "bir yetiskinden yardim istemesini soyle. Tibbi, hukuki veya acil durumda ebeveyn ya da guvenilir "
    "bir yetiskine haber vermesini oner. En fazla 12-16 kelimelik tam cumleler kur."
)


@dataclass
class CallSession:
    contact: Contact
    mode: str = "voice"
    history: list[dict[str, str]] = field(default_factory=list)
    fast_turn: int = 0


@dataclass
class AiReply:
    text: str
    provider: str
    transcript: str | None = None


def ai_status() -> dict:
    provider = _ai_provider()
    return {
        "provider": provider,
        "model": _ai_model("local-persona"),
        "configured": _provider_configured(provider),
    }


def generate_reply(session: CallSession, user_text: str) -> AiReply:
    if os.getenv("PI_FAST_CHAT_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}:
        reply, _ = scripted_reply(session.contact, user_text, session.fast_turn)
        session.fast_turn += 1
        return AiReply(text=reply, provider="scripted")

    provider = _ai_provider()
    if provider == "llama_cpp":
        try:
            return _llama_cpp_reply(session, user_text)
        except Exception:
            return AiReply(text=_local_reply(session.contact, user_text), provider="local-fallback")

    if provider == "gemini" and os.getenv("GEMINI_API_KEY"):
        try:
            return _gemini_reply(session, user_text)
        except Exception as error:
            return AiReply(text=_local_reply(session.contact, user_text, f"Gemini hatasi: {error}"), provider="local-fallback")

    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        try:
            return _openai_reply(session, user_text)
        except Exception as error:
            return AiReply(text=_local_reply(session.contact, user_text, f"AI servis hatasi: {error}"), provider="local-fallback")

    return AiReply(text=_local_reply(session.contact, user_text), provider="local")


def generate_reply_from_audio(session: CallSession, audio_path: str, prompt_text: str) -> AiReply:
    provider = _ai_provider()
    if provider == "gemini" and os.getenv("GEMINI_API_KEY"):
        try:
            return _gemini_audio_reply(session, audio_path, prompt_text)
        except Exception as error:
            return AiReply(text=_local_reply(session.contact, "", f"Sesli AI hatasi: {error}"), provider="local-fallback")

    try:
        from .stt_engine import transcribe_audio

        transcript = transcribe_audio(audio_path)
        reply = generate_reply(session, transcript)
        reply.transcript = transcript
        return reply
    except Exception:
        return AiReply(text="Seni tam duyamadım. Biraz daha yakından tekrar söyler misin?", provider="local-fallback")


def _provider_configured(provider: str) -> bool:
    provider = provider.strip().lower()
    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))
    if provider == "gemini":
        return bool(os.getenv("GEMINI_API_KEY"))
    if provider == "llama_cpp":
        return True
    return True


def _ai_provider() -> str:
    return os.getenv("PI_AI_PROVIDER_OVERRIDE", os.getenv("PI_AI_PROVIDER", "local")).strip().lower()


def _ai_model(default: str) -> str:
    return os.getenv("PI_AI_MODEL_OVERRIDE", os.getenv("PI_AI_MODEL", default))


def _ai_api_base(default: str) -> str:
    return os.getenv("PI_AI_API_BASE_OVERRIDE", os.getenv("PI_AI_API_BASE", default)).rstrip("/")


def _llama_cpp_reply(session: CallSession, user_text: str) -> AiReply:
    base_url = _ai_api_base("http://127.0.0.1:8081/v1")
    model = _ai_model("Qwen/Qwen3-0.6B-GGUF:Q8_0")
    return _openai_compatible_reply(session, user_text, base_url, model, None, "llama_cpp")


def _openai_reply(session: CallSession, user_text: str) -> AiReply:
    api_key = os.environ["OPENAI_API_KEY"]
    base_url = os.getenv("PI_AI_API_BASE", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("PI_AI_MODEL", "gpt-4o-mini")
    return _openai_compatible_reply(session, user_text, base_url, model, api_key, "openai")


def _openai_compatible_reply(
    session: CallSession,
    user_text: str,
    base_url: str,
    model: str,
    api_key: str | None,
    provider: str,
) -> AiReply:
    url = f"{base_url}/chat/completions"

    system_prompt = session.contact.system_prompt or session.contact.persona
    messages = [
        {
            "role": "system",
            "content": (
                system_prompt
                + " Bu bir telefon gorusmesi simulasyonu. Gercek kisi oldugunu iddia etme; AI karakter olarak konus. "
                + CHILD_SAFE_PROMPT
                + " Yalnizca Turkce cevap ver. Dusunme metni yazma. /no_think"
            ),
        }
    ]
    messages.extend(session.history[-8:])
    messages.append({"role": "user", "content": user_text})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.65,
        "max_tokens": 96,
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=float(os.getenv("PI_AI_TIMEOUT_SECONDS", "35"))) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code}: {body[:240]}") from error

    reply = data["choices"][0]["message"]["content"].strip()
    return AiReply(text=_clean_phone_reply(reply), provider=provider)


def _gemini_reply(session: CallSession, user_text: str) -> AiReply:
    api_key = os.environ["GEMINI_API_KEY"]
    model = os.getenv("PI_AI_MODEL", "gemini-flash-latest")
    base_url = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
    url = f"{base_url}/models/{model}:generateContent"

    system_prompt = session.contact.system_prompt or session.contact.persona
    history_text = "\n".join(
        f"{item['role']}: {item['content']}"
        for item in session.history[-8:]
    )
    prompt = (
        f"{system_prompt}\n"
        "Bu bir telefon gorusmesi simulasyonu. Gercek kisi oldugunu iddia etme; AI karakter olarak konus. "
        f"{CHILD_SAFE_PROMPT}\n\n"
        f"Konusma gecmisi:\n{history_text}\n\n"
        f"Kullanici: {user_text}\n"
        f"{session.contact.name}:"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 180,
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code}: {body[:240]}") from error

    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini bos cevap dondu")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError("Gemini cevap metni bos")
    return AiReply(text=_clean_phone_reply(text), provider="gemini")


def _gemini_audio_reply(session: CallSession, audio_path: str, prompt_text: str) -> AiReply:
    api_key = os.environ["GEMINI_API_KEY"]
    model = os.getenv("PI_AI_MODEL", "gemini-flash-latest")
    base_url = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
    url = f"{base_url}/models/{model}:generateContent"

    with open(audio_path, "rb") as audio_file:
        audio_data = base64.b64encode(audio_file.read()).decode("ascii")

    system_prompt = session.contact.system_prompt or session.contact.persona
    history_text = "\n".join(
        f"{item['role']}: {item['content']}"
        for item in session.history[-8:]
    )
    prompt = (
        f"{system_prompt}\n"
        "Bu bir telefon gorusmesi simulasyonu. Kullanicinin ses kaydindaki Turkce konusmayi dinle. "
        "Once ne dedigini anla, sonra telefondaki AI karakter olarak dogrudan cevap ver. "
        "Eger kullanici bir soru sorduysa selamlama yapma, soruya cevap ver. "
        f"{CHILD_SAFE_PROMPT} "
        "Transkript yazma; sadece verilecek cevabi yaz. Tek tam cumle kur. Cumle bitmeden yeni bir fikir acma.\n\n"
        f"Konusma gecmisi:\n{history_text}\n\n"
        f"Gorev: {prompt_text}\n"
        f"{session.contact.name}:"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "audio/wav",
                            "data": audio_data,
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.45,
            "maxOutputTokens": 90,
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code}: {body[:240]}") from error

    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini ses icin bos cevap dondu")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError("Gemini ses cevap metni bos")
    return AiReply(text=_clean_phone_reply(text), provider="gemini-audio")


def _clean_phone_reply(text: str) -> str:
    cleaned = " ".join(text.replace("\n", " ").split())
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.IGNORECASE | re.DOTALL).strip()
    cleaned = re.sub(r"^[A-Za-zÇĞİÖŞÜçğıöşü0-9 _-]{1,32}:\s*", "", cleaned)
    if not cleaned:
        return "Seni dinliyorum."

    sentences = re.findall(r"[^.!?…]+[.!?…]", cleaned)
    if sentences:
        cleaned = " ".join(sentence.strip() for sentence in sentences[:2])
    else:
        words = cleaned.split()
        cleaned = " ".join(words[:28]).rstrip(",;:")
        if cleaned and cleaned[-1] not in ".!?…":
            cleaned += "."

    words = cleaned.split()
    if len(words) > 34:
        cleaned = " ".join(words[:34]).rstrip(",;:") + "."
    return cleaned


def _local_reply(contact: Contact, user_text: str, prefix: str | None = None) -> str:
    text = user_text.strip()
    intro = f"{contact.name}: "
    if prefix:
        intro += prefix + " "

    if not text:
        return intro + "Buradayim, seni dinliyorum."
    if "merhaba" in text.lower() or "selam" in text.lower():
        return intro + f"Merhaba, seni dinliyorum."
    if "nasılsın" in text.lower() or "nasilsin" in text.lower():
        return intro + "Iyiyim, tesekkur ederim. Sen nasilsin?"

    return intro + "Seni anladim. Bunu sakin ve guvenli sekilde konusalim."
