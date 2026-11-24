//! Design tokens from design.md / ui/theme.py, fonts, and small widget helpers.
use egui::{Color32, CornerRadius, FontData, FontDefinitions, FontFamily, Frame, Margin, RichText, Stroke};
use std::sync::Arc;

#[derive(Clone, Copy)]
pub struct Palette {
    pub base: Color32,
    pub panel: Color32,
    pub panel_alt: Color32,
    pub hover: Color32,
    pub border: Color32,
    pub text: Color32,
    pub muted: Color32,
    pub dim: Color32,
}

const fn hex(v: u32) -> Color32 {
    Color32::from_rgb((v >> 16) as u8, (v >> 8) as u8, v as u8)
}

pub const DARK: Palette = Palette {
    base: hex(0x0D0F12),
    panel: hex(0x15181E),
    panel_alt: hex(0x1A1E26),
    hover: hex(0x252B36),
    border: hex(0x252B36),
    text: hex(0xF3F4F6),
    muted: hex(0x94A3B8),
    dim: hex(0x64748B),
};

pub const LIGHT: Palette = Palette {
    base: hex(0xF3F4F6),
    panel: hex(0xFFFFFF),
    panel_alt: hex(0xE5E7EB),
    hover: hex(0xD1D5DB),
    border: hex(0xD1D5DB),
    text: hex(0x111827),
    muted: hex(0x4B5563),
    dim: hex(0x6B7280),
};

pub const PRIMARY: Color32 = hex(0x10B981);
pub const PRIMARY_TEXT: Color32 = hex(0x042F2E);
pub const ALERT: Color32 = hex(0xEF4444);
pub const AMBER: Color32 = hex(0xF59E0B);
pub const CYAN: Color32 = hex(0x0EA5E9);
pub const PRIMARY_HOVER: Color32 = hex(0x059669);
pub const ALERT_HOVER: Color32 = hex(0xDC2626);
pub const CYAN_HOVER: Color32 = hex(0x0284C7);
const BORDER_FOCUS: Color32 = hex(0x3B4455);

pub const RADIUS_PANEL: u8 = 8;
pub const RADIUS_CONTROL: u8 = 5;

pub fn palette(theme: &str) -> Palette {
    if theme == "light" { LIGHT } else { DARK }
}

pub fn apply(ctx: &egui::Context, theme: &str) {
    let p = palette(theme);
    let mut v = if theme == "light" { egui::Visuals::light() } else { egui::Visuals::dark() };
    v.panel_fill = p.base;
    v.window_fill = p.panel;
    v.window_stroke = Stroke::new(1.0_f32, p.border);
    v.extreme_bg_color = p.panel_alt; // text edit background
    v.faint_bg_color = p.panel_alt;
    v.override_text_color = Some(p.text);
    v.selection.bg_fill = PRIMARY.gamma_multiply(0.6);
    v.hyperlink_color = CYAN;
    let radius = CornerRadius::same(RADIUS_CONTROL);
    for (w, fill) in [
        (&mut v.widgets.noninteractive, p.panel),
        (&mut v.widgets.inactive, p.panel_alt),
        (&mut v.widgets.hovered, p.hover),
        (&mut v.widgets.active, p.hover),
        (&mut v.widgets.open, p.hover),
    ] {
        w.bg_fill = fill;
        w.weak_bg_fill = fill;
        w.corner_radius = radius;
        w.bg_stroke = Stroke::new(1.0_f32, p.border);
    }
    v.widgets.noninteractive.fg_stroke = Stroke::new(1.0_f32, p.muted);
    // Text color comes from override_text_color, so fg_stroke only tints radio dots, check marks,
    // slider knobs and combo arrows: make those the accent
    v.widgets.inactive.fg_stroke = Stroke::new(1.5_f32, PRIMARY);
    v.widgets.hovered.fg_stroke = Stroke::new(1.5_f32, PRIMARY);
    v.widgets.active.fg_stroke = Stroke::new(2.0_f32, PRIMARY);
    v.widgets.open.fg_stroke = Stroke::new(1.5_f32, PRIMARY);
    v.widgets.hovered.bg_stroke = Stroke::new(1.0_f32, BORDER_FOCUS);
    v.selection.stroke = Stroke::new(1.0_f32, CYAN); // focused text field outline
    v.window_corner_radius = CornerRadius::same(RADIUS_PANEL);
    v.menu_corner_radius = CornerRadius::same(RADIUS_CONTROL);
    ctx.set_visuals(v);
    ctx.style_mut(|s| {
        s.spacing.item_spacing = egui::vec2(6.0, 7.0);
        s.spacing.button_padding = egui::vec2(10.0, 4.0);
        s.spacing.interact_size.y = 26.0;
        s.spacing.icon_width = 16.0;
        s.spacing.icon_spacing = 6.0;
        s.text_styles.insert(egui::TextStyle::Body, egui::FontId::proportional(13.0));
        s.text_styles.insert(egui::TextStyle::Button, egui::FontId::proportional(13.0));
    });
}

/// Segoe UI / Consolas from the system (Vietnamese + design.md fonts), egui's fonts as fallback.
pub fn install_fonts(ctx: &egui::Context) {
    let dir = std::path::PathBuf::from(std::env::var("WINDIR").unwrap_or_else(|_| r"C:\Windows".into())).join("Fonts");
    let mut fonts = FontDefinitions::default();
    let mut load = |name: &str, file: &str| -> bool {
        match std::fs::read(dir.join(file)) {
            Ok(bytes) => {
                fonts.font_data.insert(name.into(), Arc::new(FontData::from_owned(bytes)));
                true
            }
            Err(_) => false,
        }
    };
    let regular = load("segoe", "segoeui.ttf");
    let bold = load("segoe_bold", "segoeuib.ttf");
    let mono = load("consolas_bold", "consolab.ttf");
    let sym = load("segoe_sym", "seguisym.ttf");
    let defaults_prop = fonts.families[&FontFamily::Proportional].clone();
    let defaults_mono = fonts.families[&FontFamily::Monospace].clone();
    let family = |primary: Option<&str>, defaults: &Vec<String>| -> Vec<String> {
        primary.into_iter().map(String::from).chain(sym.then(|| "segoe_sym".to_string())).chain(defaults.iter().cloned()).collect()
    };
    fonts.families.insert(FontFamily::Proportional, family(regular.then_some("segoe"), &defaults_prop));
    fonts.families.insert(FontFamily::Name("bold".into()), family(if bold { Some("segoe_bold") } else { regular.then_some("segoe") }, &defaults_prop));
    fonts.families.insert(FontFamily::Monospace, family(mono.then_some("consolas_bold"), &defaults_mono));
    ctx.set_fonts(fonts);
}

pub fn bold(text: impl Into<String>, size: f32) -> RichText {
    RichText::new(text).family(FontFamily::Name("bold".into())).size(size)
}

pub fn mono(text: impl Into<String>, size: f32) -> RichText {
    RichText::new(text).family(FontFamily::Monospace).size(size)
}

pub fn card(p: &Palette) -> Frame {
    Frame::new()
        .fill(p.panel)
        .stroke(Stroke::new(1.0_f32, p.border))
        .corner_radius(CornerRadius::same(RADIUS_PANEL))
        .inner_margin(Margin::symmetric(12, 10))
}

// Type scale. Use these instead of ad-hoc sizes so every screen reads the same:
//   title    card heading            bold 11, uppercase, muted
//   caption  field/column labels     mono 10, uppercase, dim
//   body     labels, radios, values  regular 13 (TextStyle::Body, plain &str)
//   btn      secondary buttons       bold 11, uppercase
//   bold(..., 14.0)                  primary START/RUN buttons
//   readout  live value in a card    mono 11, cyan
//   data     numbers/keys            mono 12

pub fn title(p: &Palette, text: &str) -> RichText {
    bold(text.to_uppercase(), 11.0).color(p.muted)
}

pub fn caption(p: &Palette, text: &str) -> RichText {
    mono(text.to_uppercase(), 10.0).color(p.dim)
}

pub fn btn(text: &str) -> RichText {
    bold(text.to_uppercase(), 11.0)
}

pub fn readout(text: impl Into<String>) -> RichText {
    mono(text, 11.0).color(CYAN)
}

pub fn data(text: impl Into<String>) -> RichText {
    mono(text, 12.0)
}

/// Filled button with fixed colors (used for START/RUN/STOP and the dock buttons).
pub fn filled(text: RichText, fill: Color32) -> egui::Button<'static> {
    egui::Button::new(text).fill(fill).stroke(Stroke::NONE).corner_radius(CornerRadius::same(RADIUS_CONTROL))
}

/// Big painted button (START / RUN / STOP / tabs) with hover and press feedback, label centered.
pub fn action_button(ui: &mut egui::Ui, text: RichText, fill: Color32, hover: Color32, size: egui::Vec2) -> egui::Response {
    let (rect, resp) = ui.allocate_exact_size(size, egui::Sense::click());
    let color = if !ui.is_enabled() {
        fill.gamma_multiply(0.35)
    } else if resp.is_pointer_button_down_on() {
        hover.gamma_multiply(0.85)
    } else if resp.hovered() {
        hover
    } else {
        fill
    };
    ui.painter().rect_filled(rect, CornerRadius::same(RADIUS_CONTROL), color);
    let galley = egui::WidgetText::from(text).into_galley(ui, Some(egui::TextWrapMode::Extend), f32::INFINITY, egui::TextStyle::Button);
    ui.painter().galley(rect.center() - galley.size() / 2.0, galley, Color32::WHITE);
    if resp.hovered() && ui.is_enabled() {
        ui.ctx().set_cursor_icon(egui::CursorIcon::PointingHand);
    }
    resp
}

/// Fixed-width slot so columns line up across rows (macro list, settings labels).
/// `align` is the horizontal placement of the content inside the slot.
pub fn cell<R>(ui: &mut egui::Ui, width: f32, align: egui::Align, add: impl FnOnce(&mut egui::Ui) -> R) -> R {
    let layout = if align == egui::Align::Min {
        egui::Layout::left_to_right(egui::Align::Center)
    } else {
        egui::Layout::centered_and_justified(egui::Direction::LeftToRight)
    };
    ui.allocate_ui_with_layout(egui::vec2(width, ui.spacing().interact_size.y), layout, |ui| {
        ui.set_min_width(width);
        add(ui)
    })
    .inner
}
