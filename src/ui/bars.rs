//! Top status strip and bottom dock (profiles, PIN, HUD, TRAY).
use super::theme::{self, bold, btn, caption, data, Palette};
use super::{key_label, right, Act, Snap};
use crate::config::ClickerConfig;
use crate::i18n::t;

pub fn status(ui: &mut egui::Ui, cfg: &ClickerConfig, snap: &Snap, p: &Palette) {
    theme::card(p).show(ui, |ui| {
        ui.set_width(ui.available_width());
        ui.columns(3, |c| {
            let (text, color) = if snap.clicking { (t("active"), theme::PRIMARY) } else { (t("standby"), p.muted) };
            c[0].label(bold(text, 11.0).color(color));
            c[1].vertical_centered(|ui| ui.label(data(format!("CLICKS: {}", group(snap.count))).color(p.text)));
            right(&mut c[2], |ui| {
                ui.label(data(format!("[{}]", key_label(&cfg.hotkey))).color(theme::AMBER));
                ui.label(data(format!("CPS: {:.1}", snap.cps)).color(theme::CYAN));
            });
        });
    });
}

/// 12345 -> "12,345" (Python's `{:,}`).
fn group(n: u64) -> String {
    let s = n.to_string();
    let mut out = String::new();
    for (i, c) in s.chars().enumerate() {
        if i > 0 && (s.len() - i).is_multiple_of(3) {
            out.push(',');
        }
        out.push(c);
    }
    out
}

pub fn dock(ui: &mut egui::Ui, cfg: &mut ClickerConfig, snap: &Snap, p: &Palette, profiles: &[String], current: &str, acts: &mut Vec<Act>) {
    theme::card(p).show(ui, |ui| {
        ui.set_width(ui.available_width());
        ui.horizontal(|ui| {
            // Nine controls share one row: tighter padding keeps a gap between both button groups
            ui.spacing_mut().button_padding.x = 7.0;
            ui.spacing_mut().item_spacing.x = 5.0;
            ui.label(caption(p, t("profile")));
            egui::ComboBox::from_id_salt("profile").width(84.0).selected_text(current).show_ui(ui, |ui| {
                for name in profiles {
                    if ui.selectable_label(name == current, name).clicked() {
                        acts.push(Act::LoadProfile(name.clone())); // selecting loads, like the Python dropdown
                    }
                }
            });
            let small = btn;
            if ui.button(small(t("save"))).clicked() {
                acts.push(Act::SaveProfile);
            }
            if ui.button(small(t("new_profile"))).clicked() {
                acts.push(Act::NewProfile);
            }
            if ui.add_enabled(profiles.iter().any(|n| n == current), egui::Button::new(small(t("delete")).color(theme::ALERT))).clicked() {
                acts.push(Act::DeleteProfile);
            }
            right(ui, |ui| {
                if ui.button(small(t("tray"))).clicked() {
                    acts.push(Act::ToTray);
                }
                let hud = if snap.hud_visible { small(t("hud")).color(theme::CYAN) } else { small(t("hud")) };
                if ui.button(hud).clicked() {
                    acts.push(Act::ToggleHud);
                }
                let pin = if cfg.always_on_top { small(t("pin")).color(theme::CYAN) } else { small(t("pin")) };
                if ui.add(egui::Button::new(pin).fill(if cfg.always_on_top { p.hover } else { p.panel_alt })).clicked() {
                    cfg.always_on_top = !cfg.always_on_top;
                }
            });
        });
    });
}

#[cfg(test)]
mod tests {
    #[test]
    fn groups_thousands() {
        assert_eq!(super::group(0), "0");
        assert_eq!(super::group(999), "999");
        assert_eq!(super::group(1234567), "1,234,567");
    }
}
