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

#[derive(Default, Deserialize)]
struct ListenRequest {
    audio_path: Option<String>,
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
    heard_text: Option<String>,
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
    reply_to_text(&state, call_id, request.text, None).await
}

async fn reply_to_text(
    state: &AppState,
    call_id: Uuid,
    text: String,
    heard_text: Option<String>,
) -> Result<Json<MessageResponse>, StatusCode> {
    let mut calls = state.calls.write().await;
    let call = calls.get_mut(&call_id).ok_or(StatusCode::NOT_FOUND)?;
    let contact = find_contact(Some(&call.contact_id), None);
    let reply = quick_reply(&contact, &text, call);
    let (audio_url, audio_provider) = synthesize(&state.audio_dir, &contact, &reply).await;
    Ok(Json(MessageResponse {
        call_id,
        heard_text,
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
    Json(request): Json<ListenRequest>,
) -> Result<Json<MessageResponse>, StatusCode> {
    if !state.calls.read().await.contains_key(&call_id) {
        return Err(StatusCode::NOT_FOUND);
    }
    let heard = transcribe(request.audio_path.as_deref())
        .await
        .unwrap_or_else(|| "Seni duyamadim".into());
    let intent = voice_intent(&heard);
    reply_to_text(&state, call_id, intent, Some(heard)).await
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
        return greeting(contact);
    }
    if normalized.contains("nasilsin") || normalized.contains("nasılsın") {
        return match contact.id {
            "asya" => "Iyiyim, tesekkur ederim. Bugun seni mutlu eden ne oldu?".into(),
            "deniz" => "Enerjim yerinde. Bugun birlikte ilginc bir sey kesfedelim mi?".into(),
            "mira" => "Cok iyiyim. Seninle konusmak gunumu guzellestirdi.".into(),
            "atlas" => "Iyiyim. Bugun icin guzel bir plan yapmaya hazirim.".into(),
            "zeynep" => "Iyiyim canim. Senin gunun nasil geciyor?".into(),
            "kerem" => "Gayet iyiyim. Bugun yeni bir kelime ogrenmeye ne dersin?".into(),
            _ => "Iyiyim, tesekkur ederim. Sen nasilsin?".into(),
        };
    }
    if normalized.contains("sikildim")
        || normalized.contains("sıkıldım")
        || normalized.contains("oyun")
    {
        call.last_topic = "oyun".into();
        return match contact.id {
            "deniz" => "Hizli oyun: Etrafinda mavi renkli bir sey bulabilir misin?".into(),
            "kerem" => "Kelime oyunu oynayalim. Ben elma diyorum, sen a harfiyle bir kelime soyle."
                .into(),
            _ => "Bir bilmece ya da kisa hikaye secmek ister misin?".into(),
        };
    }
    if normalized.contains("bilmece")
        || (normalized.trim() == "evet" && call.last_topic == "oyun")
    {
        call.last_topic = "bilmece".into();
        return "Harika. Agzi var konusmaz, yatagi var uyumaz. Nedir?".into();
    }
    if normalized.contains("hikaye") {
        call.last_topic = "hikaye".into();
        return match contact.id {
            "mira" => "Minik bir yildiz, karanlikta yolunu arayan kuslara isik olmus. Kuslar da ona en guzel sarkilarini soylemis.".into(),
            "atlas" => "Kucuk bir gezgin her gun bir adim atmis. Sabirla yuruyunce sonunda hayalindeki tepeye ulasmis.".into(),
            _ => "Minik bir bulut, susayan ciceklere yagmur tasimis. Cicekler acinca gokyuzu rengarenk olmus.".into(),
        };
    }
    if normalized.contains("bugun") || normalized.contains("ne yapalim") {
        return match contact.id {
            "asya" => "Bugun once sevdigin bir oyunu oynayip sonra kisa bir hikaye okuyabiliriz.".into(),
            "deniz" => "Bugun basit bir deney yapalim: Hangi esyalar suyun ustunde kaliyor, tahmin edelim.".into(),
            "mira" => "Bugun bir resim cizip ona komik bir isim verebiliriz.".into(),
            "atlas" => "Uc adimli plan: oyun, dinlenme ve yeni bir sey ogrenme.".into(),
            "zeynep" => "Bugun sevdigin birine guzel bir soz soylemekle baslayabiliriz.".into(),
            "kerem" => "Bugun uc yeni kelime ogrenelim: hello merhaba, sun gunes, friend arkadas.".into(),
            _ => "Bugun guzel bir oyun secerek baslayabiliriz.".into(),
        };
    }
    if normalized.contains("tesekkur") || normalized.contains("teşekkür") {
        return "Rica ederim. Seninle konusmak cok guzel.".into();
    }
    if normalized.contains("duyamadim") {
        return "Seni tam duyamadim. Biraz daha yakindan tekrar soyler misin?".into();
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

async fn transcribe(audio_path: Option<&str>) -> Option<String> {
    let listener = std::env::var("PI_STT_LISTEN_COMMAND")
        .unwrap_or_else(|_| "/opt/pi-tablet-rust/bin/listen-turkish".into());
    let mut command = Command::new(listener);
    if let Some(path) = audio_path {
        command.arg(path);
    }
    let output = command.output().await.ok()?;
    if !output.status.success() {
        return None;
    }
    let text = String::from_utf8_lossy(&output.stdout).trim().to_string();
    (!text.is_empty()).then_some(text)
}

fn voice_intent(heard: &str) -> String {
    let normalized = heard.to_lowercase();
    if normalized.contains("nasıl") || normalized.contains("nasil") {
        "Nasilsin?".into()
    } else if normalized.contains("yapalım")
        || normalized.contains("yapalim")
        || normalized.contains("bugün")
        || normalized.contains("bugun")
    {
        "Bugun ne yapalim?".into()
    } else if normalized.contains("oyun") || normalized.contains("oyna") {
        "Oyun oynayalim".into()
    } else if normalized.contains("bilmece") {
        "Bilmece sor".into()
    } else if normalized.contains("hikaye") || normalized.contains("hikâye") {
        "Kisa hikaye anlat".into()
    } else if normalized.contains("teşekkür")
        || normalized.contains("tesekkur")
        || normalized.contains("sağ ol")
        || normalized.contains("sag ol")
    {
        "Tesekkur ederim".into()
    } else {
        heard.into()
    }
}

fn greeting(contact: &Contact) -> String {
    match contact.id {
        "asya" => "Merhaba, ben Asya. Seni dinliyorum, bugun ne konusmak istersin?".into(),
        "deniz" => "Selam, Deniz burada. Hazirsan birlikte yeni bir sey kesfedelim.".into(),
        "mira" => "Merhaba, ben Mira. Seninle sohbet etmeye cok sevindim.".into(),
        "atlas" => "Merhaba, ben Atlas. Bugun icin birlikte guzel bir plan yapabiliriz.".into(),
        "zeynep" => "Merhaba canim, ben Zeynep. Gununu bana anlatmak ister misin?".into(),
        "kerem" => "Hello, merhaba. Ben Kerem. Birlikte kelime oyunu oynayabiliriz.".into(),
        _ => format!(
            "Merhaba, ben {}. Bugun ne konusmak istersin?",
            contact.name.trim_end_matches(" AI")
        ),
    }
}

async fn synthesize(
    audio_dir: &Path,
    contact: &Contact,
    text: &str,
) -> (Option<String>, Option<&'static str>) {
    let (pitch, speed) = match contact.voice {
        "soft_female" => ("62", "155"),
        "bright_female" => ("72", "170"),
        "calm_female" => ("55", "145"),
        "warm_male" => ("42", "165"),
        "deep_male" => ("28", "140"),
        "clear_male" => ("48", "175"),
        _ => ("55", "155"),
    };
    let key = format!("espeak-ng|{pitch}|{speed}|{text}");
    let name = format!("{:x}.wav", Sha256::digest(key.as_bytes()));
    let target = audio_dir.join(&name);
    if target.is_file() {
        return (Some(format!("/audio/{name}")), Some("espeak-ng-cache"));
    }
    let status = Command::new("espeak-ng")
        .args(["-v", "tr", "-p", pitch, "-s", speed, "-w"])
        .arg(&target)
        .arg(text)
        .status()
        .await;
    if status.is_ok_and(|value| value.success()) {
        (Some(format!("/audio/{name}")), Some("espeak-ng"))
    } else {
        (None, None)
    }
}
