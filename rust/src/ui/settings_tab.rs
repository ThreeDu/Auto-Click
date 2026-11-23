//! SETTINGS tab: language, theme, hotkey binding.
use super::theme::{self, btn, data, Palette};
use super::{key_label, right, Act, Snap};
use crate::config::ClickerConfig;
use crate::core::{CaptureTarget, StatusKind};
use crate::i18n::{t, LANGUAGES};

pub fn show(ui: &mut egui::Ui, cfg: &mut ClickerConfig, snap: &Snap, p: &Palette, acts: &mut Vec<Act>) {
    let w = ui.available_width();

    theme::card(p).show(ui, |ui| {
        ui.set_width(w - 22.0);
        ui.label(theme::title(p, t("preferences")));
        ui.horizontal(|ui| {
            theme::cell(ui, 120.0, egui::Align::Min, |ui| ui.label(t("language")));
            let current = LANGUAGES.iter().find(|(c, _)| *c == cfg.language).map(|l| l.1).unwrap_or("English");
            egui::ComboBox::from_id_salt("language").width(140.0).selected_text(current).show_ui(ui, |ui| {
                for (code, name) in LANGUAGES {
                    ui.selectable_value(&mut cfg.language, code.to_string(), name);
                }
            });
        });
        ui.horizontal(|ui| {
            theme::cell(ui, 120.0, egui::Align::Min, |ui| ui.label(t("theme")));
            super::auto_tab::combo(ui, "theme", &mut cfg.theme, &["dark", "light"], 140.0);
        });
    });

    theme::card(p).show(ui, |ui| {
        ui.set_width(w - 22.0);
        ui.label(theme::title(p, t("hotkeys")));
        for (label, value, target) in [
            (t("click_key"), cfg.hotkey.clone(), CaptureTarget::Click),
            (t("macro_key"), cfg.macro_hotkey.clone(), CaptureTarget::Macro),
        ] {
            ui.horizontal(|ui| {
                theme::cell(ui, 120.0, egui::Align::Min, |ui| ui.label(label));
                egui::Frame::new().fill(p.panel_alt).stroke(egui::Stroke::new(1.0_f32, p.border)).corner_radius(theme::RADIUS_CONTROL).inner_margin(egui::Margin::symmetric(8, 3)).show(ui, |ui| {
                    ui.set_min_width(120.0);
                    ui.label(data(key_label(&value)).color(theme::AMBER));
                });
                let capturing = snap.capture == Some(target);
                let button = if capturing {
                    theme::filled(btn(t("press_key")).color(p.base), theme::AMBER)
                } else {
                    egui::Button::new(btn(t("record_key")))
                };
                if ui.add_enabled(snap.capture.is_none() || capturing, button).clicked() && !capturing {
                    acts.push(Act::Capture(target));
                }
            });
        }
        if let Some((msg, kind)) = &snap.status {
            let color = match kind {
                StatusKind::Ok => theme::PRIMARY,
                StatusKind::Error => theme::ALERT,
                StatusKind::Info => theme::AMBER,
            };
            ui.label(egui::RichText::new(msg).color(color));
        }
        ui.horizontal(|ui| {
            right(ui, |ui| {
                if ui.button(btn(t("reset_hotkeys"))).clicked() {
                    cfg.hotkey = "f6".into();
                    cfg.macro_hotkey = "f7".into();
                    acts.push(Act::Status(t("hotkeys_reset_success").into(), StatusKind::Ok));
                }
            });
        });
    });
}
