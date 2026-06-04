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
        "configured": bool(os.getenv("OPENAI_API_KEY")) if provider == "openai" else True,
    }


def generate_reply(session: CallSession, user_text: str) -> AiReply:
    provider = os.getenv("PI_AI_PROVIDER", "local").strip().lower()
    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        try:
            return _openai_reply(session, user_text)
        except Exception as error:
            return AiReply(text=_local_reply(session.contact, user_text, f"AI servis hatasi: {error}"), provider="local-fallback")

    return AiReply(text=_local_reply(session.contact, user_text), provider="local")


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
