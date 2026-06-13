use slint::{Color, ModelRc, SharedString, VecModel};
use std::{
    process::Command,
    sync::{Arc, Mutex},
};

slint::include_modules!();

fn launch(program: &str, args: &[&str]) {
    let _ = Command::new(program).args(args).spawn();
}

fn set_system_volume(percent: i32) {
    let capped = percent.clamp(0, 150);
    let _ = Command::new("wpctl")
        .args([
            "set-volume",
            "@DEFAULT_AUDIO_SINK@",
            &format!("{:.2}", capped as f32 / 100.0),
        ])
        .status();
}

fn contact_suggestion(number: &str) -> (&'static str, &'static str) {
    let digits: String = number.chars().filter(char::is_ascii_digit).collect();
    if digits.is_empty() {
        return ("", "");
    }
    const CONTACTS: &[(&str, &str)] = &[
        ("Asya AI", "+90 532 101 10 10"),
        ("Deniz AI", "+90 533 202 20 20"),
        ("Mira AI", "+90 534 303 30 30"),
        ("Atlas AI", "+90 535 404 40 40"),
        ("Zeynep AI", "+90 536 505 50 50"),
        ("Kerem AI", "+90 537 606 60 60"),
    ];
    CONTACTS
        .iter()
        .find(|(_, phone)| {
            let contact_digits: String = phone.chars().filter(char::is_ascii_digit).collect();
            contact_digits.contains(&digits) || contact_digits.ends_with(&digits)
        })
        .copied()
        .unwrap_or(("", ""))
}

fn play_phone_sound(name: &str, looping: bool) {
    let path = format!("/opt/pi-tablet-rust/sounds/{name}.wav");
    let mut command = Command::new("ffplay");
    command.args([
        "-nodisp",
        "-autoexit",
        "-loglevel",
        "error",
        "-volume",
        "85",
    ]);
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

fn stop_dtmf() {
    let _ = Command::new("pkill")
        .args(["-f", "/opt/pi-tablet-rust/sounds/dtmf-"])
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

fn color(value: &str) -> Color {
    let value = value.trim_start_matches('#');
    if value.len() == 6 {
        if let Ok(rgb) = u32::from_str_radix(value, 16) {
            return Color::from_rgb_u8((rgb >> 16) as u8, (rgb >> 8) as u8, rgb as u8);
        }
    }
    Color::from_rgb_u8(247, 247, 250)
}

fn apply_menu_config(ui: &TabletShell) {
    let Some(config) = Command::new("curl")
        .args(["-fsS", "http://127.0.0.1:8090/api/config"])
        .output()
        .ok()
        .and_then(|output| serde_json::from_slice::<serde_json::Value>(&output.stdout).ok())
    else {
        return;
    };
    ui.set_tablet_title(config["title"].as_str().unwrap_or("Pi Tablet").into());
    ui.set_tablet_background(color(config["background"].as_str().unwrap_or("#f7f7fa")));
    let items = config["apps"]
        .as_array()
        .into_iter()
        .flatten()
        .map(|app| MenuItem {
            title: SharedString::from(app["title"].as_str().unwrap_or("Uygulama")),
            subtitle: SharedString::from(app["subtitle"].as_str().unwrap_or("")),
            tile_color: color(app["color"].as_str().unwrap_or("#dce8ef")),
            action: SharedString::from(app["action"].as_str().unwrap_or("settings")),
        })
        .collect::<Vec<_>>();
    ui.set_menu_items(ModelRc::new(VecModel::from(items)));
}

fn play_reply(reply: &serde_json::Value) {
    if let Some(audio_url) = reply["audio_url"].as_str() {
        let _ = Command::new("ffplay")
            .args([
                "-nodisp",
                "-autoexit",
                "-loglevel",
                "error",
                &format!("http://127.0.0.1:8090{audio_url}"),
            ])
            .status();
    }
}

fn main() -> Result<(), slint::PlatformError> {
    let ui = TabletShell::new()?;
    ui.window().set_fullscreen(true);
    apply_menu_config(&ui);
    let active_call = Arc::new(Mutex::new(None::<String>));

    let weak = ui.as_weak();
    ui.on_phone_tone(move |tone| {
        stop_dtmf();
        play_phone_sound(&format!("dtmf-{tone}"), false);
        if let Some(ui) = weak.upgrade() {
            let (name, phone) = contact_suggestion(ui.get_dialed().as_str());
            ui.set_suggested_name(name.into());
            ui.set_suggested_initial(name.chars().next().unwrap_or('A').to_string().into());
            ui.set_suggested_phone(phone.into());
        }
    });

    ui.on_set_volume(move |percent| {
        set_system_volume(percent);
    });

    ui.on_test_sound(move || {
        play_phone_sound("ring-on", false);
    });

    let weak = ui.as_weak();
    ui.on_open_app(move |app| {
        match app.as_str() {
            "phone" => {
                if let Some(ui) = weak.upgrade() {
                    ui.set_screen("phone".into());
                }
                return;
            }
            "settings" => {
                if let Some(ui) = weak.upgrade() {
                    ui.set_screen("settings".into());
                }
                return;
            }
            "youtube-kids" => launch("/opt/pi-tablet-rust/bin/launch-youtube-kids", &[]),
            "gcompris" => launch("gcompris-qt", &["--fullscreen"]),
            "tuxpaint" => launch("tuxpaint", &["--fullscreen", "--nosysfonts"]),
            _ => {}
        }
        if let Some(ui) = weak.upgrade() {
            ui.set_status(format!("{app} aciliyor...").into());
        }
    });

    let weak = ui.as_weak();
    std::thread::spawn(move || {
        loop {
            std::thread::sleep(std::time::Duration::from_secs(3));
            let weak = weak.clone();
            let _ = slint::invoke_from_event_loop(move || {
                if let Some(ui) = weak.upgrade() {
                    apply_menu_config(&ui);
                }
            });
        }
    });

    let weak = ui.as_weak();
    let call_slot = active_call.clone();
    ui.on_start_call(move |number| {
        if let Some(ui) = weak.upgrade() {
            let (suggested_name, suggested_phone) = contact_suggestion(number.as_str());
            ui.set_contact_name(
                if suggested_name.is_empty() {
                    if number.is_empty() {
                        "Asya AI"
                    } else {
                        "Bilinmeyen Numara"
                    }
                } else {
                    suggested_name
                }
                .into(),
            );
            ui.set_calling_phone(if suggested_phone.is_empty() {
                number.clone()
            } else {
                suggested_phone.into()
            });
            ui.set_call_state("ringing".into());
            ui.set_in_call(true);
            ui.set_listening(false);
            ui.set_status("Araniyor...".into());
        }
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
            let ringing_name = name.clone();
            let weak_ringing = weak.clone();
            let _ = slint::invoke_from_event_loop(move || {
                if let Some(ui) = weak_ringing.upgrade() {
                    ui.set_contact_name(ringing_name.clone().into());
                    ui.set_status(format!("{ringing_name} telefonu caliyor...").into());
                }
            });
            std::thread::sleep(std::time::Duration::from_millis(6500));
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
            let greeting_name = name.clone();
            let weak_greeting = weak.clone();
            let _ = slint::invoke_from_event_loop(move || {
                if let Some(ui) = weak_greeting.upgrade() {
                    ui.set_status("Seni dinliyorum...".into());
                    ui.set_contact_name(greeting_name.into());
                    ui.set_last_reply(greeting.into());
                    ui.set_call_state("connected".into());
                    ui.set_in_call(true);
                    ui.set_listening(true);
                }
            });

            std::thread::sleep(std::time::Duration::from_secs(2));
            loop {
                let is_active = call_slot
                    .lock()
                    .expect("call slot")
                    .as_ref()
                    .is_some_and(|active| active == &call_id);
                if !is_active {
                    break;
                }

                let listen_url = format!("http://127.0.0.1:8090/calls/{call_id}/listen");
                let Some(reply) = post_json(&listen_url, "{}") else {
                    std::thread::sleep(std::time::Duration::from_millis(1500));
                    continue;
                };
                let heard = reply["heard_text"]
                    .as_str()
                    .unwrap_or("Seni duyamadim")
                    .to_string();
                let answer = reply["reply"]
                    .as_str()
                    .unwrap_or("Biraz daha yakindan tekrar soyler misin?")
                    .to_string();
                if heard == "Seni duyamadim" {
                    std::thread::sleep(std::time::Duration::from_millis(1500));
                    continue;
                }
                let weak_status = weak.clone();
                let heard_status = heard.clone();
                let answer_status = answer.clone();
                let _ = slint::invoke_from_event_loop(move || {
                    if let Some(ui) = weak_status.upgrade() {
                        ui.set_listening(false);
                        ui.set_status(format!("Duydum: {heard_status}").into());
                        ui.set_last_reply(answer_status.into());
                    }
                });
                play_reply(&reply);
                let weak_listen = weak.clone();
                let name_listen = name.clone();
                let _ = slint::invoke_from_event_loop(move || {
                    if let Some(ui) = weak_listen.upgrade() {
                        ui.set_listening(true);
                        ui.set_status(format!("{name_listen} seni dinliyor...").into());
                    }
                });
            }
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
            let answer = reply["reply"]
                .as_str()
                .unwrap_or("Seni dinliyorum")
                .to_string();
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
            ui.set_call_state("idle".into());
            ui.set_listening(false);
            ui.set_contact_name("".into());
            ui.set_last_reply("".into());
            ui.set_status("Gorusme sonlandi".into());
        }
    });

    ui.run()
}
