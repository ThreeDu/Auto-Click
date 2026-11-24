//! AutoClicker, Rust/egui rewrite of the Python app in the repo root.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

#[macro_use]
mod logfile;
mod config;
mod core;
mod engine;
mod hotkey;
mod i18n;
mod single_instance;
mod tray;
mod ui;
mod win;

use std::sync::Arc;

fn main() {
    if !single_instance::acquire() {
        single_instance::signal_existing();
        return;
    }
    // Profiles live next to the exe, same as the Python build
    let exe_dir = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.to_path_buf())).unwrap_or_else(|| ".".into());
    let profiles = config::Profiles::new(exe_dir.join("profiles"));
    logfile::init(&profiles.dir);
    let cfg = profiles.load_session().unwrap_or_default();
    i18n::set_language(&cfg.language);
    let core = core::Core::new(cfg, profiles);
    single_instance::serve(core.clone());

    let mut viewport = egui::ViewportBuilder::default()
        .with_title("AutoClicker")
        .with_inner_size([500.0, 620.0])
        .with_resizable(false)
        .with_maximize_button(false);
    if let Some((rgba, width, height)) = tray::icon_rgba(256) {
        viewport = viewport.with_icon(Arc::new(egui::IconData { rgba, width, height }));
    }
    let options = eframe::NativeOptions { viewport, renderer: eframe::Renderer::Glow, ..Default::default() };
    let shutdown = core.clone();
    if let Err(e) = eframe::run_native("AutoClicker", options, Box::new(move |cc| Ok(Box::new(ui::App::new(cc, core))))) {
        log!("Startup error: {e}");
        shutdown.shutdown();
        let msg: Vec<u16> = format!("Startup Error:\n\n{e}\0").encode_utf16().collect();
        unsafe {
            windows::Win32::UI::WindowsAndMessaging::MessageBoxW(
                None,
                windows::core::PCWSTR(msg.as_ptr()),
                windows::core::w!("AutoClicker Error"),
                windows::Win32::UI::WindowsAndMessaging::MB_ICONERROR,
            );
        }
    }
}
