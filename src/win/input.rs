//! Mouse output via SendInput / SetCursorPos (port of core/win32_input.py).
use std::time::{Duration, Instant};
use windows::Win32::Foundation::POINT;
use windows::Win32::UI::Input::KeyboardAndMouse::{
    SendInput, INPUT, INPUT_0, INPUT_MOUSE, MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP, MOUSEEVENTF_MIDDLEDOWN,
    MOUSEEVENTF_MIDDLEUP, MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP, MOUSEINPUT, MOUSE_EVENT_FLAGS,
};
use windows::Win32::UI::WindowsAndMessaging::{GetCursorPos, SetCursorPos};

fn flags(button: &str) -> (MOUSE_EVENT_FLAGS, MOUSE_EVENT_FLAGS) {
    match button {
        "right" => (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
        "middle" => (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
        _ => (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
    }
}

/// Tags every click we send, so the recording hook can skip exactly our own input.
pub const OUR_INPUT: usize = 0x41_43_4C_4B; // "ACLK"

fn mouse_input(flag: MOUSE_EVENT_FLAGS) -> INPUT {
    INPUT {
        r#type: INPUT_MOUSE,
        Anonymous: INPUT_0 { mi: MOUSEINPUT { dwFlags: flag, dwExtraInfo: OUR_INPUT, ..Default::default() } },
    }
}

fn send(inputs: &[INPUT]) {
    unsafe { SendInput(inputs, std::mem::size_of::<INPUT>() as i32) };
}

/// Busy-wait for short holds (1-20 ms), where sleep is too coarse.
fn spin(d: Duration) {
    let end = Instant::now() + d;
    while Instant::now() < end {
        std::hint::spin_loop();
    }
}

/// `clicks` clicks of `button`; `hold_ms` > 0 holds the button down that long (used by macros for reliability).
pub fn send_click(button: &str, clicks: u32, hold_ms: u64) {
    let (down, up) = flags(button);
    for i in 0..clicks {
        if hold_ms > 0 {
            send(&[mouse_input(down)]);
            spin(Duration::from_millis(hold_ms));
            send(&[mouse_input(up)]);
        } else {
            send(&[mouse_input(down), mouse_input(up)]);
        }
        if i + 1 < clicks {
            std::thread::sleep(Duration::from_millis(20));
        }
    }
}

/// Press or release only, for hold-to-drag.
pub fn send_button(button: &str, down: bool) {
    let (d, u) = flags(button);
    send(&[mouse_input(if down { d } else { u })]);
}

pub fn move_cursor(x: i32, y: i32) {
    unsafe {
        let _ = SetCursorPos(x, y);
    }
}

pub fn cursor_pos() -> (i32, i32) {
    let mut p = POINT::default();
    unsafe {
        let _ = GetCursorPos(&mut p);
    }
    (p.x, p.y)
}
