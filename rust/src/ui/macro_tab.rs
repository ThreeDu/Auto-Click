//! MACRO tab: step list, recording, loop options, run button.
use super::auto_tab::combo;
use super::theme::{self, bold, btn, caption, readout, Palette};
use super::{key_label, num_field, right, Act, Snap};
use crate::config::{ClickerConfig, MacroStep};
use crate::i18n::t;

const ACTIONS: [&str; 5] = ["click_left", "click_right", "click_middle", "move", "wait"];
/// (i18n key or literal, width) shared by the header and every row so they line up.
const COLUMNS: [(&str, f32); 6] = [("#", 24.0), ("action", 132.0), ("X", 70.0), ("Y", 70.0), ("delay", 84.0), ("", 26.0)];
const ROW_MARGIN: egui::Margin = egui::Margin { left: 6, right: 4, top: 2, bottom: 2 };
const LIST_HEIGHT: f32 = 224.0;

pub fn show(ui: &mut egui::Ui, cfg: &mut ClickerConfig, snap: &Snap, p: &Palette, acts: &mut Vec<Act>) {
    let w = ui.available_width();

    theme::card(p).show(ui, |ui| {
        ui.set_width(w - 22.0);
        ui.horizontal(|ui| {
            ui.label(theme::title(p, t("macro_title")));
            let total: i64 = cfg.macro_steps.iter().map(|s| s.delay_ms).sum();
            right(ui, |ui| ui.label(readout(format!("{} {} · {total} MS", cfg.macro_steps.len(), t("steps")))));
        });
        ui.horizontal(|ui| {
            if ui.button(btn(&format!("+ {}", t("add_step")))).clicked() {
                cfg.macro_steps.push(MacroStep::default());
            }
            let (rec_text, rec_color) = if snap.recording {
                (format!("■ {}", t("stop_record")), theme::ALERT)
            } else {
                (format!("● {}", t("record")), theme::AMBER)
            };
            if ui.button(btn(&rec_text).color(rec_color)).clicked() {
                acts.push(Act::Record(!snap.recording));
            }
            let mut real = snap.real_delay;
            if ui.checkbox(&mut real, t("real_delay")).changed() {
                acts.push(Act::RealDelay(real));
            }
            right(ui, |ui| {
                if ui.button(btn(t("clear_all")).color(theme::ALERT)).clicked() {
                    cfg.macro_steps.clear();
                }
            });
        });

        ui.add_space(2.0);
        let mut remove = None;
        let [c0, c1, c2, c3, c4, c5] = COLUMNS.map(|c| c.1);
        egui::Frame::new().fill(p.base).corner_radius(theme::RADIUS_CONTROL).inner_margin(4).show(ui, |ui| {
            // Header shares the row margins and cell widths, so every column lines up
            egui::Frame::new().inner_margin(ROW_MARGIN).show(ui, |ui| {
                ui.horizontal(|ui| {
                    for (text, width) in COLUMNS {
                        let align = if matches!(text, "X" | "Y" | "delay") { egui::Align::Center } else { egui::Align::Min };
                        theme::cell(ui, width, align, |ui| ui.label(caption(p, t(text))));
                    }
                });
            });
            egui::ScrollArea::vertical().max_height(LIST_HEIGHT).min_scrolled_height(LIST_HEIGHT).auto_shrink([false, false]).show(ui, |ui| {
                ui.spacing_mut().item_spacing.y = 2.0;
                if cfg.macro_steps.is_empty() {
                    ui.add_space(LIST_HEIGHT / 2.0 - 12.0);
                    ui.vertical_centered(|ui| ui.label(egui::RichText::new(t("no_steps")).color(p.dim)));
                }
                for (i, step) in cfg.macro_steps.iter_mut().enumerate() {
                    // Striped rows keep long lists readable
                    let fill = if i % 2 == 0 { p.panel } else { egui::Color32::TRANSPARENT };
                    egui::Frame::new().fill(fill).corner_radius(theme::RADIUS_CONTROL).inner_margin(ROW_MARGIN).show(ui, |ui| {
                        ui.horizontal(|ui| {
                            let left = egui::Align::Min;
                            theme::cell(ui, c0, left, |ui| ui.label(caption(p, &format!("{:02}", i + 1))));
                            theme::cell(ui, c1, left, |ui| combo(ui, &format!("action{i}"), &mut step.action, &ACTIONS, c1 - 12.0));
                            let wait = step.action == "wait";
                            theme::cell(ui, c2, left, |ui| num_field(ui, ("sx", i), &mut step.x, c2, !wait, true, 0));
                            theme::cell(ui, c3, left, |ui| num_field(ui, ("sy", i), &mut step.y, c3, !wait, true, 0));
                            theme::cell(ui, c4, left, |ui| num_field(ui, ("sd", i), &mut step.delay_ms, c4, true, false, 100));
                            if wait {
                                (step.x, step.y) = (0, 0);
                            }
                            let del = egui::Button::new(bold("×", 15.0).color(theme::ALERT)).fill(egui::Color32::TRANSPARENT).stroke(egui::Stroke::NONE).min_size(egui::vec2(c5, 24.0));
                            if ui.add(del).on_hover_cursor(egui::CursorIcon::PointingHand).clicked() {
                                remove = Some(i);
                            }
                        });
                    });
                }
            });
        });
        if let Some(i) = remove {
            cfg.macro_steps.remove(i);
        }
    });

    theme::card(p).show(ui, |ui| {
        ui.set_width(w - 22.0);
        ui.horizontal(|ui| {
            ui.radio_value(&mut cfg.macro_repeat_mode, "count".to_string(), format!("{}:", t("repeat")));
            num_field(ui, "macro_repeat", &mut cfg.macro_repeat_count, 46.0, cfg.macro_repeat_mode == "count", false, 1);
            cfg.macro_repeat_count = cfg.macro_repeat_count.max(1);
            ui.add_space(8.0);
            ui.radio_value(&mut cfg.macro_repeat_mode, "infinite".to_string(), t("infinite_loop"));
            right(ui, |ui| ui.checkbox(&mut cfg.restore_cursor, t("restore_cursor")));
        });
    });

    ui.add_space(4.0);
    let hk = key_label(&cfg.macro_hotkey);
    let (text, fill, hover) = if snap.macro_running {
        (format!("■  {} ({hk})", t("stop_macro").to_uppercase()), theme::ALERT, theme::ALERT_HOVER)
    } else {
        (format!("▶  {} ({hk})", t("run_macro").to_uppercase()), theme::CYAN, theme::CYAN_HOVER)
    };
    let enabled = snap.macro_running || !cfg.macro_steps.is_empty();
    let resp = ui.add_enabled_ui(enabled, |ui| theme::action_button(ui, bold(text, 14.0).color(egui::Color32::WHITE), fill, hover, egui::vec2(w, 44.0))).inner;
    if resp.clicked() {
        acts.push(Act::ToggleMacro);
    }
}
