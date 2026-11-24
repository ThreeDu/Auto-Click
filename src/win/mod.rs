pub mod hooks;
pub mod input;
pub mod timer;

use windows::Win32::Foundation::{HWND, RECT};
use windows::Win32::UI::WindowsAndMessaging::{
    GetWindowRect, IsIconic, IsWindowVisible, SetForegroundWindow, SetWindowPos, ShowWindow, HWND_NOTOPMOST,
    HWND_TOPMOST, SWP_NOMOVE, SWP_NOSIZE, SW_HIDE, SW_RESTORE, SW_SHOW,
};

fn hwnd(raw: isize) -> HWND {
    HWND(raw as *mut _)
}

pub fn hide_window(raw: isize) {
    unsafe {
        let _ = ShowWindow(hwnd(raw), SW_HIDE);
    }
}

pub fn is_window_visible(raw: isize) -> bool {
    unsafe { IsWindowVisible(hwnd(raw)).as_bool() }
}

/// Show, restore if minimized and bring to front. Briefly goes topmost so Windows lets it take
/// focus (same trick as restore_window in ui/app.py).
pub fn show_window(raw: isize, keep_topmost: bool) {
    let h = hwnd(raw);
    unsafe {
        let _ = ShowWindow(h, if IsIconic(h).as_bool() { SW_RESTORE } else { SW_SHOW });
        let _ = SetWindowPos(h, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE);
        if !keep_topmost {
            let _ = SetWindowPos(h, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE);
        }
        let _ = SetForegroundWindow(h);
    }
}

/// Outer window rectangle (title bar included), physical pixels.
pub fn window_rect(raw: isize) -> Option<(i32, i32, i32, i32)> {
    let mut r = RECT::default();
    unsafe { GetWindowRect(hwnd(raw), &mut r).ok()? };
    Some((r.left, r.top, r.right, r.bottom))
}
