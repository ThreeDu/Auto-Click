//! Click and macro worker threads. Timings are copied from core/clicker_engine.py and
//! core/macro_engine.py; change them only with a real-hardware test.
use crate::config::{ClickerConfig, MacroStep};
use crate::win::input::{cursor_pos, move_cursor, send_button, send_click};
use crate::win::timer::{precise_sleep, TimerResolution};
use rand::Rng;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Arc;
use std::thread::JoinHandle;
use std::time::{Duration, Instant};

type Notify = Arc<dyn Fn() + Send + Sync>;

/// Thread handle + stop flag shared by both engines.
#[derive(Default)]
struct Worker {
    stop: Arc<AtomicBool>,
    handle: Option<JoinHandle<()>>,
}

impl Worker {
    fn is_running(&self) -> bool {
        self.handle.as_ref().is_some_and(|h| !h.is_finished())
    }

    fn start(&mut self, body: impl FnOnce(&AtomicBool) + Send + 'static, on_stopped: Notify) {
        if self.is_running() {
            return;
        }
        let stop = Arc::new(AtomicBool::new(false));
        self.stop = stop.clone();
        self.handle = Some(std::thread::spawn(move || {
            let _res = TimerResolution::new();
            body(&stop);
            on_stopped();
        }));
    }

    /// Waits up to 0.5 s. The handle is kept while the thread is still alive so is_running stays
    /// true and a quick restart can't launch a second loop.
    fn stop(&mut self) {
        self.stop.store(true, Ordering::SeqCst);
        let deadline = Instant::now() + Duration::from_millis(500);
        while self.is_running() && Instant::now() < deadline {
            std::thread::sleep(Duration::from_millis(1));
        }
        if !self.is_running() {
            self.handle = None;
        }
    }
}

#[derive(Clone, Debug)]
pub struct ClickSettings {
    pub interval_ms: f64,
    pub button: String,
    pub click_type: String,
    pub fixed: Option<(i32, i32)>,
    pub repeat: u64, // 0 = until stopped
    pub jitter: bool,
    pub jitter_pct: f64, // 0.10 = ±10 %
    pub jitter_px: i32,
    pub restore_cursor: bool,
}

impl ClickSettings {
    pub fn from_config(c: &ClickerConfig) -> Self {
        Self {
            interval_ms: c.total_interval_ms().max(1) as f64,
            button: c.mouse_button.clone(),
            click_type: c.click_type.clone(),
            fixed: (c.location_mode == "fixed").then_some((c.fixed_x as i32, c.fixed_y as i32)),
            repeat: if c.repeat_mode == "count" { c.repeat_count.max(1) as u64 } else { 0 },
            jitter: c.jitter_enabled,
            jitter_pct: c.jitter_interval_pct.max(0) as f64 / 100.0,
            jitter_px: c.jitter_position_px.max(0) as i32,
            restore_cursor: c.restore_cursor,
        }
    }
}

#[derive(Default)]
pub struct Clicker {
    worker: Worker,
    pub count: Arc<AtomicU64>,
}

impl Clicker {
    pub fn is_running(&self) -> bool {
        self.worker.is_running()
    }

    pub fn stop(&mut self) {
        self.worker.stop();
    }

    pub fn start(&mut self, s: ClickSettings, on_stopped: Notify) {
        if self.is_running() {
            return;
        }
        self.count.store(0, Ordering::SeqCst);
        let count = self.count.clone();
        self.worker.start(move |stop| click_loop(&s, stop, &count), on_stopped);
    }
}

fn click_loop(s: &ClickSettings, stop: &AtomicBool, count: &AtomicU64) {
    if s.click_type == "hold_down" {
        // Keep the button pressed until stopped, so the user can drag windows/files
        if let Some((x, y)) = s.fixed {
            move_cursor(x, y);
        }
        send_button(&s.button, true);
        while !stop.load(Ordering::Relaxed) {
            std::thread::sleep(Duration::from_millis(5));
        }
        send_button(&s.button, false);
        return;
    }
    let clicks = match s.click_type.as_str() {
        "double" => 2,
        "triple" => 3,
        _ => 1,
    };
    let mut rng = rand::thread_rng();
    let mut next = Instant::now();
    while !stop.load(Ordering::Relaxed) {
        let (ox, oy) = cursor_pos();
        let (mut x, mut y) = s.fixed.unwrap_or((ox, oy));
        if s.jitter && s.jitter_px > 0 {
            x += rng.gen_range(-s.jitter_px..=s.jitter_px);
            y += rng.gen_range(-s.jitter_px..=s.jitter_px);
        }
        let moved = s.fixed.is_some() || s.jitter;
        if moved {
            move_cursor(x, y);
            precise_sleep(Duration::from_millis(2), stop);
        }
        send_click(&s.button, clicks, 2);
        if s.restore_cursor && moved {
            precise_sleep(Duration::from_millis(5), stop);
            move_cursor(ox, oy);
        }
        let n = count.fetch_add(1, Ordering::SeqCst) + 1;
        if s.repeat > 0 && n >= s.repeat {
            break;
        }
        if stop.load(Ordering::Relaxed) {
            break;
        }
        // Drift-compensated schedule; when behind, restart from now instead of bursting to catch up
        let mut ms = s.interval_ms;
        if s.jitter && s.jitter_pct > 0.0 {
            let v = ms * s.jitter_pct;
            ms = rng.gen_range((ms - v)..=(ms + v));
        }
        next += Duration::from_secs_f64(ms.max(1.0) / 1000.0);
        let now = Instant::now();
        if next > now {
            precise_sleep(next - now, stop);
        } else {
            next = now;
        }
    }
}

#[derive(Default)]
pub struct MacroRunner {
    worker: Worker,
}

impl MacroRunner {
    pub fn is_running(&self) -> bool {
        self.worker.is_running()
    }

    pub fn stop(&mut self) {
        self.worker.stop();
    }

    /// `repeat` 0 = loop until stopped.
    pub fn start(&mut self, steps: Vec<MacroStep>, repeat: u64, restore_cursor: bool, on_stopped: Notify) {
        if self.is_running() || steps.is_empty() {
            return;
        }
        self.worker.start(move |stop| macro_loop(&steps, repeat, restore_cursor, stop), on_stopped);
    }
}

fn macro_loop(steps: &[MacroStep], repeat: u64, restore: bool, stop: &AtomicBool) {
    let ms = |n: u64| Duration::from_millis(n);
    let mut iterations = 0u64;
    while !stop.load(Ordering::Relaxed) {
        for (i, step) in steps.iter().enumerate() {
            if stop.load(Ordering::Relaxed) {
                break;
            }
            // Delay runs BEFORE the action
            if step.delay_ms > 0 {
                precise_sleep(ms(step.delay_ms as u64), stop);
            }
            if stop.load(Ordering::Relaxed) {
                break;
            }
            let (x, y) = (step.x as i32, step.y as i32);
            match step.action.as_str() {
                "move" if !restore => move_cursor(x, y),
                a if a.starts_with("click_") => {
                    let button = &a["click_".len()..];
                    let orig = restore.then(cursor_pos);
                    move_cursor(x, y);
                    precise_sleep(ms(15), stop);
                    move_cursor(x, y); // re-confirm position before clicking
                    send_click(button, 1, 20);
                    if let Some((ox, oy)) = orig {
                        precise_sleep(ms(20), stop);
                        move_cursor(ox, oy);
                    }
                }
                _ => {} // wait, or move while restoring the cursor
            }
            if i + 1 == steps.len() {
                precise_sleep(ms(25), stop); // let the last click land before looping
            }
        }
        iterations += 1;
        if repeat > 0 && iterations >= repeat {
            break;
        }
    }
}
