use std::{
    collections::HashMap,
    path::{Path, PathBuf},
    sync::Arc,
};

use axum::{
    Json, Router,
    extract::{Path as AxumPath, State},
    http::StatusCode,
    routing::{get, post},
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use tokio::{process::Command, sync::RwLock};
use tower_http::services::ServeDir;
use uuid::Uuid;

#[derive(Clone, Serialize)]
struct Contact {
    id: &'static str,
    name: &'static str,
    phone: &'static str,
    persona: &'static str,
    voice: &'static str,
    video_enabled: bool,
}

const CONTACTS: &[Contact] = &[
    Contact {
        id: "asya",
        name: "Asya AI",
        phone: "+90 532 101 10 10",
        persona: "Sakin ve yardimci",
        voice: "soft_female",
        video_enabled: true,
    },
    Contact {
        id: "deniz",
        name: "Deniz AI",
        phone: "+90 533 202 20 20",
        persona: "Enerjik teknik destek",
        voice: "warm_male",
        video_enabled: true,
    },
    Contact {
        id: "mira",
        name: "Mira AI",
        phone: "+90 534 303 30 30",
        persona: "Canli sohbet karakteri",
        voice: "bright_female",
        video_enabled: true,
    },
    Contact {
        id: "atlas",
        name: "Atlas AI",
        phone: "+90 535 404 40 40",
        persona: "Planli ve ciddi",
        voice: "deep_male",
        video_enabled: true,
    },
    Contact {
        id: "zeynep",
        name: "Zeynep AI",
        phone: "+90 536 505 50 50",
        persona: "Gunluk sohbet",
        voice: "calm_female",
        video_enabled: true,
    },
    Contact {
        id: "kerem",
        name: "Kerem AI",
        phone: "+90 537 606 60 60",
        persona: "Dil pratik arkadasi",
        voice: "clear_male",
        video_enabled: true,
    },
];

#[derive(Default)]
struct Call {
    contact_id: String,
    turn: usize,
    last_topic: String,
}

#[derive(Clone)]
struct AppState {
    calls: Arc<RwLock<HashMap<Uuid, Call>>>,
    audio_dir: PathBuf,
}

#[derive(Deserialize)]
struct StartCall {
    contact_id: Option<String>,
    phone: Option<String>,
}

#[derive(Deserialize)]
struct Message {
    text: String,
}

#[derive(Serialize)]
struct CallResponse {
    call_id: Uuid,
    status: &'static str,
    contact: Contact,
}

#[derive(Serialize)]
struct MessageResponse {
    call_id: Uuid,
    reply: String,
    voice: String,
    provider: &'static str,
    audio_url: Option<String>,
    audio_provider: Option<&'static str>,
    video_hint: &'static str,
}

#[tokio::main]
async fn main() {
    let audio_dir = std::env::var("PI_TABLET_AUDIO_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("/var/lib/pi-tablet-rust/audio"));
    tokio::fs::create_dir_all(&audio_dir)
        .await
        .expect("audio directory");
    let state = AppState {
        calls: Arc::new(RwLock::new(HashMap::new())),
        audio_dir: audio_dir.clone(),
    };

    let app = Router::new()
        .route("/health", get(health))
        .route("/contacts", get(contacts))
        .route("/calls/start", post(start_call))
        .route("/calls/{call_id}/message", post(message))
        .route("/calls/{call_id}/listen", post(listen))
        .route("/calls/{call_id}/end", post(end_call))
        .nest_service("/audio", ServeDir::new(audio_dir))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:8090")
        .await
        .expect("listen");
    axum::serve(listener, app).await.expect("server");
}

async fn health() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "status": "ok",
        "runtime": "rust",
        "port": 8090,
        "waydroid_required": false
    }))
}

async fn contacts() -> Json<Vec<Contact>> {
    Json(CONTACTS.to_vec())
}

async fn start_call(
    State(state): State<AppState>,
    Json(request): Json<StartCall>,
) -> Json<CallResponse> {
    let contact = find_contact(request.contact_id.as_deref(), request.phone.as_deref());
    let call_id = Uuid::new_v4();
    state.calls.write().await.insert(
        call_id,
        Call {
            contact_id: contact.id.to_string(),
            ..Call::default()
        },
    );
    Json(CallResponse {
        call_id,
        status: "ringing",
        contact,
    })
}

async fn message(
    State(state): State<AppState>,
    AxumPath(call_id): AxumPath<Uuid>,
    Json(request): Json<Message>,
) -> Result<Json<MessageResponse>, StatusCode> {
    let mut calls = state.calls.write().await;
    let call = calls.get_mut(&call_id).ok_or(StatusCode::NOT_FOUND)?;
    let contact = find_contact(Some(&call.contact_id), None);
    let reply = quick_reply(&contact, &request.text, call);
    let (audio_url, audio_provider) = synthesize(&state.audio_dir, &contact, &reply).await;
    Ok(Json(MessageResponse {
        call_id,
        reply,
        voice: contact.voice.to_string(),
        provider: "rust-scripted",
        audio_url,
        audio_provider,
        video_hint: "avatar_idle_talking",
    }))
}

async fn listen(
    State(state): State<AppState>,
    AxumPath(call_id): AxumPath<Uuid>,
) -> Result<Json<MessageResponse>, StatusCode> {
    message(
        State(state),
        AxumPath(call_id),
        Json(Message {
            text: "Seni dinliyorum".into(),
        }),
    )
    .await
}

async fn end_call(State(state): State<AppState>, AxumPath(call_id): AxumPath<Uuid>) -> StatusCode {
    state.calls.write().await.remove(&call_id);
    StatusCode::NO_CONTENT
}

fn find_contact(id: Option<&str>, phone: Option<&str>) -> Contact {
    CONTACTS
        .iter()
        .find(|contact| {
            id == Some(contact.id)
                || phone.is_some_and(|value| digits(contact.phone).ends_with(&digits(value)))
        })
        .cloned()
        .unwrap_or(Contact {
            id: "unknown",
            name: "Bilinmeyen Numara",
            phone: "000",
            persona: "Gecici arama",
            voice: "soft_female",
            video_enabled: false,
        })
}

fn digits(value: &str) -> String {
    value.chars().filter(char::is_ascii_digit).collect()
}

fn quick_reply(contact: &Contact, text: &str, call: &mut Call) -> String {
    let normalized = text.to_lowercase();
    call.turn += 1;
    if normalized.contains("merhaba") || normalized.contains("selam") {
        return format!(
            "Merhaba, ben {}. Bugun ne konusmak istersin?",
            contact.name.trim_end_matches(" AI")
        );
    }
    if normalized.contains("nasilsin") || normalized.contains("nasılsın") {
        return "Iyiyim, tesekkur ederim. Senin gunun nasil gidiyor?".into();
    }
    if normalized.contains("sikildim") || normalized.contains("sıkıldım") {
        call.last_topic = "oyun".into();
        return "Bir bilmece ya da kisa hikaye secmek ister misin?".into();
    }
    if normalized.trim() == "evet" && call.last_topic == "oyun" {
        return "Harika. Agzi var konusmaz, yatagi var uyumaz. Nedir?".into();
    }
    call.last_topic = text
        .split_whitespace()
        .take(7)
        .collect::<Vec<_>>()
        .join(" ");
    format!(
        "{} demen ilgimi cekti. Biraz daha anlatir misin?",
        call.last_topic
    )
}

async fn synthesize(
    audio_dir: &Path,
    contact: &Contact,
    text: &str,
) -> (Option<String>, Option<&'static str>) {
    let voice = if contact.voice.contains("male") {
        "tr-TR-AhmetNeural"
    } else {
        "tr-TR-EmelNeural"
    };
    let key = format!("{voice}|{text}");
    let name = format!("{:x}.mp3", Sha256::digest(key.as_bytes()));
    let target = audio_dir.join(&name);
    if target.is_file() {
        return (Some(format!("/audio/{name}")), Some("edge-tts-cache"));
    }
    let edge_tts = std::env::var("PI_EDGE_TTS_COMMAND").unwrap_or_else(|_| "edge-tts".into());
    let status = Command::new(edge_tts)
        .args(["--voice", voice, "--text", text, "--write-media"])
        .arg(&target)
        .status()
        .await;
    if status.is_ok_and(|value| value.success()) {
        (Some(format!("/audio/{name}")), Some("edge-tts"))
    } else {
        (None, None)
    }
}
