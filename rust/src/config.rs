//! Settings schema and profile storage. Same JSON format and folder as the Python build,
//! so both read each other's `profiles/*.json`.
use serde::{Deserialize, Serialize};
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct MacroStep {
    pub action: String, // click_left | click_right | click_middle | move | wait
    pub x: i64,
    pub y: i64,
    pub delay_ms: i64,
}

impl Default for MacroStep {
    fn default() -> Self {
        Self { action: "click_left".into(), x: 0, y: 0, delay_ms: 100 }
    }
}

/// Field names, order and defaults mirror `config.py`. Missing keys take defaults and unknown keys
/// are ignored, like `ClickerConfig.from_dict`.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct ClickerConfig {
    pub interval_hours: i64,
    pub interval_minutes: i64,
    pub interval_seconds: i64,
    pub interval_ms: i64,
    pub mouse_button: String,
    pub click_type: String,
    pub hotkey: String,
    pub macro_hotkey: String,
    pub hotkey_mode: String,
    pub location_mode: String,
    pub fixed_x: i64,
    pub fixed_y: i64,
    pub repeat_mode: String,
    pub repeat_count: i64,
    pub jitter_enabled: bool,
    pub jitter_interval_pct: i64,
    pub jitter_position_px: i64,
    pub always_on_top: bool,
    pub language: String,
    pub theme: String,
    pub macro_steps: Vec<MacroStep>,
    pub macro_repeat_mode: String,
    pub macro_repeat_count: i64,
    pub restore_cursor: bool,
}

impl Default for ClickerConfig {
    fn default() -> Self {
        Self {
            interval_hours: 0,
            interval_minutes: 0,
            interval_seconds: 0,
            interval_ms: 100,
            mouse_button: "left".into(),
            click_type: "single".into(),
            hotkey: "f6".into(),
            macro_hotkey: "f7".into(),
            hotkey_mode: "toggle".into(),
            location_mode: "cursor".into(),
            fixed_x: 0,
            fixed_y: 0,
            repeat_mode: "infinite".into(),
            repeat_count: 100,
            jitter_enabled: false,
            jitter_interval_pct: 10,
            jitter_position_px: 3,
            always_on_top: false,
            language: "en".into(),
            theme: "dark".into(),
            macro_steps: Vec::new(),
            macro_repeat_mode: "count".into(),
            macro_repeat_count: 1,
            restore_cursor: false,
        }
    }
}

impl ClickerConfig {
    pub fn total_interval_ms(&self) -> i64 {
        self.interval_hours * 3_600_000 + self.interval_minutes * 60_000 + self.interval_seconds * 1000 + self.interval_ms
    }

    /// Missing or unreadable file gives defaults, like `ClickerConfig.load_from_file`.
    pub fn load(path: &Path) -> Self {
        match fs::read_to_string(path) {
            Ok(text) => serde_json::from_str(&text).unwrap_or_else(|e| {
                crate::log!("Error loading config from {}: {e}", path.display());
                Self::default()
            }),
            Err(_) => Self::default(),
        }
    }

    /// Writes to `<path>.tmp` then renames, so a crash mid-write never leaves a half-written file.
    pub fn save(&self, path: &Path) -> io::Result<()> {
        let tmp = PathBuf::from(format!("{}.tmp", path.display()));
        let result = (|| {
            if let Some(dir) = path.parent() {
                fs::create_dir_all(dir)?;
            }
            let mut buf = Vec::new();
            let mut ser = serde_json::Serializer::with_formatter(&mut buf, serde_json::ser::PrettyFormatter::with_indent(b"    "));
            self.serialize(&mut ser).map_err(io::Error::other)?;
            fs::write(&tmp, &buf)?;
            fs::rename(&tmp, path)
        })();
        if let Err(e) = &result {
            crate::log!("Error saving config to {}: {e}", path.display());
            let _ = fs::remove_file(&tmp);
        }
        result
    }
}

const SESSION: &str = "_last_session";

pub struct Profiles {
    pub dir: PathBuf,
}

impl Profiles {
    /// Uses `preferred` if writable, else `%APPDATA%\AutoClicker\profiles` (same fallback as profile_manager.py).
    pub fn new(preferred: PathBuf) -> Self {
        let writable = fs::create_dir_all(&preferred).is_ok() && {
            let probe = preferred.join(".write_test");
            let ok = fs::write(&probe, "ok").is_ok();
            let _ = fs::remove_file(&probe);
            ok
        };
        if writable {
            return Self { dir: preferred };
        }
        let base = std::env::var_os("APPDATA").map(PathBuf::from).unwrap_or_else(|| PathBuf::from("."));
        let dir = base.join("AutoClicker").join("profiles");
        let _ = fs::create_dir_all(&dir);
        Self { dir }
    }

    /// Safe as a Windows filename and not clashing with `_last_session`.
    pub fn is_valid_name(name: &str) -> bool {
        let name = name.trim();
        if name.is_empty() || name.chars().count() > 64 || name.starts_with('_') || name.ends_with('.') {
            return false;
        }
        if name.chars().any(|c| "<>:\"/\\|?*".contains(c) || (c as u32) < 32) {
            return false;
        }
        let stem = name.split('.').next().unwrap_or("").to_lowercase();
        let reserved = ["con", "prn", "aux", "nul"].contains(&stem.as_str())
            || ((stem.starts_with("com") || stem.starts_with("lpt"))
                && stem.len() == 4
                && matches!(stem.as_bytes()[3], b'1'..=b'9'));
        !reserved
    }

    fn path(&self, name: &str) -> PathBuf {
        self.dir.join(format!("{}.json", name.trim()))
    }

    pub fn list(&self) -> Vec<String> {
        let mut names: Vec<String> = fs::read_dir(&self.dir)
            .into_iter()
            .flatten()
            .flatten()
            .filter_map(|e| e.file_name().to_str().and_then(|n| n.strip_suffix(".json")).map(String::from))
            .filter(|n| n != SESSION)
            .collect();
        names.sort();
        names
    }

    pub fn save(&self, name: &str, cfg: &ClickerConfig) -> bool {
        Self::is_valid_name(name) && cfg.save(&self.path(name)).is_ok()
    }

    pub fn load(&self, name: &str) -> ClickerConfig {
        ClickerConfig::load(&self.path(name))
    }

    pub fn delete(&self, name: &str) {
        if let Err(e) = fs::remove_file(self.path(name)) {
            crate::log!("Error deleting profile {name}: {e}");
        }
    }

    pub fn save_session(&self, cfg: &ClickerConfig) {
        let _ = cfg.save(&self.path(SESSION));
    }

    pub fn load_session(&self) -> Option<ClickerConfig> {
        let p = self.path(SESSION);
        p.exists().then(|| ClickerConfig::load(&p))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tmpdir(tag: &str) -> PathBuf {
        let d = std::env::temp_dir().join(format!("autoclicker-test-{tag}-{}", std::process::id()));
        let _ = fs::remove_dir_all(&d);
        fs::create_dir_all(&d).unwrap();
        d
    }

    #[test]
    fn reads_python_written_json() {
        // json.dump output from the Python build: ASCII-escaped unicode, an unknown key, missing fields
        let text = r#"{"interval_ms": 5, "removed_field": 1, "language": "vi",
            "macro_steps": [{"action": "move", "x": -20, "y": 2}], "hotkey": "<f6>"}"#;
        let c: ClickerConfig = serde_json::from_str(text).unwrap();
        assert_eq!(c.interval_ms, 5);
        assert_eq!(c.hotkey, "<f6>");
        assert_eq!(c.macro_hotkey, "f7");
        assert_eq!(c.macro_steps[0], MacroStep { action: "move".into(), x: -20, y: 2, delay_ms: 100 });
        let n: ClickerConfig = serde_json::from_str(r#"{"language": "Tiếng"}"#).unwrap();
        assert_eq!(n.language, "Tiếng");
    }

    #[test]
    fn real_profiles_round_trip() {
        // Every profile the user already has must load with no field lost
        let dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("../profiles");
        for entry in fs::read_dir(dir).into_iter().flatten().flatten() {
            let path = entry.path();
            if path.extension().is_some_and(|e| e == "json") {
                let text = fs::read_to_string(&path).unwrap();
                let raw: serde_json::Value = serde_json::from_str(&text).unwrap();
                let cfg: ClickerConfig = serde_json::from_str(&text).unwrap();
                let back = serde_json::to_value(&cfg).unwrap();
                for (k, v) in raw.as_object().unwrap() {
                    assert_eq!(back.get(k), Some(v), "{}: field {k}", path.display());
                }
            }
        }
    }

    #[test]
    fn save_load_round_trip_leaves_no_tmp() {
        let d = tmpdir("rt");
        let p = d.join("p.json");
        let c = ClickerConfig { interval_ms: 7, macro_steps: vec![MacroStep { action: "move".into(), x: 1, y: 2, delay_ms: 3 }], ..Default::default() };
        c.save(&p).unwrap();
        assert_eq!(ClickerConfig::load(&p), c);
        assert_eq!(fs::read_dir(&d).unwrap().count(), 1);
        assert!(fs::read_to_string(&p).unwrap().contains("\n    \"interval_hours\": 0,"));
    }

    #[test]
    fn failed_save_keeps_old_file() {
        let d = tmpdir("fail");
        let p = d.join("p.json");
        ClickerConfig { interval_ms: 7, ..Default::default() }.save(&p).unwrap();
        // Target is now a directory, so the rename fails
        let blocked = d.join("blocked.json");
        fs::create_dir_all(blocked.join("x")).unwrap();
        assert!(ClickerConfig::default().save(&blocked).is_err());
        assert!(!d.join("blocked.json.tmp").exists());
        assert_eq!(ClickerConfig::load(&p).interval_ms, 7);
    }

    #[test]
    fn profile_names() {
        for ok in ["default", "Game 1", "tiếng việt", "a.b"] {
            assert!(Profiles::is_valid_name(ok), "{ok}");
        }
        let long = "a".repeat(65);
        for bad in ["", "   ", "a/b", "a\\b", "a:b", "what?", "_last_session", "CON", "com1", "nul.txt", "x.", long.as_str()] {
            assert!(!Profiles::is_valid_name(bad), "{bad}");
        }
        assert!(Profiles::is_valid_name("com0") && Profiles::is_valid_name("console"));
    }

    #[test]
    fn profiles_skip_session_and_reject_bad_names() {
        let pm = Profiles::new(tmpdir("pm"));
        assert!(!pm.save("_last_session", &ClickerConfig::default()));
        assert!(pm.save("ok", &ClickerConfig::default()));
        pm.save_session(&ClickerConfig::default());
        assert_eq!(pm.list(), vec!["ok".to_string()]);
        assert!(pm.load_session().is_some());
    }
}
