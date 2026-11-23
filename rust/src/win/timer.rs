//! 1 ms timer resolution + hybrid sleep (port of core/timer.py).
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::{Duration, Instant};
use windows::Win32::Media::{timeBeginPeriod, timeEndPeriod};

/// Holds 1 ms system timer resolution while alive.
pub struct TimerResolution;

impl TimerResolution {
    pub fn new() -> Self {
        unsafe { timeBeginPeriod(1) };
        TimerResolution
    }
}

impl Drop for TimerResolution {
    fn drop(&mut self) {
        unsafe { timeEndPeriod(1) };
    }
}

/// Sleep in ≤20 ms slices until 2 ms remain, then busy-wait. Returns early once `stop` is set.
pub fn precise_sleep(d: Duration, stop: &AtomicBool) {
    let target = Instant::now() + d;
    if d > Duration::from_millis(3) {
        while !stop.load(Ordering::Relaxed) {
            let remaining = target.saturating_duration_since(Instant::now());
            if remaining <= Duration::from_millis(2) {
                break;
            }
            std::thread::sleep((remaining - Duration::from_millis(2)).min(Duration::from_millis(20)));
        }
    }
    while Instant::now() < target && !stop.load(Ordering::Relaxed) {
        std::hint::spin_loop();
    }
}
