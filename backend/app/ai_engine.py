import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from .models import Contact


@dataclass
class CallSession:
    contact: Contact
    mode: str = "voice"
    history: list[dict[str, str]] = field(default_factory=list)


@dataclass
class AiReply:
    text: str
    provider: str


def ai_status() -> dict:
    provider = os.getenv("PI_AI_PROVIDER", "local")
    return {
        "provider": provider,
        "model": os.getenv("PI_AI_MODEL", "local-persona"),
        "configured": _provider_configured(provider),
    }


def generate_reply(session: CallSession, user_text: str) -> AiReply:
    provider = os.getenv("PI_AI_PROVIDER", "local").strip().lower()
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


def _provider_configured(provider: str) -> bool:
    provider = provider.strip().lower()
    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))
    if provider == "gemini":
        return bool(os.getenv("GEMINI_API_KEY"))
    return True


def _openai_reply(session: CallSession, user_text: str) -> AiReply:
    api_key = os.environ["OPENAI_API_KEY"]
    base_url = os.getenv("PI_AI_API_BASE", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("PI_AI_MODEL", "gpt-4o-mini")
    url = f"{base_url}/chat/completions"

    system_prompt = session.contact.system_prompt or session.contact.persona
    messages = [
        {
            "role": "system",
            "content": (
                system_prompt
                + " Bu bir telefon gorusmesi simulasyonu. Gercek kisi oldugunu iddia etme; AI karakter olarak konus. "
                + "Turkce cevap ver ve 1-3 cumlede kal."
            ),
        }
    ]
    messages.extend(session.history[-8:])
    messages.append({"role": "user", "content": user_text})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 180,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code}: {body[:240]}") from error

    reply = data["choices"][0]["message"]["content"].strip()
    return AiReply(text=reply, provider="openai")


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
        "Turkce cevap ver ve 1-3 cumlede kal.\n\n"
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
    return AiReply(text=text, provider="gemini")


def _local_reply(contact: Contact, user_text: str, prefix: str | None = None) -> str:
    text = user_text.strip()
    intro = f"{contact.name}: "
    if prefix:
        intro += prefix + " "

    if not text:
        return intro + "Buradayim, seni dinliyorum."
    if "merhaba" in text.lower() or "selam" in text.lower():
        return intro + f"Merhaba. Ben {contact.name}; {contact.persona.lower()} olarak bu gorusmedeyim."
    if "nasılsın" in text.lower() or "nasilsin" in text.lower():
        return intro + "Iyiyim, tesekkur ederim. Senin icin buradayim."

    return intro + f"'{text}' mesajini aldim. Bu kisinin persona modu: {contact.persona}."
