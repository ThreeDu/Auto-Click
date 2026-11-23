//! AUTO CLICK tab: interval, click options, location, repeat & jitter, start button.
use super::theme::{self, bold, btn, caption, mono, readout, Palette};
use super::{key_label, num_field, right, Act, Snap};
use crate::config::ClickerConfig;
use crate::i18n::t;
use crate::win::input::cursor_pos;

/// Readout next to the interval title (interval_card.py `_update_readout`).
fn interval_readout(total_ms: i64) -> String {
    if total_ms <= 0 {
        t("max_speed").into()
    } else if total_ms < 1000 {
        format!("{:.1} CPS ({total_ms}ms)", 1000.0 / total_ms as f64)
    } else {
        format!("1 click / {:.1}s", total_ms as f64 / 1000.0)
    }
}

pub fn show(ui: &mut egui::Ui, cfg: &mut ClickerConfig, snap: &Snap, p: &Palette, acts: &mut Vec<Act>) {
    let w = ui.available_width();

    theme::card(p).show(ui, |ui| {
        ui.set_width(w - 22.0);
        ui.horizontal(|ui| {
            ui.label(theme::title(p, t("interval_title")));
            right(ui, |ui| ui.label(readout(interval_readout(cfg.total_interval_ms()))));
        });
        // Each column: small label centered over its control, all controls on one baseline
        let column = |ui: &mut egui::Ui, width: f32, align: egui::Align, add: &mut dyn FnMut(&mut egui::Ui)| {
            ui.allocate_ui_with_layout(egui::vec2(width, 48.0), egui::Layout::top_down(align), |ui| {
                ui.spacing_mut().item_spacing.y = 4.0;
                add(ui);
            });
        };
        ui.horizontal(|ui| {
            for (label, value, width, id) in [
                ("H", &mut cfg.interval_hours, 40.0, "h"),
                ("M", &mut cfg.interval_minutes, 40.0, "m"),
                ("S", &mut cfg.interval_seconds, 40.0, "s"),
                ("MS", &mut cfg.interval_ms, 60.0, "ms"),
            ] {
                column(ui, width, egui::Align::Center, &mut |ui| {
                    ui.label(caption(p, label));
                    num_field(ui, ("interval", id), value, width, true, false, 0);
                });
            }
            right(ui, |ui| {
                column(ui, 176.0, egui::Align::Max, &mut |ui| {
                    ui.label(caption(p, t("preset")));
                    preset_group(ui, cfg, p);
                });
            });
        });
    });

    theme::card(p).show(ui, |ui| {
        ui.set_width(w - 22.0);
        ui.label(theme::title(p, t("options_title")));
        ui.horizontal(|ui| {
            combo(ui, "button", &mut cfg.mouse_button, &["left", "right", "middle"], 95.0);
            combo(ui, "click_type", &mut cfg.click_type, &["single", "double", "triple", "hold_down"], 105.0);
            right(ui, |ui| {
                ui.radio_value(&mut cfg.hotkey_mode, "hold".to_string(), t("hold"));
                ui.radio_value(&mut cfg.hotkey_mode, "toggle".to_string(), t("toggle"));
            });
        });
    });

    theme::card(p).show(ui, |ui| {
        ui.set_width(w - 22.0);
        ui.horizontal(|ui| {
            ui.label(theme::title(p, t("location_title")));
            let (x, y) = cursor_pos();
            right(ui, |ui| ui.label(readout(format!("{x}, {y}"))));
        });
        ui.horizontal(|ui| {
            ui.radio_value(&mut cfg.location_mode, "cursor".to_string(), t("follow_cursor"));
            ui.add_space(12.0);
            ui.radio_value(&mut cfg.location_mode, "fixed".to_string(), t("fixed_coordinate"));
        });
        let fixed = cfg.location_mode == "fixed";
        ui.horizontal(|ui| {
            ui.label(caption(p, "X"));
            num_field(ui, "fixed_x", &mut cfg.fixed_x, 52.0, fixed, true, 0);
            ui.label(caption(p, "Y"));
            num_field(ui, "fixed_y", &mut cfg.fixed_y, 52.0, fixed, true, 0);
            if ui.add(egui::Button::new(btn(t("pick_location")))).clicked() {
                acts.push(Act::Pick);
            }
            right(ui, |ui| ui.add_enabled(fixed, egui::Checkbox::new(&mut cfg.restore_cursor, t("restore_cursor"))));
        });
    });

    theme::card(p).show(ui, |ui| {
        ui.set_width(w - 22.0);
        ui.label(theme::title(p, &format!("{} & JITTER", t("repeat_title"))));
        ui.horizontal(|ui| {
            ui.radio_value(&mut cfg.repeat_mode, "infinite".to_string(), t("until_stopped"));
            ui.add_space(12.0);
            ui.radio_value(&mut cfg.repeat_mode, "count".to_string(), format!("{}:", t("repeat_times")));
            num_field(ui, "repeat_count", &mut cfg.repeat_count, 52.0, cfg.repeat_mode == "count", false, 1);
        });
        ui.horizontal(|ui| {
            ui.checkbox(&mut cfg.jitter_enabled, t("jitter"));
            ui.add_enabled_ui(cfg.jitter_enabled, |ui| {
                ui.spacing_mut().slider_width = 90.0;
                ui.spacing_mut().interact_size.y = 14.0; // knob size follows this height
                ui.add(egui::Slider::new(&mut cfg.jitter_interval_pct, 1..=50).show_value(false).trailing_fill(true));
                ui.label(readout(format!("±{}%", cfg.jitter_interval_pct)));
                ui.add(egui::Slider::new(&mut cfg.jitter_position_px, 1..=20).show_value(false).trailing_fill(true));
                ui.label(readout(format!("±{}px", cfg.jitter_position_px)));
            });
        });
    });

    ui.add_space(4.0);
    let hk = key_label(&cfg.hotkey);
    let (text, fill, hover, color) = if snap.clicking {
        (format!("■  {} ({hk})", t("stop_clicking").to_uppercase()), theme::ALERT, theme::ALERT_HOVER, egui::Color32::WHITE)
    } else {
        (format!("▶  {} ({hk})", t("start_clicking").to_uppercase()), theme::PRIMARY, theme::PRIMARY_HOVER, theme::PRIMARY_TEXT)
    };
    if theme::action_button(ui, bold(text, 14.0).color(color), fill, hover, egui::vec2(w, 44.0)).clicked() {
        acts.push(Act::ToggleClick);
    }
}

/// The four CPS presets as one joined control; the one matching the current interval is lit.
fn preset_group(ui: &mut egui::Ui, cfg: &mut ClickerConfig, p: &Palette) {
    let height = ui.spacing().interact_size.y;
    egui::Frame::new().fill(p.panel_alt).stroke(egui::Stroke::new(1.0_f32, p.border)).corner_radius(theme::RADIUS_CONTROL).inner_margin(2).show(ui, |ui| {
        ui.spacing_mut().item_spacing.x = 2.0;
        ui.with_layout(egui::Layout::left_to_right(egui::Align::Center), |ui| {
            for (label, ms) in [("10", 100), ("50", 20), ("100", 10), ("MAX", 1)] {
                let active = cfg.total_interval_ms() == ms;
                let (fill, color) = if active { (p.hover, theme::CYAN) } else { (p.panel_alt, p.muted) };
                if theme::action_button(ui, mono(label, 11.0).color(color), fill, p.hover, egui::vec2(40.0, height - 4.0)).clicked() {
                    (cfg.interval_hours, cfg.interval_minutes, cfg.interval_seconds, cfg.interval_ms) = (0, 0, 0, ms);
                }
            }
        });
    });
}

/// Dropdown over canonical ids, showing translated labels.
pub fn combo(ui: &mut egui::Ui, id: &str, value: &mut String, options: &[&str], width: f32) {
    egui::ComboBox::from_id_salt(id).width(width).selected_text(t(value)).show_ui(ui, |ui| {
        for o in options {
            ui.selectable_value(value, o.to_string(), t(o));
        }
    });
}

#[cfg(test)]
mod tests {
    #[test]
    fn readout_matches_python() {
        assert_eq!(super::interval_readout(100), "10.0 CPS (100ms)");
        assert_eq!(super::interval_readout(1500), "1 click / 1.5s");
    }
}
