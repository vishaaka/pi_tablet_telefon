use std::process::Command;

slint::include_modules!();

fn launch(program: &str, args: &[&str]) {
    let _ = Command::new(program).args(args).spawn();
}

fn main() -> Result<(), slint::PlatformError> {
    let ui = TabletShell::new()?;
    ui.window().set_fullscreen(true);

    let weak = ui.as_weak();
    ui.on_open_app(move |app| {
        match app.as_str() {
            "youtube-kids" => launch(
                "chromium",
                &[
                    "--kiosk",
                    "--noerrdialogs",
                    "--disable-infobars",
                    "--no-first-run",
                    "https://www.youtubekids.com",
                ],
            ),
            "gcompris" => launch("gcompris-qt", &["--fullscreen"]),
            "tuxpaint" => launch("tuxpaint", &["--fullscreen", "--nosysfonts"]),
            _ => {}
        }
        if let Some(ui) = weak.upgrade() {
            ui.set_status(format!("{app} aciliyor...").into());
        }
    });

    ui.run()
}
