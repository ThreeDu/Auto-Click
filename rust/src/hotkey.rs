//! Hotkey strings ("f6", "ctrl+shift+a", "<f6>") <-> virtual-key codes, and the toggle/hold logic.
//! Names follow pynput, which is what the Python build writes into profiles.
use std::collections::HashSet;

const CTRL: u32 = 0x11;
const SHIFT: u32 = 0x10;
const ALT: u32 = 0x12;
const CMD: u32 = 0x5B;

#[rustfmt::skip]
const NAMED: &[(&str, u32)] = &[
    ("ctrl", CTRL), ("shift", SHIFT), ("alt", ALT), ("alt_gr", ALT), ("cmd", CMD),
    ("backspace", 0x08), ("tab", 0x09), ("enter", 0x0D), ("pause", 0x13), ("caps_lock", 0x14),
    ("esc", 0x1B), ("space", 0x20), ("page_up", 0x21), ("page_down", 0x22), ("end", 0x23),
    ("home", 0x24), ("left", 0x25), ("up", 0x26), ("right", 0x27), ("down", 0x28),
    ("print_screen", 0x2C), ("insert", 0x2D), ("delete", 0x2E), ("menu", 0x5D),
    ("num_lock", 0x90), ("scroll_lock", 0x91),
    ("media_volume_mute", 0xAD), ("media_volume_down", 0xAE), ("media_volume_up", 0xAF),
    ("media_next", 0xB0), ("media_previous", 0xB1), ("media_play_pause", 0xB3),
];

/// US-layout punctuation keys.
const PUNCT: &[(char, u32)] = &[
    (';', 0xBA), ('=', 0xBB), (',', 0xBC), ('-', 0xBD), ('.', 0xBE), ('/', 0xBF),
    ('`', 0xC0), ('[', 0xDB), ('\\', 0xDC), (']', 0xDD), ('\'', 0xDE),
];

const ALIASES: &[(&str, &str)] = &[
    ("control", "ctrl"), ("escape", "esc"), ("return", "enter"),
    ("del", "delete"), ("ins", "insert"), ("capslock", "caps_lock"),
];

/// Left/right modifiers become one key and numpad digits count as digits, like pynput's canonical().
pub fn normalize_vk(vk: u32) -> u32 {
    match vk {
        0xA0 | 0xA1 => SHIFT,
        0xA2 | 0xA3 => CTRL,
        0xA4 | 0xA5 => ALT,
        0x5C => CMD,
        0x60..=0x69 => vk - 0x30,
        _ => vk,
    }
}

pub fn is_modifier(vk: u32) -> bool {
    matches!(normalize_vk(vk), CTRL | SHIFT | ALT | CMD)
}

fn part_to_vk(part: &str) -> Option<u32> {
    let part = ALIASES.iter().find(|(a, _)| *a == part).map(|(_, n)| *n).unwrap_or(part);
    if let Some((_, vk)) = NAMED.iter().find(|(n, _)| *n == part) {
        return Some(*vk);
    }
    let mut chars = part.chars();
    if let (Some(c), None) = (chars.next(), chars.next()) {
        return match c {
            'a'..='z' => Some(c as u32 - 'a' as u32 + 0x41),
            '0'..='9' => Some(c as u32),
            _ => PUNCT.iter().find(|(p, _)| *p == c).map(|(_, vk)| *vk),
        };
    }
    if let Some(n) = part.strip_prefix('f').and_then(|n| n.parse::<u32>().ok()) {
        return (1..=24).contains(&n).then_some(0x6F + n);
    }
    part.strip_prefix("vk").and_then(|n| n.parse().ok())
}

/// Parses a hotkey string into its set of keys. None if empty or any part is unknown.
pub fn parse(s: &str) -> Option<Vec<u32>> {
    let lower = s.trim().to_lowercase();
    let keys: Option<Vec<u32>> = lower
        .split('+')
        .map(|p| p.trim().trim_matches(|c| c == '<' || c == '>'))
        .filter(|p| !p.is_empty())
        .map(part_to_vk)
        .collect();
    keys.filter(|k| !k.is_empty())
}

pub fn is_valid(s: &str) -> bool {
    parse(s).is_some()
}

/// Name for a captured key, in the format `parse` reads back.
pub fn vk_name(vk: u32) -> String {
    let vk = normalize_vk(vk);
    if let Some((n, _)) = NAMED.iter().find(|(_, v)| *v == vk) {
        return n.to_string();
    }
    match vk {
        0x41..=0x5A => ((vk - 0x41) as u8 + b'a') as char,
        0x30..=0x39 => vk as u8 as char,
        0x70..=0x87 => return format!("f{}", vk - 0x6F),
        _ => match PUNCT.iter().find(|(_, v)| *v == vk) {
            Some((c, _)) => *c,
            None => return format!("vk{vk}"),
        },
    }
    .to_string()
}

/// "ctrl+shift+a" style string; modifiers sorted alphabetically like the Python capture.
pub fn combo_string(mods: &HashSet<u32>, key: u32) -> String {
    let mut parts: Vec<String> = mods.iter().map(|m| vk_name(*m)).collect();
    parts.sort();
    parts.push(vk_name(key));
    parts.join("+")
}

/// What the user sees: "F6", "CTRL+SHIFT+A".
pub fn display(s: &str) -> String {
    s.to_uppercase().replace(['<', '>'], "")
}

#[derive(Debug, PartialEq)]
pub enum Action {
    ToggleClick,
    ToggleMacro,
    HoldStart,
    HoldStop,
}

/// Tracks pressed keys. Each combo fires once per press (auto-repeat ignored) and re-arms when one
/// of its keys is released. In hold mode the click combo starts on press and stops on release.
#[derive(Default)]
pub struct HotkeyState {
    pressed: HashSet<u32>,
    click_down: bool,
    macro_down: bool,
}

impl HotkeyState {
    pub fn on_key(&mut self, vk: u32, down: bool, click: Option<&[u32]>, macro_: Option<&[u32]>, hold_mode: bool) -> Vec<Action> {
        let vk = normalize_vk(vk);
        let mut out = Vec::new();
        let full = |pressed: &HashSet<u32>, combo: Option<&[u32]>| combo.is_some_and(|c| c.iter().all(|k| pressed.contains(&normalize_vk(*k))));
        let has = |combo: Option<&[u32]>| combo.is_some_and(|c| c.iter().any(|k| normalize_vk(*k) == vk));
        if down {
            self.pressed.insert(vk);
            if !self.click_down && full(&self.pressed, click) {
                self.click_down = true;
                out.push(if hold_mode { Action::HoldStart } else { Action::ToggleClick });
            }
            if !self.macro_down && full(&self.pressed, macro_) {
                self.macro_down = true;
                out.push(Action::ToggleMacro);
            }
        } else {
            self.pressed.remove(&vk);
            if self.click_down && has(click) {
                self.click_down = false;
                if hold_mode {
                    out.push(Action::HoldStop);
                }
            }
            if self.macro_down && has(macro_) {
                self.macro_down = false;
            }
        }
        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_python_formats() {
        assert_eq!(parse("F6"), Some(vec![0x75]));
        assert_eq!(parse("<f7>"), Some(vec![0x76]));
        assert_eq!(parse("ctrl+shift+a"), Some(vec![CTRL, SHIFT, 0x41]));
        assert_eq!(parse("<ctrl>+<shift>+a"), Some(vec![CTRL, SHIFT, 0x41]));
        assert_eq!(parse("Control+Escape"), Some(vec![CTRL, 0x1B]));
        assert_eq!(parse("f24"), Some(vec![0x87]));
        for bad in ["", "notakey", "f25", "+"] {
            assert!(!is_valid(bad), "{bad}");
        }
        for ok in ["f6", "a", "space", "5", "-", "page_up"] {
            assert!(is_valid(ok), "{ok}");
        }
    }

    #[test]
    fn names_round_trip() {
        for vk in [0x41, 0x35, 0x75, 0x20, 0xBD, 0x21, 0xA2, 0x65] {
            let name = vk_name(vk);
            assert_eq!(parse(&name), Some(vec![normalize_vk(vk)]), "{name}");
        }
        let mods: HashSet<u32> = [SHIFT, CTRL].into();
        assert_eq!(combo_string(&mods, 0x41), "ctrl+shift+a");
    }

    #[test]
    fn toggle_fires_once_per_press() {
        let mut s = HotkeyState::default();
        let f6 = parse("f6").unwrap();
        let f7 = parse("f7").unwrap();
        let mut run = |vk, down| s.on_key(vk, down, Some(&f6), Some(&f7), false);
        assert_eq!(run(0x75, true), vec![Action::ToggleClick]);
        assert!(run(0x75, true).is_empty()); // auto-repeat
        assert!(run(0x75, false).is_empty());
        assert_eq!(run(0x75, true), vec![Action::ToggleClick]);
        assert_eq!(run(0x76, true), vec![Action::ToggleMacro]);
    }

    #[test]
    fn hold_mode_with_combo_and_left_right_modifiers() {
        let mut s = HotkeyState::default();
        let combo = parse("ctrl+shift+a").unwrap();
        let mut run = |vk, down| s.on_key(vk, down, Some(&combo), None, true);
        assert!(run(0xA2, true).is_empty()); // left ctrl
        assert!(run(0xA1, true).is_empty()); // right shift
        assert_eq!(run(0x41, true), vec![Action::HoldStart]);
        assert!(run(0x41, true).is_empty());
        assert_eq!(run(0xA1, false), vec![Action::HoldStop]);
        assert!(run(0x41, false).is_empty());
    }
}
