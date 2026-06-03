from pydantic import BaseModel


class Contact(BaseModel):
    id: str
    name: str
    phone: str
    persona: str
    voice: str
    video_enabled: bool = True


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


class EndCallResponse(BaseModel):
    call_id: str
    status: str
