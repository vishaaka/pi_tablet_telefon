use std::{
    process::Command,
    sync::{Arc, Mutex},
};

slint::include_modules!();

fn launch(program: &str, args: &[&str]) {
    let _ = Command::new(program).args(args).spawn();
}

fn play_phone_sound(name: &str, looping: bool) {
    let path = format!("/opt/pi-tablet-rust/sounds/{name}.wav");
    let mut command = Command::new("ffplay");
    command.args(["-nodisp", "-autoexit", "-loglevel", "error", "-volume", "100"]);
    if looping {
        command.args(["-stream_loop", "-1"]);
    }
    let _ = command.arg(path).spawn();
}

fn stop_ringback() {
    let _ = Command::new("pkill")
        .args(["-f", "/opt/pi-tablet-rust/sounds/ringback.wav"])
        .status();
}

fn post_json(url: &str, body: &str) -> Option<serde_json::Value> {
    let output = Command::new("curl")
        .args([
            "-fsS",
            "-X",
            "POST",
            "-H",
            "Content-Type: application/json",
            "-d",
            body,
            url,
        ])
        .output()
        .ok()?;
    serde_json::from_slice(&output.stdout).ok()
}

fn play_reply(reply: &serde_json::Value) {
    if let Some(audio_url) = reply["audio_url"].as_str() {
        launch(
            "ffplay",
            &[
                "-nodisp",
                "-autoexit",
                "-loglevel",
                "error",
                &format!("http://127.0.0.1:8090{audio_url}"),
            ],
        );
    }
}

fn main() -> Result<(), slint::PlatformError> {
    let ui = TabletShell::new()?;
    ui.window().set_fullscreen(true);
    let active_call = Arc::new(Mutex::new(None::<String>));

    ui.on_phone_tone(move |tone| {
        play_phone_sound(&format!("dtmf-{tone}"), false);
    });

    let weak = ui.as_weak();
    ui.on_open_app(move |app| {
        match app.as_str() {
            "youtube-kids" => launch(
                "/opt/pi-tablet-rust/bin/launch-youtube-kids",
                &[],
            ),
            "gcompris" => launch("gcompris-qt", &["--fullscreen"]),
            "tuxpaint" => launch("tuxpaint", &["--fullscreen", "--nosysfonts"]),
            _ => {}
        }
        if let Some(ui) = weak.upgrade() {
            ui.set_status(format!("{app} aciliyor...").into());
        }
    });

    let weak = ui.as_weak();
    let call_slot = active_call.clone();
    ui.on_start_call(move |number| {
        let weak = weak.clone();
        let call_slot = call_slot.clone();
        std::thread::spawn(move || {
            stop_ringback();
            play_phone_sound("ringback", true);
            let phone = number.as_str();
            let body = if phone.is_empty() {
                r#"{"contact_id":"asya"}"#.to_string()
            } else {
                format!(r#"{{"phone":"{phone}"}}"#)
            };
            let Some(start) = post_json("http://127.0.0.1:8090/calls/start", &body) else {
                stop_ringback();
                let _ = slint::invoke_from_event_loop(move || {
                    if let Some(ui) = weak.upgrade() {
                        ui.set_status("Rust backend bulunamadi".into());
                    }
                });
                return;
            };
            let Some(call_id) = start["call_id"].as_str().map(ToOwned::to_owned) else {
                stop_ringback();
                return;
            };
            *call_slot.lock().expect("call slot") = Some(call_id.clone());
            let name = start["contact"]["name"]
                .as_str()
                .unwrap_or("AI kisi")
                .to_string();
            std::thread::sleep(std::time::Duration::from_millis(2200));
            stop_ringback();
            play_phone_sound("connect", false);
            std::thread::sleep(std::time::Duration::from_millis(250));
            let message_url = format!("http://127.0.0.1:8090/calls/{call_id}/message");
            let reply = post_json(&message_url, r#"{"text":"Merhaba"}"#);
            if let Some(reply) = reply.as_ref() {
                play_reply(reply);
            }
            let greeting = reply
                .and_then(|value| value["reply"].as_str().map(ToOwned::to_owned))
                .unwrap_or_else(|| "Merhaba".into());
            let _ = slint::invoke_from_event_loop(move || {
                if let Some(ui) = weak.upgrade() {
                    ui.set_status(format!("{name} ile gorusuluyor").into());
                    ui.set_contact_name(name.into());
                    ui.set_last_reply(greeting.into());
                    ui.set_in_call(true);
                }
            });
        });
    });

    let weak = ui.as_weak();
    let call_slot = active_call.clone();
    ui.on_send_message(move |text| {
        let weak = weak.clone();
        let call_slot = call_slot.clone();
        let text = text.to_string();
        std::thread::spawn(move || {
            let Some(call_id) = call_slot.lock().expect("call slot").clone() else {
                return;
            };
            let url = format!("http://127.0.0.1:8090/calls/{call_id}/message");
            let body = serde_json::json!({ "text": text }).to_string();
            let Some(reply) = post_json(&url, &body) else {
                return;
            };
            play_reply(&reply);
            let answer = reply["reply"].as_str().unwrap_or("Seni dinliyorum").to_string();
            let _ = slint::invoke_from_event_loop(move || {
                if let Some(ui) = weak.upgrade() {
                    ui.set_last_reply(answer.into());
                }
            });
        });
    });

    let weak = ui.as_weak();
    let call_slot = active_call.clone();
    ui.on_listen(move || {
        let weak = weak.clone();
        let call_slot = call_slot.clone();
        std::thread::spawn(move || {
            let Some(call_id) = call_slot.lock().expect("call slot").clone() else {
                return;
            };
            let url = format!("http://127.0.0.1:8090/calls/{call_id}/listen");
            let reply = post_json(&url, "{}");
            if let Some(reply) = reply.as_ref() {
                play_reply(reply);
            }
            let heard = reply
                .as_ref()
                .and_then(|value| value["heard_text"].as_str())
                .unwrap_or("Seni duyamadim")
                .to_string();
            let answer = reply
                .as_ref()
                .and_then(|value| value["reply"].as_str())
                .unwrap_or("Biraz daha yakindan tekrar soyler misin?")
                .to_string();
            let _ = slint::invoke_from_event_loop(move || {
                if let Some(ui) = weak.upgrade() {
                    ui.set_listening(false);
                    ui.set_status(format!("Duydum: {heard}").into());
                    ui.set_last_reply(answer.into());
                }
            });
        });
    });

    let weak = ui.as_weak();
    ui.on_end_call(move || {
        stop_ringback();
        if let Some(call_id) = active_call.lock().expect("call slot").take() {
            let url = format!("http://127.0.0.1:8090/calls/{call_id}/end");
            std::thread::spawn(move || {
                let _ = post_json(&url, "{}");
            });
        }
        let _ = Command::new("pkill")
            .args(["-f", "ffplay.*127.0.0.1:8090"])
            .status();
        play_phone_sound("end", false);
        if let Some(ui) = weak.upgrade() {
            ui.set_in_call(false);
            ui.set_listening(false);
            ui.set_contact_name("".into());
            ui.set_last_reply("".into());
            ui.set_status("Gorusme sonlandi".into());
        }
    });

    ui.run()
}
