//! Controller: owns the config, engines and input-driven modes (hotkeys, recording, picking,
//! key capture). Runs on its own thread so hotkeys work while the window is hidden in the tray,
//! when egui isn't updating.
use crate::config::{ClickerConfig, MacroStep, Profiles};
use crate::engine::{ClickSettings, Clicker, MacroRunner};
use crate::hotkey::{self, Action, HotkeyState};
use crate::i18n::t;
use crate::win::{self, hooks, hooks::InputEvent, input::cursor_pos};
use std::collections::HashSet;
use std::sync::atomic::{AtomicIsize, Ordering};
use std::sync::mpsc;
use std::sync::{Arc, Mutex, MutexGuard, OnceLock};
use std::time::{Duration, Instant};

#[derive(Clone, Copy, PartialEq, Debug)]
pub enum CaptureTarget {
    Click,
    Macro,
}

#[derive(Clone, Copy, PartialEq)]
pub enum StatusKind {
    Info,
    Ok,
    Error,
}

/// Transient state shared with the UI (not saved).
pub struct State {
    pub recording: bool,
    pub real_delay: bool,
    last_record: Option<Instant>,
    pub picking: bool,
    pub capture: Option<CaptureTarget>,
    capture_mods: HashSet<u32>,
    pub status: Option<(String, StatusKind)>,
    pub hud_visible: bool,
    cps_start: Instant,
}

pub struct Core {
    pub cfg: Mutex<ClickerConfig>,
    pub profiles: Profiles,
    pub state: Mutex<State>,
    clicker: Mutex<Clicker>,
    runner: Mutex<MacroRunner>,
    ctx: OnceLock<egui::Context>,
    hwnd: AtomicIsize,
    saved: Mutex<ClickerConfig>,
}

fn lock<T>(m: &Mutex<T>) -> MutexGuard<'_, T> {
    // A panicked holder must not take the whole app down with it
    m.lock().unwrap_or_else(|e| e.into_inner())
}

impl Core {
    pub fn new(cfg: ClickerConfig, profiles: Profiles) -> Arc<Self> {
        Arc::new(Self {
            saved: Mutex::new(cfg.clone()),
            cfg: Mutex::new(cfg),
            profiles,
            state: Mutex::new(State {
                recording: false,
                real_delay: false,
                last_record: None,
                picking: false,
                capture: None,
                capture_mods: HashSet::new(),
                status: None,
                hud_visible: false,
                cps_start: Instant::now(),
            }),
            clicker: Mutex::default(),
            runner: Mutex::default(),
            ctx: OnceLock::new(),
            hwnd: AtomicIsize::new(0),
        })
    }

    /// Called once the window exists: starts the hook and controller threads.
    pub fn attach(self: &Arc<Self>, ctx: egui::Context, hwnd: isize) {
        let _ = self.ctx.set(ctx);
        self.hwnd.store(hwnd, Ordering::SeqCst);
        let (tx, rx) = mpsc::channel::<InputEvent>();
        let mouse_tx = tx.clone();
        hooks::start(move |ev| {
            let _ = mouse_tx.send(ev);
        });
        let core = self.clone();
        std::thread::spawn(move || core.poll_keys(tx));
        let core = self.clone();
        std::thread::spawn(move || {
            let mut keys = HotkeyState::default();
            loop {
                match rx.recv_timeout(Duration::from_millis(500)) {
                    Ok(ev) => core.on_input(&mut keys, ev),
                    Err(mpsc::RecvTimeoutError::Timeout) => {}
                    Err(mpsc::RecvTimeoutError::Disconnected) => break,
                }
                core.autosave();
            }
        });
    }

    pub fn lock_cfg(&self) -> MutexGuard<'_, ClickerConfig> {
        lock(&self.cfg)
    }

    pub fn lock_state(&self) -> MutexGuard<'_, State> {
        lock(&self.state)
    }

    pub fn repaint(&self) {
        if let Some(ctx) = self.ctx.get() {
            ctx.request_repaint();
        }
    }

    fn notify(&self) -> Arc<dyn Fn() + Send + Sync> {
        let ctx = self.ctx.get().cloned();
        Arc::new(move || {
            if let Some(c) = &ctx {
                c.request_repaint();
            }
        })
    }

    // ── Clicking ────────────────────────────────────────────────

    pub fn clicking(&self) -> bool {
        lock(&self.clicker).is_running()
    }

    pub fn click_count(&self) -> u64 {
        lock(&self.clicker).count.load(Ordering::Relaxed)
    }

    pub fn cps(&self) -> f64 {
        let secs = lock(&self.state).cps_start.elapsed().as_secs_f64();
        if secs > 0.0 { self.click_count() as f64 / secs } else { 0.0 }
    }

    pub fn start_click(&self) {
        let settings = ClickSettings::from_config(&self.lock_cfg());
        let notify = self.notify();
        let mut c = lock(&self.clicker);
        if !c.is_running() {
            lock(&self.state).cps_start = Instant::now();
            c.start(settings, notify);
        }
        drop(c);
        self.repaint();
    }

    pub fn stop_click(&self) {
        lock(&self.clicker).stop();
        self.repaint();
    }

    pub fn toggle_click(&self) {
        if self.clicking() { self.stop_click() } else { self.start_click() }
    }

    // ── Macro ───────────────────────────────────────────────────

    pub fn macro_running(&self) -> bool {
        lock(&self.runner).is_running()
    }

    pub fn start_macro(&self) {
        let (steps, repeat, restore) = {
            let c = self.lock_cfg();
            let repeat = if c.macro_repeat_mode == "count" { c.macro_repeat_count.max(1) as u64 } else { 0 };
            (c.macro_steps.clone(), repeat, c.restore_cursor)
        };
        let notify = self.notify();
        lock(&self.runner).start(steps, repeat, restore, notify);
        self.repaint();
    }

    pub fn stop_macro(&self) {
        lock(&self.runner).stop();
        self.repaint();
    }

    pub fn toggle_macro(&self) {
        if self.macro_running() { self.stop_macro() } else { self.start_macro() }
    }

    // ── Recording / picking / key capture ───────────────────────

    pub fn set_recording(&self, on: bool) {
        let mut s = self.lock_state();
        s.recording = on;
        s.last_record = None;
        hooks::set_mouse_hook(on || s.picking);
        drop(s);
        self.repaint();
    }

    pub fn start_pick(&self) {
        self.lock_cfg().location_mode = "fixed".into();
        let mut s = self.lock_state();
        s.picking = true;
        hooks::set_mouse_hook(true);
        drop(s);
        self.repaint();
    }

    /// `pos` None = cancelled.
    pub fn end_pick(&self, pos: Option<(i32, i32)>) {
        if let Some((x, y)) = pos {
            let mut c = self.lock_cfg();
            c.location_mode = "fixed".into();
            c.fixed_x = x as i64;
            c.fixed_y = y as i64;
        }
        let mut s = self.lock_state();
        s.picking = false;
        hooks::set_mouse_hook(s.recording);
        drop(s);
        self.show_window();
    }

    pub fn start_capture(&self, target: CaptureTarget) {
        let mut s = self.lock_state();
        s.capture = Some(target);
        s.capture_mods.clear();
        s.status = Some((t("press_key_hint").into(), StatusKind::Info));
        drop(s);
        self.repaint();
    }

    pub fn set_status(&self, msg: impl Into<String>, kind: StatusKind) {
        self.lock_state().status = Some((msg.into(), kind));
        self.repaint();
    }

    // ── Window ──────────────────────────────────────────────────

    pub fn hwnd(&self) -> isize {
        self.hwnd.load(Ordering::SeqCst)
    }

    pub fn show_window(&self) {
        let top = self.lock_cfg().always_on_top;
        win::show_window(self.hwnd(), top);
        self.repaint();
    }

    pub fn hide_window(&self) {
        win::hide_window(self.hwnd());
    }

    pub fn toggle_window(&self) {
        if win::is_window_visible(self.hwnd()) { self.hide_window() } else { self.show_window() }
    }

    pub fn toggle_hud(&self) {
        let mut s = self.lock_state();
        s.hud_visible = !s.hud_visible;
        drop(s);
        self.repaint();
    }

    // ── Persistence / exit ──────────────────────────────────────

    /// Saves the session at most twice a second, only when something changed.
    fn autosave(&self) {
        let cfg = self.lock_cfg().clone();
        let mut saved = lock(&self.saved);
        if *saved != cfg {
            self.profiles.save_session(&cfg);
            *saved = cfg;
        }
    }

    pub fn shutdown(&self) {
        lock(&self.clicker).stop();
        lock(&self.runner).stop();
        hooks::set_mouse_hook(false);
        self.profiles.save_session(&self.lock_cfg());
    }

    // ── Input ───────────────────────────────────────────────────

    /// Keys worth polling right now: the hotkeys, Esc/Enter/Space while picking, everything
    /// (minus mouse buttons and left/right modifier duplicates) while capturing a new hotkey.
    fn watched_keys(&self) -> Vec<u32> {
        let (capturing, picking) = {
            let s = self.lock_state();
            (s.capture.is_some(), s.picking)
        };
        if capturing {
            return (0x08..=0xFE).filter(|vk| !(0xA0..=0xA5).contains(vk) && *vk != 0x5C).collect();
        }
        let c = self.lock_cfg();
        let mut keys: Vec<u32> = [&c.hotkey, &c.macro_hotkey].into_iter().filter_map(|h| hotkey::parse(h)).flatten().collect();
        if picking {
            keys.extend([0x1B, 0x0D, 0x20]);
        }
        keys.sort_unstable();
        keys.dedup();
        keys
    }

    /// Turns key-state changes into Key events every 5 ms. A key that just became watched is
    /// read once silently, so a key already held then doesn't fire.
    fn poll_keys(&self, tx: mpsc::Sender<InputEvent>) {
        let mut prev: [Option<bool>; 256] = [None; 256];
        let mut watch = Vec::new();
        for tick in 0u64.. {
            if tick % 10 == 0 {
                watch = self.watched_keys();
                let mut keep = [false; 256];
                watch.iter().for_each(|vk| keep[*vk as usize] = true);
                prev.iter_mut().zip(keep).filter(|(_, k)| !k).for_each(|(p, _)| *p = None);
            }
            for &vk in &watch {
                let down = hooks::key_down(vk);
                if prev[vk as usize].is_some_and(|was| was != down) && tx.send(InputEvent::Key { vk, down }).is_err() {
                    return;
                }
                prev[vk as usize] = Some(down);
            }
            std::thread::sleep(Duration::from_millis(5));
        }
    }

    fn on_input(&self, keys: &mut HotkeyState, ev: InputEvent) {
        match ev {
            InputEvent::Key { vk, down } => {
                if down && self.handle_capture(vk) {
                    return;
                }
                let picking = self.lock_state().picking;
                if picking {
                    if down {
                        match vk {
                            0x1B => self.end_pick(None),
                            0x0D | 0x20 => self.end_pick(Some(cursor_pos())),
                            _ => {}
                        }
                    }
                    return;
                }
                let (click, macro_, hold) = {
                    let c = self.lock_cfg();
                    (hotkey::parse(&c.hotkey), hotkey::parse(&c.macro_hotkey), c.hotkey_mode == "hold")
                };
                for action in keys.on_key(vk, down, click.as_deref(), macro_.as_deref(), hold) {
                    match action {
                        Action::ToggleClick => self.toggle_click(),
                        Action::HoldStart => self.start_click(),
                        Action::HoldStop => self.stop_click(),
                        Action::ToggleMacro => self.toggle_macro(),
                    }
                }
            }
            InputEvent::Mouse { button, down, x, y } => {
                let (picking, recording) = {
                    let s = self.lock_state();
                    (s.picking, s.recording)
                };
                if picking {
                    match (button, down) {
                        (0, false) => self.end_pick(Some((x, y))),
                        (1, false) => self.end_pick(None),
                        _ => {}
                    }
                } else if recording && down {
                    self.record_click(button, x, y);
                }
            }
        }
    }

    /// Returns true when the key was consumed by the Settings "RECORD" capture.
    /// Lock rule used everywhere: never hold `state` and `cfg` at the same time.
    fn handle_capture(&self, vk: u32) -> bool {
        let mut s = self.lock_state();
        let Some(target) = s.capture else { return false };
        if hotkey::is_modifier(vk) {
            s.capture_mods.insert(hotkey::normalize_vk(vk));
            return true;
        }
        s.capture = None;
        let combo = hotkey::combo_string(&s.capture_mods, vk);
        drop(s);
        let status = if vk == 0x1B {
            (t("binding_cancelled").into(), StatusKind::Info)
        } else if hotkey::is_valid(&combo) {
            let mut c = self.lock_cfg();
            match target {
                CaptureTarget::Click => c.hotkey = combo.clone(),
                CaptureTarget::Macro => c.macro_hotkey = combo.clone(),
            }
            (format!("{} [{}]", t("key_set"), hotkey::display(&combo)), StatusKind::Ok)
        } else {
            (format!("{} {combo}", t("invalid_key")), StatusKind::Error)
        };
        self.set_status(status.0, status.1);
        true
    }

    fn record_click(&self, button: u8, x: i32, y: i32) {
        // Clicks on our own window (e.g. the Stop button) are not part of the macro
        if let Some((l, t, r, b)) = win::window_rect(self.hwnd()) {
            if win::is_window_visible(self.hwnd()) && x >= l && x < r && y >= t && y < b {
                return;
            }
        }
        let action = match button {
            1 => "click_right",
            2 => "click_middle",
            _ => "click_left",
        };
        let now = Instant::now();
        let mut s = self.lock_state();
        // Delay runs before the action, so the gap since the previous click belongs to this step
        let delay = match (s.real_delay, s.last_record) {
            (true, Some(prev)) => (now - prev).as_millis().clamp(50, 30_000) as i64,
            _ => 100,
        };
        s.last_record = Some(now);
        drop(s);
        self.lock_cfg().macro_steps.push(MacroStep { action: action.into(), x: x as i64, y: y as i64, delay_ms: delay });
        self.repaint();
    }
}
