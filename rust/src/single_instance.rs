//! One instance at a time. Same mutex name and port as main.py, so the Python and Rust builds
//! also exclude each other (they share profiles/).
use crate::core::Core;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::Arc;
use std::time::Duration;
use windows::core::w;
use windows::Win32::Foundation::{GetLastError, ERROR_ALREADY_EXISTS};
use windows::Win32::System::Threading::CreateMutexW;

const ADDR: &str = "127.0.0.1:47829";

/// True if this is the first instance. The mutex handle is intentionally never closed.
pub fn acquire() -> bool {
    unsafe {
        let handle = CreateMutexW(None, false, w!("AutoClicker_SingleInstance_Mutex_v1"));
        !(handle.is_ok() && GetLastError() == ERROR_ALREADY_EXISTS)
    }
}

/// Asks the running instance to show its window.
pub fn signal_existing() {
    if let Ok(addr) = ADDR.parse() {
        if let Ok(mut s) = TcpStream::connect_timeout(&addr, Duration::from_millis(300)) {
            let _ = s.write_all(b"SHOW\n");
        }
    }
}

pub fn serve(core: Arc<Core>) {
    let listener = match TcpListener::bind(ADDR) {
        Ok(l) => l,
        Err(e) => {
            crate::log!("Single instance server start failed: {e}");
            return;
        }
    };
    std::thread::spawn(move || {
        for mut conn in listener.incoming().flatten() {
            let mut buf = [0u8; 64];
            let _ = conn.set_read_timeout(Some(Duration::from_millis(500)));
            if let Ok(n) = conn.read(&mut buf) {
                if buf[..n].windows(4).any(|w| w == b"SHOW") {
                    core.show_window();
                }
            }
        }
    });
}
