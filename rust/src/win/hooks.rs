//! Global input. Mouse buttons come from a low-level hook (installed only while recording or
//! picking); its callback just forwards events so the system never waits on us.
//!
//! The keyboard is polled with GetAsyncKeyState instead of hooked: a WH_KEYBOARD_LL hook gets no
//! events while our own eframe window has focus (verified with a bare eframe window), which would
//! break pressing F6 with the app in front.
use std::sync::atomic::{AtomicU32, Ordering};
use std::sync::OnceLock;
use windows::Win32::Foundation::{HINSTANCE, LPARAM, LRESULT, WPARAM};
use windows::Win32::System::LibraryLoader::GetModuleHandleW;
use windows::Win32::System::Threading::GetCurrentThreadId;
use windows::Win32::UI::Input::KeyboardAndMouse::GetAsyncKeyState;
use windows::Win32::UI::WindowsAndMessaging::{
    CallNextHookEx, GetMessageW, PostThreadMessageW, SetWindowsHookExW, UnhookWindowsHookEx, HHOOK, MSG,
    MSLLHOOKSTRUCT, WH_MOUSE_LL, WM_APP, WM_LBUTTONDOWN, WM_LBUTTONUP, WM_MBUTTONDOWN, WM_MBUTTONUP, WM_RBUTTONDOWN,
    WM_RBUTTONUP, WM_XBUTTONDOWN, WM_XBUTTONUP,
};

#[derive(Clone, Copy, Debug)]
pub enum InputEvent {
    Key { vk: u32, down: bool },
    /// button: 0 left, 1 right, 2 middle, 3 x-button. Physical screen coordinates.
    Mouse { button: u8, down: bool, x: i32, y: i32 },
}

type Callback = Box<dyn Fn(InputEvent) + Send + Sync>;
static CALLBACK: OnceLock<Callback> = OnceLock::new();
static THREAD_ID: AtomicU32 = AtomicU32::new(0);
const MSG_MOUSE_ON: u32 = WM_APP + 1;
const MSG_MOUSE_OFF: u32 = WM_APP + 2;

/// Physical key state, including keys injected by tools like AutoHotkey.
pub fn key_down(vk: u32) -> bool {
    unsafe { GetAsyncKeyState(vk as i32) < 0 }
}

unsafe extern "system" fn mouse_proc(code: i32, wparam: WPARAM, lparam: LPARAM) -> LRESULT {
    if code >= 0 {
        let info = &*(lparam.0 as *const MSLLHOOKSTRUCT);
        let ev = match wparam.0 as u32 {
            WM_LBUTTONDOWN => Some((0, true)),
            WM_LBUTTONUP => Some((0, false)),
            WM_RBUTTONDOWN => Some((1, true)),
            WM_RBUTTONUP => Some((1, false)),
            WM_MBUTTONDOWN => Some((2, true)),
            WM_MBUTTONUP => Some((2, false)),
            WM_XBUTTONDOWN => Some((3, true)),
            WM_XBUTTONUP => Some((3, false)),
            _ => None,
        };
        // Skip only our own clicks; other injected input (remote desktop, pen tablets) is real user input
        if info.dwExtraInfo != super::input::OUR_INPUT {
            if let (Some((button, down)), Some(cb)) = (ev, CALLBACK.get()) {
                cb(InputEvent::Mouse { button, down, x: info.pt.x, y: info.pt.y });
            }
        }
    }
    CallNextHookEx(None, code, wparam, lparam)
}

/// Starts the (idle) mouse-hook thread. Call once.
pub fn start(callback: impl Fn(InputEvent) + Send + Sync + 'static) {
    if CALLBACK.set(Box::new(callback)).is_err() {
        return;
    }
    std::thread::spawn(|| unsafe {
        THREAD_ID.store(GetCurrentThreadId(), Ordering::SeqCst);
        let hinst: HINSTANCE = GetModuleHandleW(None).map(|m| m.into()).unwrap_or_default();
        let mut mouse: Option<HHOOK> = None;
        let mut msg = MSG::default();
        while GetMessageW(&mut msg, None, 0, 0).as_bool() {
            match msg.message {
                MSG_MOUSE_ON if mouse.is_none() => match SetWindowsHookExW(WH_MOUSE_LL, Some(mouse_proc), hinst, 0) {
                    Ok(h) => mouse = Some(h),
                    Err(e) => crate::log!("[hooks] mouse hook failed: {e}"),
                },
                MSG_MOUSE_OFF => {
                    if let Some(h) = mouse.take() {
                        let _ = UnhookWindowsHookEx(h);
                    }
                }
                _ => {}
            }
        }
    });
}

/// The mouse hook is only installed while recording or picking a location.
pub fn set_mouse_hook(on: bool) {
    let tid = THREAD_ID.load(Ordering::SeqCst);
    if tid != 0 {
        unsafe {
            let _ = PostThreadMessageW(tid, if on { MSG_MOUSE_ON } else { MSG_MOUSE_OFF }, WPARAM(0), LPARAM(0));
        }
    }
}
