//! English / Vietnamese strings. Keys match i18n/strings_*.py; keys below "Rust build" replace
//! text the Python UI had hardcoded in English.
use std::sync::atomic::{AtomicBool, Ordering};

static VIETNAMESE: AtomicBool = AtomicBool::new(false);

pub fn set_language(code: &str) {
    VIETNAMESE.store(code == "vi", Ordering::Relaxed);
}

/// Returns the key itself when missing, like `t()` in localization.py.
pub fn t(key: &str) -> &str {
    let vi = VIETNAMESE.load(Ordering::Relaxed);
    STRINGS.iter().find(|(k, _, _)| *k == key).map(|(_, en, v)| if vi { *v } else { *en }).unwrap_or(key)
}

pub const LANGUAGES: [(&str, &str); 2] = [("en", "English"), ("vi", "Tiếng Việt")];

#[rustfmt::skip]
const STRINGS: &[(&str, &str, &str)] = &[
    ("app_title", "AutoClicker", "AutoClicker"),
    ("interval_title", "Click Interval", "Khoảng cách click"),
    ("hours", "Hours", "Giờ"),
    ("minutes", "Minutes", "Phút"),
    ("seconds", "Seconds", "Giây"),
    ("milliseconds", "Milliseconds", "Mili-giây"),
    ("options_title", "Click Options", "Tùy chọn click"),
    ("left", "Left", "Trái"),
    ("right", "Right", "Phải"),
    ("middle", "Middle", "Giữa"),
    ("single", "Single", "Đơn"),
    ("double", "Double", "Kép"),
    ("triple", "Triple", "Ba"),
    ("hold_down", "Hold down", "Giữ chuột"),
    ("toggle", "Toggle", "Bật/Tắt"),
    ("hold", "Hold", "Giữ"),
    ("location_title", "Click Location", "Vị trí click"),
    ("follow_cursor", "Follow Cursor", "Theo con trỏ"),
    ("fixed_coordinate", "Fixed Coordinate", "Tọa độ cố định"),
    ("pick_location", "Pick Location", "Chọn vị trí"),
    ("repeat_title", "Repeat Rules", "Quy tắc lặp lại"),
    ("until_stopped", "Until Stopped", "Đến khi dừng"),
    ("repeat_times", "Repeat Times", "Số lần lặp"),
    ("macro_title", "Macro Builder", "Tạo Macro"),
    ("action", "Action", "Hành động"),
    ("delay", "Delay (ms)", "Độ trễ (ms)"),
    ("add_step", "Add Step", "Thêm bước"),
    ("record", "Record", "Ghi hình"),
    ("real_delay", "Real delay", "Delay thực"),
    ("clear_all", "Clear All", "Xóa tất cả"),
    ("run_macro", "Run Macro", "Chạy Macro"),
    ("stop_macro", "Stop Macro", "Dừng Macro"),
    ("repeat", "Repeat", "Lặp lại"),
    ("click_left", "Click Left", "Click trái"),
    ("click_right", "Click Right", "Click phải"),
    ("click_middle", "Click Middle", "Click giữa"),
    ("move", "Move", "Di chuyển"),
    ("wait", "Wait", "Chờ"),
    ("profile", "Profile", "Hồ sơ"),
    ("save", "Save", "Lưu"),
    ("save_as", "Save As", "Lưu thành..."),
    ("delete", "Delete", "Xóa"),
    ("clicks", "Clicks:", "Số click:"),
    ("cps", "CPS:", "CPS:"),
    ("stop", "Stop", "Dừng"),
    ("start_clicking", "Start Clicking", "Bắt đầu Click"),
    ("stop_clicking", "Stop Clicking", "Dừng Click"),
    ("show_hide", "Show/Hide", "Hiện/Ẩn"),
    ("exit", "Exit", "Thoát"),
    ("language", "Language", "Ngôn ngữ"),
    ("theme", "Theme", "Giao diện"),
    ("dark", "Dark", "Tối"),
    ("light", "Light", "Sáng"),
    ("mini_hud", "Show Mini HUD", "Hiện Mini HUD"),
    ("confirm_delete", "Are you sure you want to delete this profile?", "Bạn có chắc chắn muốn xóa hồ sơ này không?"),
    ("profile_name_prompt", "Enter profile name:", "Nhập tên hồ sơ:"),
    ("invalid_profile_name", "Invalid profile name. Avoid \\ / : * ? \" < > |, a leading \"_\" and reserved names like CON.", "Tên hồ sơ không hợp lệ. Không dùng \\ / : * ? \" < > |, dấu \"_\" ở đầu hoặc tên hệ thống như CON."),
    ("profile_save_failed", "Could not save the profile. Check the log file for details.", "Không thể lưu hồ sơ. Xem file log để biết chi tiết."),
    ("restore_cursor", "Restore Cursor", "Giữ nguyên chuột"),
    ("reset_hotkeys", "Reset Defaults", "Khôi phục mặc định"),
    ("hotkeys_reset_success", "✓ Restored default keybinds: [F6] / [F7]", "✓ Đã khôi phục phím mặc định: [F6] / [F7]"),
    // Rust build
    ("tab_auto", "AUTO CLICK", "AUTO CLICK"),
    ("tab_macro", "MACRO", "MACRO"),
    ("tab_settings", "SETTINGS", "CÀI ĐẶT"),
    ("standby", "● STANDBY", "● CHỜ"),
    ("active", "● ACTIVE", "● ĐANG CHẠY"),
    ("running", "● RUNNING", "● ĐANG CHẠY"),
    ("preset", "PRESET", "MẪU"),
    ("max_speed", "MAX SPEED (1ms)", "TỐC ĐỘ TỐI ĐA (1ms)"),
    ("jitter", "Jitter:", "Jitter:"),
    ("infinite_loop", "Repeat (∞ Loop)", "Lặp vô hạn (∞)"),
    ("steps", "STEPS", "BƯỚC"),
    ("no_steps", "No steps yet. Click + Add Step, or Record to capture clicks.", "Chưa có bước nào. Bấm + Thêm bước, hoặc Ghi hình để ghi lại các click."),
    ("stop_record", "Stop", "Dừng"),
    ("preferences", "PREFERENCES", "TÙY CHỌN"),
    ("hotkeys", "HOTKEYS", "PHÍM TẮT"),
    ("click_key", "Auto Click Key:", "Phím Auto Click:"),
    ("macro_key", "Macro Key:", "Phím Macro:"),
    ("record_key", "RECORD", "GHI PHÍM"),
    ("press_key", "PRESS KEY...", "NHẤN PHÍM..."),
    ("press_key_hint", "Press any key (F1-F12, letter, number) or ESC to cancel...", "Nhấn một phím (F1-F12, chữ, số) hoặc ESC để hủy..."),
    ("binding_cancelled", "Binding cancelled.", "Đã hủy gán phím."),
    ("invalid_key", "Not a valid hotkey:", "Phím không hợp lệ:"),
    ("key_set", "✓ Key set to:", "✓ Đã đặt phím:"),
    ("new_profile", "+NEW", "+MỚI"),
    ("pin", "PIN", "GHIM"),
    ("hud", "HUD", "HUD"),
    ("tray", "TRAY", "KHAY"),
    ("tray_toggle_click", "Start/Stop clicking", "Bật/Tắt click"),
    ("tray_toggle_macro", "Run/Stop macro", "Chạy/Dừng macro"),
    ("picker_banner", "LEFT-CLICK to pick location  ·  [Esc] to cancel", "CLICK CHUỘT TRÁI để chọn vị trí  ·  [Esc] để hủy"),
    ("cancel", "Cancel", "Hủy"),
    ("ok", "OK", "OK"),
    ("yes", "Yes", "Có"),
    ("no", "No", "Không"),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lookup_and_fallback() {
        set_language("vi");
        assert_eq!(t("hold_down"), "Giữ chuột");
        set_language("en");
        assert_eq!(t("hold_down"), "Hold down");
        assert_eq!(t("no_such_key"), "no_such_key");
    }

    #[test]
    fn no_duplicate_keys() {
        let mut keys: Vec<_> = STRINGS.iter().map(|s| s.0).collect();
        keys.sort();
        let n = keys.len();
        keys.dedup();
        assert_eq!(n, keys.len());
    }
}
