from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from .ai_engine import CallSession, ai_status, generate_reply, generate_reply_from_audio
from .hailo_runtime import hailo_runtime
from .mic_capture import capture_call_audio
from .models import EndCallResponse, MessageRequest, MessageResponse, StartCallRequest, StartCallResponse
from .personas import CONTACTS, find_contact
from .tts_engine import AUDIO_DIR, synthesize_for_contact, tts_status

app = FastAPI(title="Pi Tablet Telefon Backend", version="0.1.0")
active_calls: dict[str, CallSession] = {}
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "hailo": hailo_runtime.status(),
        "ai": ai_status(),
        "tts": tts_status(),
    }


@app.get("/contacts")
def contacts():
    return CONTACTS


@app.post("/calls/start", response_model=StartCallResponse)
def start_call(request: StartCallRequest) -> StartCallResponse:
    contact = find_contact(request.contact_id, request.phone)
    call_id = str(uuid4())
    active_calls[call_id] = CallSession(contact=contact, mode=request.mode)
    return StartCallResponse(call_id=call_id, status="ringing", contact=contact)


@app.post("/calls/{call_id}/message", response_model=MessageResponse)
def send_message(call_id: str, request: MessageRequest) -> MessageResponse:
    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Call not found")

    session = active_calls[call_id]
    session.history.append({"role": "user", "content": request.text})
    ai_reply = generate_reply(session, request.text)
    session.history.append({"role": "assistant", "content": ai_reply.text})
    tts = synthesize_for_contact(call_id, session.contact, ai_reply.text)
    video_hint = "avatar_idle_talking" if session.contact.video_enabled else None
    return MessageResponse(
        call_id=call_id,
        reply=ai_reply.text,
        voice=session.contact.voice,
        video_hint=video_hint,
        provider=ai_reply.provider,
        audio_url=tts.audio_url,
        audio_provider=tts.provider,
    )


@app.post("/calls/{call_id}/listen", response_model=MessageResponse)
def listen_and_reply(call_id: str) -> MessageResponse:
    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Call not found")

    session = active_calls[call_id]
    try:
        audio_path = capture_call_audio(call_id, seconds=5)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Microphone capture failed: {error}") from error

    prompt = "Kullanicinin az once soyledigine cevap ver."
    session.history.append({"role": "user", "content": "[voice message]"})
    ai_reply = generate_reply_from_audio(session, str(audio_path), prompt)
    session.history.append({"role": "assistant", "content": ai_reply.text})
    tts = synthesize_for_contact(call_id, session.contact, ai_reply.text)
    video_hint = "avatar_idle_talking" if session.contact.video_enabled else None
    return MessageResponse(
        call_id=call_id,
        reply=ai_reply.text,
        voice=session.contact.voice,
        video_hint=video_hint,
        provider=ai_reply.provider,
        audio_url=tts.audio_url,
        audio_provider=tts.provider,
    )


@app.post("/calls/{call_id}/end", response_model=EndCallResponse)
def end_call(call_id: str) -> EndCallResponse:
    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Call not found")
    active_calls.pop(call_id)
    return EndCallResponse(call_id=call_id, status="ended")
