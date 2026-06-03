from uuid import uuid4

from fastapi import FastAPI, HTTPException

from .hailo_runtime import hailo_runtime
from .models import EndCallResponse, MessageRequest, MessageResponse, StartCallRequest, StartCallResponse
from .personas import CONTACTS, find_contact

app = FastAPI(title="Pi Tablet Telefon Backend", version="0.1.0")
active_calls: dict[str, str] = {}


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "hailo": hailo_runtime.status(),
    }


@app.get("/contacts")
def contacts():
    return CONTACTS


@app.post("/calls/start", response_model=StartCallResponse)
def start_call(request: StartCallRequest) -> StartCallResponse:
    contact = find_contact(request.contact_id, request.phone)
    call_id = str(uuid4())
    active_calls[call_id] = contact.id
    return StartCallResponse(call_id=call_id, status="ringing", contact=contact)


@app.post("/calls/{call_id}/message", response_model=MessageResponse)
def send_message(call_id: str, request: MessageRequest) -> MessageResponse:
    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Call not found")

    contact_id = active_calls[call_id]
    contact = find_contact(contact_id, None)
    reply = (
        f"{contact.name}: Seni duydum. Bu MVP asamasinda '{request.text}' mesajina "
        "temsili bir AI cevabi uretiyorum."
    )
    video_hint = "avatar_idle_talking" if contact.video_enabled else None
    return MessageResponse(call_id=call_id, reply=reply, voice=contact.voice, video_hint=video_hint)


@app.post("/calls/{call_id}/end", response_model=EndCallResponse)
def end_call(call_id: str) -> EndCallResponse:
    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Call not found")
    active_calls.pop(call_id)
    return EndCallResponse(call_id=call_id, status="ended")
