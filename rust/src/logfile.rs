//! The release exe has no console, so messages and panics go to `profiles/autoclicker.log`.
use std::fs::{File, OpenOptions};
use std::io::Write;
use std::path::Path;
use std::sync::Mutex;

static FILE: Mutex<Option<File>> = Mutex::new(None);

#[macro_export]
macro_rules! log {
    ($($arg:tt)*) => { $crate::logfile::write(&format!($($arg)*)) };
}

pub fn init(dir: &Path) {
    let path = dir.join("autoclicker.log");
    // Start fresh once the log passes 1 MB so it can't grow forever
    let big = std::fs::metadata(&path).map(|m| m.len() > 1_000_000).unwrap_or(false);
    let file = OpenOptions::new().create(true).append(!big).write(true).truncate(big).open(&path);
    if let Ok(f) = file {
        *FILE.lock().unwrap_or_else(|e| e.into_inner()) = Some(f);
    }
    let now = unsafe { windows::Win32::System::SystemInformation::GetLocalTime() };
    write(&format!(
        "\n=== AutoClicker (Rust) started {:04}-{:02}-{:02} {:02}:{:02}:{:02} ===",
        now.wYear, now.wMonth, now.wDay, now.wHour, now.wMinute, now.wSecond
    ));
    std::panic::set_hook(Box::new(|info| write(&format!("PANIC: {info}"))));
}

pub fn write(msg: &str) {
    if cfg!(debug_assertions) {
        eprintln!("{msg}");
    }
    if let Some(f) = FILE.lock().unwrap_or_else(|e| e.into_inner()).as_mut() {
        let _ = writeln!(f, "{msg}");
    }
}
