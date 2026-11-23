mod auto_tab;
mod bars;
mod macro_tab;
mod settings_tab;
pub mod theme;

use crate::config::ClickerConfig;
use crate::core::{CaptureTarget, Core, StatusKind};
use crate::hotkey;
use crate::i18n::{self, t};
use crate::tray::Tray;
use egui::{Align, Align2, Layout, RichText, ViewportBuilder, ViewportCommand, ViewportId};
use std::hash::Hash;
use std::sync::Arc;
use std::time::Duration;
use theme::{bold, Palette};

/// Everything the UI reads from the controller, taken once per frame (before locking the config,
/// see the lock rule in core.rs).
pub struct Snap {
    pub clicking: bool,
    pub macro_running: bool,
    pub count: u64,
    pub cps: f64,
    pub recording: bool,
    pub real_delay: bool,
    pub picking: bool,
    pub capture: Option<CaptureTarget>,
    pub status: Option<(String, StatusKind)>,
    pub hud_visible: bool,
}

impl Snap {
    fn take(core: &Core) -> Self {
        let (clicking, count, cps, macro_running) = (core.clicking(), core.click_count(), core.cps(), core.macro_running());
        let s = core.lock_state();
        Self {
            clicking,
            macro_running,
            count,
            cps: if clicking { cps } else { 0.0 },
            recording: s.recording,
            real_delay: s.real_delay,
            picking: s.picking,
            capture: s.capture,
            status: s.status.clone(),
            hud_visible: s.hud_visible,
        }
    }
}

/// Things the UI asks for while the config is locked; run after the lock is released.
pub enum Act {
    ToggleClick,
    ToggleMacro,
    Record(bool),
    RealDelay(bool),
    Pick,
    Capture(CaptureTarget),
    Status(String, StatusKind),
    ToggleHud,
    ToTray,
    LoadProfile(String),
    SaveProfile,
    NewProfile,
    DeleteProfile,
}

#[derive(PartialEq, Clone, Copy)]
enum Tab {
    Auto,
    Macro,
    Settings,
}

enum Dialog {
    NewProfile { name: String, error: Option<String> },
    ConfirmDelete,
    Message(String),
}

pub struct App {
    core: Arc<Core>,
    tab: Tab,
    profiles: Vec<String>,
    profile: String,
    dialog: Option<Dialog>,
    tray: Option<Tray>,
    applied: Option<(String, String, bool)>, // theme, language, always_on_top
    hidden_for_pick: bool,
}

impl App {
    pub fn new(cc: &eframe::CreationContext, core: Arc<Core>) -> Self {
        theme::install_fonts(&cc.egui_ctx);
        let hwnd = raw_hwnd(cc).unwrap_or(0);
        core.attach(cc.egui_ctx.clone(), hwnd);
        let tray = Tray::new(core.clone());
        let mut app = Self {
            core,
            tab: Tab::Auto,
            profiles: Vec::new(),
            profile: "default".into(),
            dialog: None,
            tray,
            applied: None,
            hidden_for_pick: false,
        };
        app.refresh_profiles();
        app
    }

    fn refresh_profiles(&mut self) {
        self.profiles = self.core.profiles.list();
        if self.profiles.is_empty() {
            self.profiles.push("default".into());
        }
        if !self.profiles.contains(&self.profile) {
            self.profile = self.profiles[0].clone();
        }
    }

    /// Theme, language and always-on-top follow the config; apply only when they change.
    fn sync_settings(&mut self, ctx: &egui::Context, cfg: &ClickerConfig) {
        let now = (cfg.theme.clone(), cfg.language.clone(), cfg.always_on_top);
        if self.applied.as_ref() == Some(&now) {
            return;
        }
        let old = self.applied.replace(now);
        if old.as_ref().map(|o| &o.0) != Some(&cfg.theme) {
            theme::apply(ctx, &cfg.theme);
        }
        if old.as_ref().map(|o| &o.1) != Some(&cfg.language) {
            i18n::set_language(&cfg.language);
            if let Some(tray) = &self.tray {
                tray.update_texts();
            }
        }
        if old.as_ref().map(|o| o.2) != Some(cfg.always_on_top) {
            let level = if cfg.always_on_top { egui::WindowLevel::AlwaysOnTop } else { egui::WindowLevel::Normal };
            ctx.send_viewport_cmd(ViewportCommand::WindowLevel(level));
        }
    }

    fn run(&mut self, act: Act) {
        let core = &self.core;
        match act {
            Act::ToggleClick => core.toggle_click(),
            Act::ToggleMacro => core.toggle_macro(),
            Act::Record(on) => core.set_recording(on),
            Act::RealDelay(on) => core.lock_state().real_delay = on,
            Act::Pick => core.start_pick(),
            Act::Capture(target) => core.start_capture(target),
            Act::Status(msg, kind) => core.set_status(msg, kind),
            Act::ToggleHud => core.toggle_hud(),
            Act::ToTray => core.hide_window(),
            Act::LoadProfile(name) => {
                let mut loaded = core.profiles.load(&name);
                let mut cfg = core.lock_cfg();
                // Keep the UI language and theme; the profile's always-on-top does apply
                loaded.language = cfg.language.clone();
                loaded.theme = cfg.theme.clone();
                *cfg = loaded;
                self.profile = name;
            }
            Act::SaveProfile => {
                let cfg = core.lock_cfg().clone();
                if !core.profiles.save(&self.profile, &cfg) {
                    self.dialog = Some(Dialog::Message(t("profile_save_failed").into()));
                }
                self.refresh_profiles();
            }
            Act::NewProfile => self.dialog = Some(Dialog::NewProfile { name: String::new(), error: None }),
            Act::DeleteProfile => self.dialog = Some(Dialog::ConfirmDelete),
        }
    }

    fn dialogs(&mut self, ctx: &egui::Context) {
        let Some(mut dialog) = self.dialog.take() else { return };
        let mut close = false;
        let window = |title: &str| {
            egui::Window::new(title.to_string()).collapsible(false).resizable(false).anchor(Align2::CENTER_CENTER, [0.0, 0.0])
        };
        match &mut dialog {
            Dialog::NewProfile { name, error } => {
                window(t("save_as")).show(ctx, |ui| {
                    ui.label(t("profile_name_prompt"));
                    let edit = ui.add(egui::TextEdit::singleline(name).desired_width(240.0));
                    edit.request_focus();
                    if let Some(e) = error {
                        ui.colored_label(theme::ALERT, e.as_str());
                    }
                    ui.horizontal(|ui| {
                        let enter = edit.lost_focus() && ui.input(|i| i.key_pressed(egui::Key::Enter));
                        if ui.button(theme::btn(t("ok"))).clicked() || enter {
                            let n = name.trim().to_string();
                            if !crate::config::Profiles::is_valid_name(&n) {
                                *error = Some(t("invalid_profile_name").into());
                            } else if !self.core.profiles.save(&n, &self.core.lock_cfg().clone()) {
                                *error = Some(t("profile_save_failed").into());
                            } else {
                                self.profile = n;
                                close = true;
                            }
                        }
                        if ui.button(theme::btn(t("cancel"))).clicked() {
                            close = true;
                        }
                    });
                });
                if close {
                    self.refresh_profiles();
                }
            }
            Dialog::ConfirmDelete => {
                window(t("delete")).show(ctx, |ui| {
                    ui.label(t("confirm_delete"));
                    ui.horizontal(|ui| {
                        if ui.button(theme::btn(t("yes"))).clicked() {
                            self.core.profiles.delete(&self.profile);
                            close = true;
                        }
                        if ui.button(theme::btn(t("no"))).clicked() {
                            close = true;
                        }
                    });
                });
                if close {
                    self.refresh_profiles();
                }
            }
            Dialog::Message(msg) => {
                window(t("app_title")).show(ctx, |ui| {
                    ui.label(msg.as_str());
                    if ui.button(theme::btn(t("ok"))).clicked() {
                        close = true;
                    }
                });
            }
        }
        if !close {
            self.dialog = Some(dialog);
        }
    }
}

impl eframe::App for App {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        let snap = Snap::take(&self.core);
        let mut acts = Vec::new();
        {
            let core = self.core.clone();
            let mut cfg = core.lock_cfg();
            self.sync_settings(ctx, &cfg);
            let p = theme::palette(&cfg.theme);
            egui::TopBottomPanel::top("status").frame(egui::Frame::new().fill(p.base).inner_margin(egui::Margin { left: 8, right: 8, top: 8, bottom: 2 })).show_separator_line(false).show(ctx, |ui| {
                bars::status(ui, &cfg, &snap, &p);
            });
            egui::TopBottomPanel::bottom("dock").frame(egui::Frame::new().fill(p.base).inner_margin(egui::Margin { left: 8, right: 8, top: 2, bottom: 8 })).show_separator_line(false).show(ctx, |ui| {
                bars::dock(ui, &mut cfg, &snap, &p, &self.profiles, &self.profile, &mut acts);
            });
            egui::CentralPanel::default().frame(egui::Frame::new().fill(p.base).inner_margin(egui::Margin::symmetric(8, 4))).show(ctx, |ui| {
                self.tabs(ui, &p);
                ui.add_space(4.0);
                match self.tab {
                    Tab::Auto => auto_tab::show(ui, &mut cfg, &snap, &p, &mut acts),
                    Tab::Macro => macro_tab::show(ui, &mut cfg, &snap, &p, &mut acts),
                    Tab::Settings => settings_tab::show(ui, &mut cfg, &snap, &p, &mut acts),
                }
            });
        }
        self.dialogs(ctx);
        for act in acts {
            self.run(act);
        }

        if snap.hud_visible {
            show_hud(ctx, self.core.clone());
        }
        if snap.picking {
            show_picker_banner(ctx, self.core.clone());
            if !self.hidden_for_pick {
                // Hide so the user can pick a spot behind the window
                self.hidden_for_pick = true;
                self.core.hide_window();
            }
        } else {
            self.hidden_for_pick = false;
        }

        let live = snap.clicking || snap.macro_running || snap.recording || self.tab == Tab::Auto;
        if live {
            ctx.request_repaint_after(Duration::from_millis(100));
        }
    }

    fn on_exit(&mut self, _gl: Option<&eframe::glow::Context>) {
        self.core.shutdown();
    }
}

impl App {
    fn tabs(&mut self, ui: &mut egui::Ui, p: &Palette) {
        egui::Frame::new().fill(p.panel_alt).corner_radius(theme::RADIUS_PANEL).inner_margin(3).show(ui, |ui| {
            ui.columns(3, |cols| {
                for (col, (tab, key)) in cols.iter_mut().zip([(Tab::Auto, "tab_auto"), (Tab::Macro, "tab_macro"), (Tab::Settings, "tab_settings")]) {
                    let selected = self.tab == tab;
                    let fill = if selected { p.hover } else { p.panel_alt };
                    let text = theme::btn(t(key)).color(if selected { p.text } else { p.muted });
                    let size = egui::vec2(col.available_width(), 26.0);
                    if theme::action_button(col, text, fill, p.hover, size).clicked() {
                        self.tab = tab;
                    }
                }
            });
        });
    }
}

fn raw_hwnd(cc: &eframe::CreationContext) -> Option<isize> {
    use raw_window_handle::{HasWindowHandle, RawWindowHandle};
    match cc.window_handle().ok()?.as_raw() {
        RawWindowHandle::Win32(h) => Some(h.hwnd.get()),
        _ => None,
    }
}

/// Digit-only entry bound to an integer, like the CTkEntry fields. Empty reads as `empty`.
/// Text is kept while focused so typing isn't fought by the value.
pub fn num_field(ui: &mut egui::Ui, id: impl Hash, value: &mut i64, width: f32, enabled: bool, signed: bool, empty: i64) -> bool {
    let id = ui.make_persistent_id(id);
    let mut text = ui.data_mut(|d| d.get_temp::<String>(id)).unwrap_or_else(|| value.to_string());
    // Same height as buttons/combos so a row of mixed controls lines up
    let height = ui.spacing().interact_size.y;
    let edit = egui::TextEdit::singleline(&mut text)
        .desired_width(width)
        .min_size(egui::vec2(width, height))
        .horizontal_align(Align::Center)
        .vertical_align(Align::Center)
        .font(egui::FontId::monospace(12.0));
    let resp = ui.add_enabled(enabled, edit);
    let mut changed = false;
    if resp.changed() {
        let mut filtered: String = text.chars().filter(|c| c.is_ascii_digit()).collect();
        if signed && text.trim_start().starts_with('-') {
            filtered.insert(0, '-');
        }
        filtered.truncate(9);
        text = filtered;
        let v = if text.is_empty() || text == "-" { empty } else { text.parse().unwrap_or(empty) };
        changed = v != *value;
        *value = v;
    }
    if !resp.has_focus() {
        text = value.to_string();
    }
    ui.data_mut(|d| d.insert_temp(id, text));
    changed
}

/// Right-aligned helper: lays out `add` from the right edge on the same row.
pub fn right<R>(ui: &mut egui::Ui, add: impl FnOnce(&mut egui::Ui) -> R) -> R {
    ui.with_layout(Layout::right_to_left(Align::Center), add).inner
}

fn show_hud(ctx: &egui::Context, core: Arc<Core>) {
    let builder = ViewportBuilder::default()
        .with_title("AutoClicker HUD")
        .with_inner_size([480.0, 48.0])
        .with_position([100.0, 100.0])
        .with_decorations(false)
        .with_resizable(false)
        .with_always_on_top()
        .with_taskbar(false);
    // Deferred: keeps repainting on its own while the main window is hidden in the tray
    ctx.show_viewport_deferred(ViewportId::from_hash_of("hud"), builder, move |ctx, _| {
        if !core.lock_state().hud_visible {
            ctx.send_viewport_cmd(ViewportCommand::Close);
            return;
        }
        let snap = Snap::take(&core);
        let p = theme::DARK;
        egui::CentralPanel::default()
            .frame(egui::Frame::new().fill(p.panel).stroke(egui::Stroke::new(1.0_f32, p.border)).inner_margin(egui::Margin::symmetric(12, 6)))
            .show(ctx, |ui| {
                let drag = ui.interact(ui.max_rect(), egui::Id::new("hud_drag"), egui::Sense::drag());
                if drag.drag_started() {
                    ctx.send_viewport_cmd(ViewportCommand::StartDrag);
                }
                ui.horizontal_centered(|ui| {
                    let (status, color) = if snap.clicking { (t("running"), theme::PRIMARY) } else { (t("standby"), p.muted) };
                    ui.label(bold(status, 11.0).color(color));
                    ui.add_space(8.0);
                    ui.label(theme::data(format!("CPS: {:.1}", snap.cps)).color(theme::CYAN));
                    ui.label(RichText::new("|").color(p.dim));
                    ui.label(theme::data(format!("{} {}", t("clicks").to_uppercase(), snap.count)).color(p.text));
                    right(ui, |ui| {
                        let text = theme::btn(t("stop")).color(egui::Color32::WHITE);
                        if theme::action_button(ui, text, theme::ALERT, theme::ALERT_HOVER, egui::vec2(64.0, 26.0)).clicked() {
                            core.stop_click();
                        }
                    });
                });
            });
        ctx.request_repaint_after(Duration::from_millis(200));
    });
}

fn show_picker_banner(ctx: &egui::Context, core: Arc<Core>) {
    let screen_w = ctx.input(|i| i.viewport().monitor_size).map(|s| s.x).unwrap_or(1280.0);
    let builder = ViewportBuilder::default()
        .with_title("AutoClicker Picker")
        .with_inner_size([460.0, 40.0])
        .with_position([((screen_w - 460.0) / 2.0).max(10.0), 24.0])
        .with_decorations(false)
        .with_resizable(false)
        .with_always_on_top()
        .with_taskbar(false);
    ctx.show_viewport_deferred(ViewportId::from_hash_of("picker"), builder, move |ctx, _| {
        if !core.lock_state().picking {
            ctx.send_viewport_cmd(ViewportCommand::Close);
            return;
        }
        let p = theme::DARK;
        egui::CentralPanel::default()
            .frame(egui::Frame::new().fill(p.panel).stroke(egui::Stroke::new(1.0_f32, theme::CYAN)).inner_margin(egui::Margin::symmetric(14, 6)))
            .show(ctx, |ui| {
                ui.horizontal_centered(|ui| {
                    ui.label(RichText::new(t("picker_banner")).color(p.text));
                    right(ui, |ui| {
                        if ui.add(theme::filled(bold("✕", 11.0).color(p.muted), p.panel)).clicked() {
                            core.end_pick(None);
                        }
                    });
                });
            });
        ctx.request_repaint_after(Duration::from_millis(100));
    });
}

/// "[F6]" style label for a hotkey string.
pub fn key_label(s: &str) -> String {
    hotkey::display(s)
}
