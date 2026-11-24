//! System tray icon and menu. Handlers run on the UI thread's message loop, which keeps
//! pumping while the window is hidden, and call straight into the controller.
use crate::core::Core;
use crate::i18n::t;
use std::sync::Arc;
use tray_icon::menu::{Menu, MenuEvent, MenuItem, PredefinedMenuItem};
use tray_icon::{Icon, MouseButton, MouseButtonState, TrayIcon, TrayIconBuilder, TrayIconEvent};

pub struct Tray {
    _icon: TrayIcon,
    items: Vec<(MenuItem, &'static str)>,
}

pub fn icon_rgba(size: u32) -> Option<(Vec<u8>, u32, u32)> {
    let img = image::load_from_memory(include_bytes!("../assets/icon.png")).ok()?.thumbnail(size, size).to_rgba8();
    let (w, h) = img.dimensions();
    Some((img.into_raw(), w, h))
}

impl Tray {
    pub fn new(core: Arc<Core>) -> Option<Self> {
        let keys = [("show", "show_hide"), ("click", "tray_toggle_click"), ("macro", "tray_toggle_macro"), ("hud", "mini_hud"), ("exit", "exit")];
        let items: Vec<(MenuItem, &'static str)> = keys.iter().map(|(id, key)| (MenuItem::with_id(*id, t(key), true, None), *key)).collect();
        let menu = Menu::new();
        for (i, (item, _)) in items.iter().enumerate() {
            if i == items.len() - 1 {
                menu.append(&PredefinedMenuItem::separator()).ok()?;
            }
            menu.append(item).ok()?;
        }
        let (rgba, w, h) = icon_rgba(64)?;
        let icon = TrayIconBuilder::new()
            .with_menu(Box::new(menu))
            .with_menu_on_left_click(false)
            .with_tooltip("AutoClicker")
            .with_icon(Icon::from_rgba(rgba, w, h).ok()?)
            .build()
            .map_err(|e| crate::log!("System tray initialization failed: {e}"))
            .ok()?;

        let c = core.clone();
        MenuEvent::set_event_handler(Some(move |e: MenuEvent| match e.id.0.as_str() {
            "show" => c.toggle_window(),
            "click" => c.toggle_click(),
            "macro" => c.toggle_macro(),
            "hud" => c.toggle_hud(),
            "exit" => {
                c.shutdown();
                std::process::exit(0);
            }
            _ => {}
        }));
        TrayIconEvent::set_event_handler(Some(move |e: TrayIconEvent| {
            if let TrayIconEvent::Click { button: MouseButton::Left, button_state: MouseButtonState::Up, .. } = e {
                core.toggle_window();
            }
        }));
        Some(Self { _icon: icon, items })
    }

    pub fn update_texts(&self) {
        for (item, key) in &self.items {
            item.set_text(t(key));
        }
    }
}
