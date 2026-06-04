from pydantic import BaseModel


class Contact(BaseModel):
    id: str
    name: str
    phone: str
    persona: str
    voice: str
    video_enabled: bool = True
    system_prompt: str | None = None
    tts_voice: str | None = None
    tts_rate: int = 0
    tts_pitch: int = 0


class StartCallRequest(BaseModel):
    contact_id: str | None = None
    phone: str | None = None
    mode: str = "voice"


class StartCallResponse(BaseModel):
    call_id: str
    status: str
    contact: Contact


class MessageRequest(BaseModel):
    text: str


class MessageResponse(BaseModel):
    call_id: str
    reply: str
    voice: str
    video_hint: str | None = None
    provider: str = "local"
    audio_url: str | None = None
    audio_provider: str | None = None


class EndCallResponse(BaseModel):
    call_id: str
    status: str
