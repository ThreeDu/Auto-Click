"""
AutoClicker — Main Application Window
Compact & Sleek Utilitarian Redesign.
Zero-scroll Auto-Click deck, side-by-side modular controls, high-density hardware HUD.
"""

import os
import sys
import time
import customtkinter as ctk
from typing import Optional

from config import ClickerConfig
from profile_manager import ProfileManager
from core.clicker_engine import ClickerEngine
from core.macro_engine import MacroEngine, MacroStep
from core.hotkey_manager import HotkeyManager, normalize_hotkey, is_valid_hotkey
from core.win32_input import get_cursor_pos
from i18n.localization import t, set_language, get_language, get_available_languages
from ui.theme import (
    BG_BASE, BG_PANEL, BG_PANEL_ALT, BG_HOVER, BORDER_SUBTLE,
    TEXT_MAIN, TEXT_MUTED, TEXT_DIM, ACCENT_PRIMARY, ACCENT_PRIMARY_HOVER,
    ACCENT_ALERT, ACCENT_ALERT_HOVER, ACCENT_AMBER, ACCENT_CYAN,
    FONT_FAMILY, FONT_MONO, FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_MD, FONT_SIZE_LG,
    RADIUS_PANEL, RADIUS_CONTROL,
    apply_theme_patches
)


class LocationPickerBanner(ctk.CTkToplevel):
    """Floating HUD banner showing instructions while picking screen coordinates."""

    def __init__(self, master, cancel_callback):
        super().__init__(master)
        self.cancel_callback = cancel_callback

        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.96)

        try:
            screen_w = self.winfo_screenwidth()
            banner_w = 460
            x = max(10, (screen_w - banner_w) // 2)
            self.geometry(f"{banner_w}x40+{x}+24")
        except Exception:
            self.geometry("460x40+200+24")

        container = ctk.CTkFrame(
            self,
            fg_color=BG_PANEL,
            border_color=ACCENT_CYAN,
            border_width=1,
            corner_radius=RADIUS_CONTROL
        )
        container.pack(fill="both", expand=True)

        msg = (
            "🎯 CLICK CHUỘT TRÁI để chọn vị trí  ·  [Esc] để hủy"
            if get_language() == "vi" else
            "🎯 LEFT-CLICK to pick location  ·  [Esc] to cancel"
        )
        lbl = ctk.CTkLabel(
            container,
            text=msg,
            font=(FONT_FAMILY, 11, "bold"),
            text_color=TEXT_MAIN
        )
        lbl.pack(side="left", padx=14, pady=6)

        btn_cancel = ctk.CTkButton(
            container,
            text="✕",
            width=26,
            height=24,
            font=(FONT_FAMILY, 11, "bold"),
            fg_color="transparent",
            hover_color=ACCENT_ALERT,
            text_color=TEXT_MUTED,
            corner_radius=RADIUS_CONTROL,
            command=self.cancel_callback
        )
        btn_cancel.pack(side="right", padx=(0, 8), pady=6)


class AutoClickerApp(ctk.CTk):
    """Main application window for AutoClicker."""

    def __init__(self, config: ClickerConfig, profile_manager: ProfileManager):
        super().__init__()

        self.config = config
        self.profile_manager = profile_manager

        # Core engines
        self.clicker_engine = ClickerEngine()
        self.macro_engine = MacroEngine()
        self.hotkey_manager = HotkeyManager()

        # State
        self._mini_hud: Optional[object] = None
        self._tray_manager: Optional[object] = None
        self._cps_start_time: float = 0
        self._last_click_count: int = 0
        self._is_recording_macro: bool = False
        self._recording_listener = None
        self._hk_listener = None
        self._current_profile_name: str = "default"
        self._picker_banner = None
        self._pick_mouse_listener = None
        self._pick_kb_listener = None

        # Window setup
        self._setup_window()
        self._setup_theme()
        self._build_ui()
        self._setup_engines()
        self._setup_hotkeys()
        self._setup_tray()
        self._load_config_to_ui()
        self._start_status_updater()

    # ─── Window Setup ──────────────────────────────────────────

    def _setup_window(self):
        """Configure comfortable window dimensions with locked utilitarian aspect."""
        self.title("AutoClicker")
        self.geometry("500x620")
        self.minsize(480, 600)
        self.resizable(False, False)
        self.configure(fg_color=BG_BASE)

        if self.config.always_on_top:
            self.attributes("-topmost", True)

        # Set app window and taskbar icon
        from main import get_app_dir, get_bundle_dir
        icon_candidates = [
            os.path.join(get_bundle_dir(), 'assets', 'icon.ico'),
            os.path.join(get_app_dir(), 'assets', 'icon.ico'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'icon.ico'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'icon.ico'),
            os.path.join(os.getcwd(), 'assets', 'icon.ico'),
        ]
        for icon_path in icon_candidates:
            if os.path.exists(icon_path):
                try:
                    self.iconbitmap(icon_path)
                    break
                except Exception:
                    pass

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_theme(self):
        ctk.set_appearance_mode(self.config.theme)
        apply_theme_patches()

    # ─── Build UI ──────────────────────────────────────────────

    def _build_ui(self):
        if hasattr(self, 'content_frame') and self.content_frame:
            try:
                self.content_frame.destroy()
            except Exception:
                pass

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)

        # 1. Top Instrument Status Strip
        self._build_status_bar(self.content_frame)

        # 2. Segmented Navigation Tab View
        self.tabview = ctk.CTkTabview(
            self.content_frame,
            corner_radius=RADIUS_PANEL,
            fg_color=BG_BASE,
            segmented_button_fg_color=BG_PANEL_ALT,
            segmented_button_selected_color=BG_HOVER,
            segmented_button_selected_hover_color="#2A303C",
            segmented_button_unselected_color=BG_PANEL_ALT,
            segmented_button_unselected_hover_color=BG_HOVER,
            segmented_button_font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            text_color=TEXT_MAIN
        )
        self.tabview.pack(fill="both", expand=True, padx=8, pady=(2, 4))

        tab_auto = self.tabview.add("AUTO CLICK")
        self._build_auto_click_tab(tab_auto)

        tab_macro = self.tabview.add("MACRO")
        self._build_macro_tab(tab_macro)

        tab_settings = self.tabview.add("SETTINGS")
        self._build_settings_tab(tab_settings)

        def _sync_restore_from_location():
            val = self.location_card.is_restore_cursor()
            self.macro_card.set_restore_cursor(val)

        def _sync_restore_from_macro():
            val = self.macro_card.is_restore_cursor()
            self.location_card.set_restore_cursor(val)

        self.location_card.restore_cursor_cb.configure(command=_sync_restore_from_location)
        self.macro_card.restore_cursor_cb.configure(command=_sync_restore_from_macro)

        # 3. Bottom Unified Control Dock
        self._build_bottom_bar(self.content_frame)

    def _build_status_bar(self, parent=None):
        """Compact status instrument strip."""
        p = parent if parent is not None else self
        self.status_frame = ctk.CTkFrame(
            p,
            corner_radius=RADIUS_PANEL,
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER_SUBTLE,
            height=34
        )
        self.status_frame.pack(fill="x", padx=8, pady=(8, 2))
        self.status_frame.grid_columnconfigure(1, weight=1)

        # Status
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="● STANDBY",
            font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            text_color=TEXT_MUTED
        )
        self.status_label.grid(row=0, column=0, padx=(10, 8), pady=6, sticky="w")

        # Clicks
        self.click_count_label = ctk.CTkLabel(
            self.status_frame,
            text="CLICKS: 0",
            font=(FONT_MONO, FONT_SIZE_MD, "bold"),
            text_color=TEXT_MAIN
        )
        self.click_count_label.grid(row=0, column=1, padx=6, pady=6)

        # CPS
        self.cps_label = ctk.CTkLabel(
            self.status_frame,
            text="CPS: 0.0",
            font=(FONT_MONO, FONT_SIZE_MD, "bold"),
            text_color=ACCENT_CYAN
        )
        self.cps_label.grid(row=0, column=2, padx=8, pady=6)

        # Hotkey Badge
        self.hotkey_label = ctk.CTkLabel(
            self.status_frame,
            text=f"[{self.config.hotkey.upper().strip('<>')}]",
            font=(FONT_MONO, FONT_SIZE_SM, "bold"),
            text_color=ACCENT_AMBER
        )
        self.hotkey_label.grid(row=0, column=3, padx=(4, 10), pady=6, sticky="e")

    def _build_auto_click_tab(self, parent):
        """Build Auto Click tab with NO SCROLLBAR — all cards stacked cleanly at full width."""
        from ui.components.interval_card import IntervalCard
        from ui.components.options_card import OptionsCard
        from ui.components.location_card import LocationCard
        from ui.components.repeat_card import RepeatCard

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=2, pady=2)

        # Row 1: Interval (full width)
        self.interval_card = IntervalCard(container)
        self.interval_card.pack(fill="x", pady=(0, 4))

        # Row 2: Options (full width)
        self.options_card = OptionsCard(container)
        self.options_card.pack(fill="x", pady=(0, 4))
        self.options_card.on_mode_changed = self._on_hotkey_mode_changed

        # Row 3: Location (full width)
        self.location_card = LocationCard(container)
        self.location_card.pack(fill="x", pady=(0, 4))
        self.location_card.on_pick_location = self._handle_pick_location

        # Row 4: Repeat & Anti-Bot Jitter (full width)
        self.repeat_card = RepeatCard(container)
        self.repeat_card.pack(fill="x", pady=(0, 6))

        # Row 5: Primary Trigger Button
        self.start_button = ctk.CTkButton(
            container,
            text=f"▶  {t('start_clicking').upper()} ({self.config.hotkey.upper().strip('<>')})",
            font=(FONT_FAMILY, 14, "bold"),
            height=42,
            corner_radius=RADIUS_CONTROL,
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_PRIMARY_HOVER,
            text_color="#042F2E",
            command=self._toggle_clicking
        )
        self.start_button.pack(fill="x", pady=(0, 2))

    def _build_macro_tab(self, parent):
        """Build macro sequence tab."""
        from ui.components.macro_card import MacroCard

        self.macro_card = MacroCard(parent)
        self.macro_card.pack(fill="both", expand=True, padx=2, pady=2)
        self.macro_card.set_hotkey(self.config.macro_hotkey)
        self.macro_card.on_run_macro = self._start_macro
        self.macro_card.on_stop_macro = self._stop_macro
        self.macro_card.on_record_start = self._start_recording
        self.macro_card.on_record_stop = self._stop_recording
        self.macro_card.on_steps_changed = self._save_current_session

    def _build_settings_tab(self, parent):
        """Compact settings tab with legible typography."""
        settings_frame = ctk.CTkFrame(parent, fg_color="transparent")
        settings_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # Regional & Theme
        pref_card = ctk.CTkFrame(
            settings_frame,
            corner_radius=RADIUS_PANEL,
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        pref_card.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            pref_card,
            text="PREFERENCES",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=10, pady=(8, 6))

        row1 = ctk.CTkFrame(pref_card, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkLabel(row1, text=t('language'), font=(FONT_FAMILY, 12), text_color=TEXT_MAIN).pack(side="left")

        langs = get_available_languages()
        lang_names = [name for _, name in langs]
        current_lang_name = dict(langs).get(get_language(), "English")

        self.lang_menu = ctk.CTkOptionMenu(
            row1, values=lang_names, height=26, font=(FONT_FAMILY, 11, "bold"),
            fg_color=BG_PANEL_ALT, button_color=BORDER_SUBTLE, button_hover_color=BG_HOVER,
            text_color=TEXT_MAIN, dropdown_fg_color=BG_PANEL, dropdown_hover_color=BG_HOVER,
            dropdown_text_color=TEXT_MAIN, dropdown_font=(FONT_FAMILY, 11),
            corner_radius=RADIUS_CONTROL, command=self._on_language_changed
        )
        self.lang_menu.set(current_lang_name)
        self.lang_menu.pack(side="right")

        row2 = ctk.CTkFrame(pref_card, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkLabel(row2, text=t('theme'), font=(FONT_FAMILY, 12), text_color=TEXT_MAIN).pack(side="left")

        self.theme_menu = ctk.CTkOptionMenu(
            row2, values=[t("dark"), t("light")], height=26, font=(FONT_FAMILY, 11, "bold"),
            fg_color=BG_PANEL_ALT, button_color=BORDER_SUBTLE, button_hover_color=BG_HOVER,
            text_color=TEXT_MAIN, dropdown_fg_color=BG_PANEL, dropdown_hover_color=BG_HOVER,
            dropdown_text_color=TEXT_MAIN, dropdown_font=(FONT_FAMILY, 11),
            corner_radius=RADIUS_CONTROL, command=self._on_theme_changed
        )
        current_theme_name = t("dark") if self.config.theme == "dark" else t("light")
        self.theme_menu.set(current_theme_name)
        self.theme_menu.pack(side="right")

        # Hotkeys
        hk_card = ctk.CTkFrame(
            settings_frame,
            corner_radius=RADIUS_PANEL,
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        hk_card.pack(fill="x")

        ctk.CTkLabel(
            hk_card,
            text="HOTKEYS",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=10, pady=(8, 6))

        # Auto Click Key row
        hk1 = ctk.CTkFrame(hk_card, fg_color="transparent")
        hk1.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkLabel(hk1, text="Auto Click Key:", font=(FONT_FAMILY, 12), text_color=TEXT_MAIN).pack(side="left")

        hk1_right = ctk.CTkFrame(hk1, fg_color="transparent")
        hk1_right.pack(side="right")

        self.hotkey_entry = ctk.CTkEntry(
            hk1_right, width=76, height=28, font=(FONT_MONO, 11, "bold"),
            fg_color=BG_PANEL_ALT, border_color=BORDER_SUBTLE, border_width=1,
            corner_radius=RADIUS_CONTROL, text_color=ACCENT_AMBER, justify="center"
        )
        self.hotkey_entry.insert(0, self.config.hotkey.upper().strip('<>'))
        self.hotkey_entry.configure(state="readonly")
        self.hotkey_entry.pack(side="left", padx=(0, 4))

        self.bind_click_btn = ctk.CTkButton(
            hk1_right, text="RECORD", width=68, height=28, font=(FONT_FAMILY, 10, "bold"),
            fg_color=BG_PANEL_ALT, hover_color=BG_HOVER, text_color=TEXT_MAIN,
            border_color=BORDER_SUBTLE, border_width=1, corner_radius=RADIUS_CONTROL,
            command=lambda: self._start_listening_for_hotkey("click")
        )
        self.bind_click_btn.pack(side="left")

        # Macro Key row
        hk2 = ctk.CTkFrame(hk_card, fg_color="transparent")
        hk2.pack(fill="x", padx=10, pady=(0, 4))
        ctk.CTkLabel(hk2, text="Macro Key:", font=(FONT_FAMILY, 12), text_color=TEXT_MAIN).pack(side="left")

        hk2_right = ctk.CTkFrame(hk2, fg_color="transparent")
        hk2_right.pack(side="right")

        self.macro_hotkey_entry = ctk.CTkEntry(
            hk2_right, width=76, height=28, font=(FONT_MONO, 11, "bold"),
            fg_color=BG_PANEL_ALT, border_color=BORDER_SUBTLE, border_width=1,
            corner_radius=RADIUS_CONTROL, text_color=ACCENT_AMBER, justify="center"
        )
        self.macro_hotkey_entry.insert(0, self.config.macro_hotkey.upper().strip('<>'))
        self.macro_hotkey_entry.configure(state="readonly")
        self.macro_hotkey_entry.pack(side="left", padx=(0, 4))

        self.bind_macro_btn = ctk.CTkButton(
            hk2_right, text="RECORD", width=68, height=28, font=(FONT_FAMILY, 10, "bold"),
            fg_color=BG_PANEL_ALT, hover_color=BG_HOVER, text_color=TEXT_MAIN,
            border_color=BORDER_SUBTLE, border_width=1, corner_radius=RADIUS_CONTROL,
            command=lambda: self._start_listening_for_hotkey("macro")
        )
        self.bind_macro_btn.pack(side="left")

        # Status / Feedback label
        self.hk_status_label = ctk.CTkLabel(
            hk_card,
            text="",
            font=(FONT_FAMILY, 10),
            text_color=TEXT_MUTED
        )
        self.hk_status_label.pack(fill="x", padx=10, pady=(2, 4))

        btn_row = ctk.CTkFrame(hk_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 8))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        self.reset_hk_btn = ctk.CTkButton(
            btn_row, text=t('reset_hotkeys').upper(), height=28, font=(FONT_FAMILY, 10, "bold"),
            fg_color="transparent", hover_color=BG_HOVER, text_color=TEXT_MUTED,
            border_color=BORDER_SUBTLE, border_width=1, corner_radius=RADIUS_CONTROL,
            command=self._reset_default_hotkeys
        )
        self.reset_hk_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        apply_btn = ctk.CTkButton(
            btn_row, text="APPLY KEYBINDS", height=28, font=(FONT_FAMILY, 11, "bold"),
            fg_color=BG_PANEL_ALT, hover_color=BG_HOVER, text_color=TEXT_MAIN,
            border_color=BORDER_SUBTLE, border_width=1, corner_radius=RADIUS_CONTROL,
            command=self._apply_hotkey_settings
        )
        apply_btn.grid(row=0, column=1, padx=(4, 0), sticky="ew")

    def _build_bottom_bar(self, parent=None):
        """Unified compact bottom toolbar (profile + quick toggles in 1 strip)."""
        from ui.components.profile_card import ProfileCard

        p = parent if parent is not None else self
        dock_strip = ctk.CTkFrame(
            p,
            corner_radius=RADIUS_PANEL,
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER_SUBTLE,
            height=34
        )
        dock_strip.pack(fill="x", padx=8, pady=(0, 8))

        # Profile dock (Left)
        self.profile_card = ProfileCard(dock_strip, fg_color="transparent", border_width=0)
        self.profile_card.pack(side="left", padx=2, pady=2)
        self.profile_card.on_save = self._save_profile
        self.profile_card.on_save_as = self._save_profile_as
        self.profile_card.on_load = self._load_profile
        self.profile_card.on_delete = self._delete_profile

        profiles = self.profile_manager.list_profiles()
        if not profiles:
            profiles = ["default"]
        self.profile_card.set_profiles(profiles, self._current_profile_name)

        # Quick Utility Buttons (Right)
        self.aot_var = ctk.BooleanVar(value=self.config.always_on_top)

        self.tray_btn = ctk.CTkButton(
            dock_strip, text="TRAY", width=48, height=26, font=(FONT_FAMILY, 10, "bold"),
            fg_color=BG_PANEL_ALT, hover_color=BG_HOVER, text_color=TEXT_DIM,
            border_color=BORDER_SUBTLE, border_width=1, corner_radius=RADIUS_CONTROL,
            command=self._minimize_to_tray
        )
        self.tray_btn.pack(side="right", padx=(2, 6), pady=4)

        self.hud_btn = ctk.CTkButton(
            dock_strip, text="HUD", width=48, height=26, font=(FONT_FAMILY, 10, "bold"),
            fg_color=BG_PANEL_ALT, hover_color=BG_HOVER, text_color=TEXT_MAIN,
            border_color=BORDER_SUBTLE, border_width=1, corner_radius=RADIUS_CONTROL,
            command=self._toggle_mini_hud
        )
        self.hud_btn.pack(side="right", padx=2, pady=4)

        self.aot_btn = ctk.CTkButton(
            dock_strip, text="PIN", width=46, height=26, font=(FONT_FAMILY, 10, "bold"),
            fg_color=BG_HOVER if self.config.always_on_top else BG_PANEL_ALT,
            hover_color=BG_HOVER,
            text_color=ACCENT_CYAN if self.config.always_on_top else TEXT_MAIN,
            border_color=BORDER_SUBTLE, border_width=1, corner_radius=RADIUS_CONTROL,
            command=self._toggle_always_on_top
        )
        self.aot_btn.pack(side="right", padx=2, pady=4)

    # ─── Engine Setup ──────────────────────────────────────────

    def _setup_engines(self):
        self.clicker_engine.on_click_update = self._on_click_update
        self.clicker_engine.on_stopped = self._on_engine_stopped
        self.macro_engine.on_step_update = self._on_macro_step_update
        self.macro_engine.on_stopped = self._on_macro_stopped

    def _setup_hotkeys(self):
        self.hotkey_manager.hotkey = self.config.hotkey
        self.hotkey_manager.macro_hotkey = self.config.macro_hotkey
        self.hotkey_manager.mode = self.config.hotkey_mode
        self.hotkey_manager.on_toggle = lambda: self.after(0, self._toggle_clicking)
        self.hotkey_manager.on_macro_toggle = lambda: self.after(0, self._toggle_macro)
        self.hotkey_manager.on_hold_start = lambda: self.after(0, self._start_clicking)
        self.hotkey_manager.on_hold_stop = lambda: self.after(0, self._stop_clicking)
        self.hotkey_manager.start()

    def _setup_tray(self):
        try:
            from ui.tray import TrayManager
            self._tray_manager = TrayManager(self)
            self._tray_manager.on_toggle_click = lambda: self.after(0, self._toggle_clicking)
            self._tray_manager.on_toggle_hud = lambda: self.after(0, self._toggle_mini_hud)
            self._tray_manager.start()
        except Exception as e:
            print(f"System tray initialization failed: {e}")

    # ─── Config ↔ UI ──────────────────────────────────────────

    def _load_config_to_ui(self):
        self._is_loading_config = True
        try:
            c = self.config
            self.interval_card.set_values(
                c.interval_hours, c.interval_minutes,
                c.interval_seconds, c.interval_ms
            )
            self.options_card.set_values(c.mouse_button, c.click_type, c.hotkey_mode)
            self.location_card.set_values(c.location_mode, c.fixed_x, c.fixed_y, c.restore_cursor)
            self.repeat_card.set_values(
                c.repeat_mode, c.repeat_count,
                c.jitter_enabled, c.jitter_interval_pct, c.jitter_position_px
            )
            self.macro_card.set_restore_cursor(c.restore_cursor)
            self.macro_card.set_hotkey(c.macro_hotkey)
            self.macro_card.set_repeat(c.macro_repeat_mode, c.macro_repeat_count)
            self.macro_card.set_steps(c.macro_steps if c.macro_steps else [])
            if hasattr(self, 'hotkey_entry') and self.hotkey_entry:
                self.hotkey_entry.configure(state="normal")
                self.hotkey_entry.delete(0, 'end')
                self.hotkey_entry.insert(0, c.hotkey.upper().strip('<>'))
                self.hotkey_entry.configure(state="readonly")
            if hasattr(self, 'macro_hotkey_entry') and self.macro_hotkey_entry:
                self.macro_hotkey_entry.configure(state="normal")
                self.macro_hotkey_entry.delete(0, 'end')
                self.macro_hotkey_entry.insert(0, c.macro_hotkey.upper().strip('<>'))
                self.macro_hotkey_entry.configure(state="readonly")
            if hasattr(self, 'hotkey_label') and self.hotkey_label:
                self.hotkey_label.configure(text=f"[{c.hotkey.upper().strip('<>')}]")
            if hasattr(self, 'start_button') and self.start_button:
                self.start_button.configure(text=f"▶  {t('start_clicking').upper()} ({c.hotkey.upper().strip('<>')})")
        finally:
            self._is_loading_config = False

    def _collect_config_from_ui(self) -> ClickerConfig:
        hrs, mins, secs, ms = self.interval_card.get_values()
        button = self.options_card.get_button()
        click_type = self.options_card.get_click_type()
        mode = self.options_card.get_mode()
        loc_mode = self.location_card.get_mode()
        fx, fy = self.location_card.get_fixed_pos()
        rep_mode = self.repeat_card.get_repeat_mode()
        rep_count = self.repeat_card.get_repeat_count()
        jitter_on = self.repeat_card.is_jitter_enabled()
        jitter_int, jitter_pos = self.repeat_card.get_jitter_values()
        restore_cursor = self.location_card.is_restore_cursor() or self.macro_card.is_restore_cursor()

        return ClickerConfig(
            interval_hours=hrs,
            interval_minutes=mins,
            interval_seconds=secs,
            interval_ms=ms,
            mouse_button=button,
            click_type=click_type,
            hotkey=self.config.hotkey,
            macro_hotkey=self.config.macro_hotkey,
            hotkey_mode=mode,
            location_mode=loc_mode,
            fixed_x=fx,
            fixed_y=fy,
            repeat_mode=rep_mode,
            repeat_count=rep_count,
            jitter_enabled=jitter_on,
            jitter_interval_pct=jitter_int,
            jitter_position_px=jitter_pos,
            always_on_top=self.aot_var.get(),
            language=get_language(),
            theme=self.config.theme,
            macro_steps=self.macro_card.get_steps(),
            macro_repeat_mode=self.macro_card.get_repeat_mode(),
            macro_repeat_count=self.macro_card.get_repeat_count(),
            restore_cursor=restore_cursor,
        )

    def _apply_config_to_engine(self):
        config = self._collect_config_from_ui()
        self.clicker_engine.interval_ms = max(1, config.get_total_interval_ms())
        self.clicker_engine.button = config.mouse_button
        self.clicker_engine.click_type = config.click_type
        self.clicker_engine.jitter_enabled = config.jitter_enabled
        self.clicker_engine.jitter_interval_pct = max(0, config.jitter_interval_pct) / 100.0
        self.clicker_engine.jitter_position_px = max(0, config.jitter_position_px)
        self.clicker_engine.restore_cursor = config.restore_cursor
        self.macro_engine.restore_cursor = config.restore_cursor

        if config.location_mode == 'fixed':
            self.clicker_engine.fixed_position = (config.fixed_x, config.fixed_y)
        else:
            self.clicker_engine.fixed_position = None

        if config.repeat_mode == 'count':
            self.clicker_engine.repeat_count = max(1, config.repeat_count)
        else:
            self.clicker_engine.repeat_count = 0

    # ─── Click Control ─────────────────────────────────────────

    def _toggle_clicking(self):
        try:
            if self.clicker_engine.is_running:
                self._stop_clicking()
            else:
                self._start_clicking()
        except Exception as e:
            print(f"Toggle clicking error: {e}")

    def _start_clicking(self):
        try:
            if self.clicker_engine.is_running:
                return

            self._apply_config_to_engine()
            self._cps_start_time = time.time()
            self._last_click_count = 0
            self.clicker_engine.start()

            self._update_ui_running(True)
        except Exception as e:
            print(f"Start clicking error: {e}")
            self._update_ui_running(False)

    def _stop_clicking(self):
        try:
            self.clicker_engine.stop()
            self._update_ui_running(False)
        except Exception as e:
            print(f"Stop clicking error: {e}")

    def _update_ui_running(self, is_running: bool):
        try:
            hk_display = self.config.hotkey.upper().strip('<>')
            if is_running:
                self.status_label.configure(
                    text="● ACTIVE", text_color=ACCENT_PRIMARY
                )
                self.start_button.configure(
                    text=f"■  {t('stop_clicking').upper()} ({hk_display})",
                    fg_color=ACCENT_ALERT,
                    hover_color=ACCENT_ALERT_HOVER,
                    text_color="#FFFFFF"
                )
            else:
                self.status_label.configure(
                    text="● STANDBY", text_color=TEXT_MUTED
                )
                self.start_button.configure(
                    text=f"▶  {t('start_clicking').upper()} ({hk_display})",
                    fg_color=ACCENT_PRIMARY,
                    hover_color=ACCENT_PRIMARY_HOVER,
                    text_color="#042F2E"
                )
                self.cps_label.configure(text="CPS: 0.0")

            if self._mini_hud and self._mini_hud.winfo_exists():
                cps = self._calculate_cps() if is_running else 0
                self._mini_hud.update_status(
                    is_running, cps, self.clicker_engine.click_count
                )
        except Exception:
            pass

    # ─── Macro Control ─────────────────────────────────────────

    def _toggle_macro(self):
        if self.macro_engine.is_running:
            self._stop_macro()
        else:
            self._start_macro()

    def _start_macro(self):
        if self.macro_engine.is_running:
            return

        steps_data = self.macro_card.get_steps()
        if not steps_data:
            return

        self.macro_engine.steps = [
            MacroStep(
                action=s.get('action', 'click_left'),
                x=int(s.get('x', 0)),
                y=int(s.get('y', 0)),
                delay_ms=int(s.get('delay_ms', 100))
            )
            for s in steps_data
        ]

        rep_mode = self.macro_card.get_repeat_mode()
        if rep_mode == 'count':
            self.macro_engine.repeat_count = self.macro_card.get_repeat_count()
        else:
            self.macro_engine.repeat_count = 0

        self.macro_engine.restore_cursor = self.macro_card.is_restore_cursor()

        self.macro_engine.start()
        self.macro_card.set_running(True)

    def _stop_macro(self):
        self.macro_engine.stop()
        self.macro_card.set_running(False)

    def _is_point_in_window(self, x: int, y: int) -> bool:
        try:
            wx = self.winfo_rootx()
            wy = self.winfo_rooty()
            ww = self.winfo_width()
            wh = self.winfo_height()
            return (wx <= x <= wx + ww) and (wy <= y <= wy + wh)
        except Exception:
            return False

    def _start_recording(self):
        self._is_recording_macro = True
        self._last_record_time = None
        try:
            from pynput import mouse

            def on_click(x, y, button, pressed):
                if not self._is_recording_macro:
                    return False
                if pressed:
                    # Ignore clicks inside AutoClicker app itself (e.g. clicking STOP button)
                    if self._is_point_in_window(int(x), int(y)):
                        return

                    now = time.time()
                    if self._last_record_time is not None:
                        elapsed_ms = max(50, min(30000, int((now - self._last_record_time) * 1000)))
                        self.after(0, lambda d=elapsed_ms: self.macro_card.update_last_step_delay(d))
                    self._last_record_time = now

                    button_map = {
                        mouse.Button.left: 'click_left',
                        mouse.Button.right: 'click_right',
                        mouse.Button.middle: 'click_middle',
                    }
                    action = button_map.get(button, 'click_left')
                    self.after(0, lambda: self.macro_card.add_step(
                        action, int(x), int(y), 100
                    ))

            self._recording_listener = mouse.Listener(on_click=on_click)
            self._recording_listener.start()
        except Exception as e:
            print(f"Recording failed: {e}")
            self._is_recording_macro = False

    def _stop_recording(self):
        self._is_recording_macro = False
        self._last_record_time = None
        if self._recording_listener:
            self._recording_listener.stop()
            self._recording_listener = None
        self._save_current_session()

    # ─── Pick Location ─────────────────────────────────────────

    def _handle_pick_location(self):
        self.withdraw()
        self.after(150, self._start_location_picker)

    def _start_location_picker(self):
        try:
            from pynput import mouse, keyboard as kb

            self._picker_banner = LocationPickerBanner(self, self._cancel_pick_location)

            def on_click(x, y, button, pressed):
                if not pressed:
                    if button == mouse.Button.left:
                        self.after(0, lambda: self._finish_pick_location(int(x), int(y)))
                        return False
                    elif button == mouse.Button.right:
                        self.after(0, self._cancel_pick_location)
                        return False

            def on_press(key):
                if key in (kb.Key.space, kb.Key.enter):
                    cur_x, cur_y = get_cursor_pos()
                    self.after(0, lambda: self._finish_pick_location(cur_x, cur_y))
                    return False
                elif key == kb.Key.esc:
                    self.after(0, self._cancel_pick_location)
                    return False

            self._pick_mouse_listener = mouse.Listener(on_click=on_click)
            self._pick_mouse_listener.start()

            self._pick_kb_listener = kb.Listener(on_press=on_press)
            self._pick_kb_listener.start()
        except Exception as e:
            print(f"Pick location failed: {e}")
            self._cancel_pick_location()

    def _cleanup_picker(self):
        if self._picker_banner and self._picker_banner.winfo_exists():
            try:
                self._picker_banner.destroy()
            except Exception:
                pass
        self._picker_banner = None

        if self._pick_mouse_listener:
            try:
                self._pick_mouse_listener.stop()
            except Exception:
                pass
            self._pick_mouse_listener = None

        if self._pick_kb_listener:
            try:
                self._pick_kb_listener.stop()
            except Exception:
                pass
            self._pick_kb_listener = None

    def _finish_pick_location(self, x: int, y: int):
        self._cleanup_picker()
        self.location_card.set_values('fixed', x, y)
        self.restore_window()

    def _cancel_pick_location(self):
        self._cleanup_picker()
        self.restore_window()

    # ─── Callbacks ─────────────────────────────────────────────

    def _on_click_update(self, count: int):
        try:
            self.after(0, lambda: self._update_click_display(count))
        except Exception:
            pass

    def _update_click_display(self, count: int):
        self.click_count_label.configure(text=f"CLICKS: {count:,}")
        cps = self._calculate_cps()
        self.cps_label.configure(text=f"CPS: {cps:.1f}")

        if self._mini_hud and self._mini_hud.winfo_exists():
            self._mini_hud.update_status(True, cps, count)

    def _calculate_cps(self) -> float:
        elapsed = time.time() - self._cps_start_time
        if elapsed <= 0:
            return 0.0
        return self.clicker_engine.click_count / elapsed

    def _on_engine_stopped(self):
        try:
            self.after(0, lambda: self._update_ui_running(False))
        except Exception:
            pass

    def _on_macro_step_update(self, current: int, total: int):
        pass

    def _on_macro_stopped(self):
        try:
            self.after(0, lambda: self.macro_card.set_running(False))
        except Exception:
            pass

    # ─── Settings Callbacks ────────────────────────────────────

    def _on_language_changed(self, value: str):
        langs = get_available_languages()
        lang_map = {name: code for code, name in langs}
        lang_code = lang_map.get(value, 'en')

        if lang_code == self.config.language:
            return

        # 1. Collect current settings accurately before switching
        self.config = self._collect_config_from_ui()
        self.config.language = lang_code
        set_language(lang_code)

        # 2. Save session immediately
        self._save_current_session()

        # 3. Rebuild UI dynamically in-place (no restart needed!)
        self._build_ui()
        self._load_config_to_ui()

        # 4. Stay on SETTINGS tab
        try:
            self.tabview.set("SETTINGS")
        except Exception:
            pass

    def _restart_app(self):
        """Cleanly restart the application to apply deep changes like language."""
        try:
            self._save_current_session()
            if hasattr(self, 'instance_server') and self.instance_server:
                try:
                    self.instance_server.close()
                except Exception:
                    pass
                self.instance_server = None

            self._on_close()

            time.sleep(0.25)

            from main import get_app_dir, get_app_executable
            real_exe, extra_args = get_app_executable()
            app_dir = get_app_dir()

            import subprocess
            subprocess.Popen([real_exe] + extra_args, cwd=app_dir)
            os._exit(0)
        except Exception as e:
            print(f"Restart error: {e}")

    def _on_theme_changed(self, value: str):
        if value == t("dark"):
            self.config.theme = "dark"
            ctk.set_appearance_mode("dark")
        else:
            self.config.theme = "light"
            ctk.set_appearance_mode("light")
        self._save_current_session()

    def _on_always_on_top_changed(self):
        self.config.always_on_top = self.aot_var.get()
        self.attributes("-topmost", self.config.always_on_top)
        self._save_current_session()

    def _toggle_always_on_top(self):
        new_val = not self.config.always_on_top
        self.config.always_on_top = new_val
        self.aot_var.set(new_val)
        self.attributes("-topmost", new_val)
        self.aot_btn.configure(
            fg_color=BG_HOVER if new_val else BG_PANEL_ALT,
            text_color=ACCENT_CYAN if new_val else TEXT_MAIN
        )
        self._save_current_session()

    def _on_hotkey_mode_changed(self, new_mode: str):
        self.config.hotkey_mode = new_mode
        self.hotkey_manager.mode = new_mode
        self.hotkey_manager.start()

    def _start_listening_for_hotkey(self, target: str):
        if self._hk_listener:
            try:
                self._hk_listener.stop()
            except Exception:
                pass
            self._hk_listener = None

        btn = self.bind_click_btn if target == "click" else self.bind_macro_btn
        btn.configure(
            text="PRESS KEY...",
            fg_color=ACCENT_AMBER,
            text_color="#0D0F12"
        )
        self.hk_status_label.configure(
            text="Press any key (F1-F12, letter, number) or ESC to cancel...",
            text_color=ACCENT_AMBER
        )

        from pynput import keyboard as kb
        held_modifiers = set()

        def on_press(key):
            try:
                if key in (kb.Key.ctrl, kb.Key.ctrl_l, kb.Key.ctrl_r):
                    held_modifiers.add('ctrl')
                    return
                if key in (kb.Key.alt, kb.Key.alt_l, kb.Key.alt_r, kb.Key.alt_gr):
                    held_modifiers.add('alt')
                    return
                if key in (kb.Key.shift, kb.Key.shift_l, kb.Key.shift_r):
                    held_modifiers.add('shift')
                    return

                if key == kb.Key.esc:
                    self.after(0, lambda: self._finish_listening_hotkey(target, None))
                    return False

                if isinstance(key, kb.Key):
                    k_str = key.name
                elif hasattr(key, 'char') and key.char:
                    k_str = key.char
                elif hasattr(key, 'vk') and key.vk:
                    k_str = chr(key.vk).lower() if 32 <= key.vk <= 126 else f"vk{key.vk}"
                else:
                    k_str = str(key).strip("'")

                if held_modifiers:
                    combo_str = "+".join(sorted(held_modifiers) + [k_str])
                else:
                    combo_str = k_str

                self.after(0, lambda: self._finish_listening_hotkey(target, combo_str))
                return False
            except Exception as ex:
                print(f"Error capturing key: {ex}")
                self.after(0, lambda: self._finish_listening_hotkey(target, None))
                return False

        def on_release(key):
            pass

        self._hk_listener = kb.Listener(on_press=on_press, on_release=on_release)
        self._hk_listener.start()

    def _finish_listening_hotkey(self, target: str, captured_key: Optional[str]):
        self._hk_listener = None
        btn = self.bind_click_btn if target == "click" else self.bind_macro_btn
        btn.configure(
            text="RECORD",
            fg_color=BG_PANEL_ALT,
            text_color=TEXT_MAIN
        )

        if not captured_key:
            self.hk_status_label.configure(
                text="Binding cancelled.",
                text_color=TEXT_MUTED
            )
            return

        captured_clean = captured_key.strip().lower()
        if not is_valid_hotkey(captured_clean):
            self.hk_status_label.configure(
                text=f"Key '{captured_key}' is not a valid hotkey.",
                text_color=ACCENT_ALERT
            )
            return

        if target == "click":
            self.config.hotkey = captured_clean
            self.hotkey_entry.configure(state="normal")
            self.hotkey_entry.delete(0, 'end')
            self.hotkey_entry.insert(0, captured_clean.upper().strip('<>'))
            self.hotkey_entry.configure(state="readonly")
            self.hotkey_label.configure(text=f"[{captured_clean.upper().strip('<>')}]")
            self.start_button.configure(
                text=f"▶  {t('start_clicking').upper()} ({captured_clean.upper().strip('<>')})"
            )
        else:
            self.config.macro_hotkey = captured_clean
            self.macro_hotkey_entry.configure(state="normal")
            self.macro_hotkey_entry.delete(0, 'end')
            self.macro_hotkey_entry.insert(0, captured_clean.upper().strip('<>'))
            self.macro_hotkey_entry.configure(state="readonly")
            self.macro_card.set_hotkey(captured_clean)

        self.hotkey_manager.update_hotkey(self.config.hotkey, self.config.macro_hotkey)
        self._save_current_session()

        target_name = "Auto Click" if target == "click" else "Macro"
        self.hk_status_label.configure(
            text=f"✓ {target_name} key set to: [{captured_clean.upper().strip('<>')}]",
            text_color=ACCENT_PRIMARY
        )

    def _apply_hotkey_settings(self):
        new_hotkey = self.hotkey_entry.get().strip().lower()
        new_macro = self.macro_hotkey_entry.get().strip().lower()

        if not new_hotkey:
            new_hotkey = self.config.hotkey
        if not new_macro:
            new_macro = self.config.macro_hotkey

        if not is_valid_hotkey(new_hotkey):
            self.hk_status_label.configure(
                text=f"Invalid Auto Click key: '{new_hotkey}'",
                text_color=ACCENT_ALERT
            )
            return

        if not is_valid_hotkey(new_macro):
            self.hk_status_label.configure(
                text=f"Invalid Macro key: '{new_macro}'",
                text_color=ACCENT_ALERT
            )
            return

        self.config.hotkey = new_hotkey
        self.config.macro_hotkey = new_macro

        self.hotkey_manager.update_hotkey(self.config.hotkey, self.config.macro_hotkey)

        self.hotkey_label.configure(text=f"[{self.config.hotkey.upper().strip('<>')}]")
        self.start_button.configure(
            text=f"▶  {t('start_clicking').upper()} ({self.config.hotkey.upper().strip('<>')})"
        )
        self.macro_card.set_hotkey(self.config.macro_hotkey)

        self._save_current_session()

        self.hk_status_label.configure(
            text=f"✓ Keybinds applied: [{self.config.hotkey.upper().strip('<>')}] / [{self.config.macro_hotkey.upper().strip('<>')}]",
            text_color=ACCENT_PRIMARY
        )

    def _reset_default_hotkeys(self):
        default_click = "f6"
        default_macro = "f7"

        self.config.hotkey = default_click
        self.config.macro_hotkey = default_macro

        self.hotkey_entry.configure(state="normal")
        self.hotkey_entry.delete(0, 'end')
        self.hotkey_entry.insert(0, default_click.upper())
        self.hotkey_entry.configure(state="readonly")

        self.macro_hotkey_entry.configure(state="normal")
        self.macro_hotkey_entry.delete(0, 'end')
        self.macro_hotkey_entry.insert(0, default_macro.upper())
        self.macro_hotkey_entry.configure(state="readonly")

        self.hotkey_manager.update_hotkey(self.config.hotkey, self.config.macro_hotkey)

        self.hotkey_label.configure(text=f"[{default_click.upper()}]")
        self.start_button.configure(
            text=f"▶  {t('start_clicking').upper()} ({default_click.upper()})"
        )
        self.macro_card.set_hotkey(default_macro)

        self._save_current_session()

        self.hk_status_label.configure(
            text=f"✓ {t('hotkeys_reset_success')}",
            text_color=ACCENT_PRIMARY
        )

    def _save_current_session(self):
        if getattr(self, '_is_loading_config', False):
            return
        try:
            config = self._collect_config_from_ui()
            self.profile_manager.save_last_session(config)
        except Exception:
            pass

    # ─── Profile Management ────────────────────────────────────

    def _save_profile(self):
        config = self._collect_config_from_ui()
        name = self.profile_card.get_selected_profile()
        self.profile_manager.save_profile(name, config)
        self._current_profile_name = name

    def _save_profile_as(self):
        dialog = ctk.CTkInputDialog(
            text=t("profile_name_prompt"), title=t("save_as")
        )
        name = dialog.get_input()
        if name and name.strip():
            name = name.strip()
            config = self._collect_config_from_ui()
            self.profile_manager.save_profile(name, config)
            self._current_profile_name = name
            profiles = self.profile_manager.list_profiles()
            self.profile_card.set_profiles(profiles, name)

    def _load_profile(self):
        name = self.profile_card.get_selected_profile()
        try:
            config = self.profile_manager.load_profile(name)
            self.config = config
            self._current_profile_name = name
            self._load_config_to_ui()
        except Exception as e:
            print(f"Failed to load profile: {e}")

    def _delete_profile(self):
        from tkinter import messagebox
        name = self.profile_card.get_selected_profile()
        if messagebox.askyesno(t("delete"), t("confirm_delete")):
            self.profile_manager.delete_profile(name)
            profiles = self.profile_manager.list_profiles()
            if not profiles:
                profiles = ["default"]
            self.profile_card.set_profiles(profiles, profiles[0])

    # ─── Mini HUD ──────────────────────────────────────────────

    def _toggle_mini_hud(self):
        from ui.components.mini_hud import MiniHUD

        if self._mini_hud and self._mini_hud.winfo_exists():
            self._mini_hud.toggle()
        else:
            self._mini_hud = MiniHUD(self)
            self._mini_hud.on_stop_clicked = self._stop_clicking
            is_running = self.clicker_engine.is_running
            cps = self._calculate_cps() if is_running else 0
            self._mini_hud.update_status(
                is_running, cps, self.clicker_engine.click_count
            )

    # ─── System Tray ───────────────────────────────────────────

    def _minimize_to_tray(self):
        self.withdraw()
        if self._tray_manager:
            self._tray_manager.notify(
                "AutoClicker",
                "App minimized to tray. Double-click tray icon to restore."
            )

    def restore_window(self):
        """Force the window to deiconify, lift to front, and focus."""
        try:
            self.deiconify()
            self.lift()
            self.attributes("-topmost", True)
            self.focus_force()
            if not self.config.always_on_top:
                self.after(250, lambda: self.attributes("-topmost", False))
        except Exception:
            pass

    def toggle_visibility(self):
        if self.state() == 'withdrawn' or not self.winfo_viewable():
            self.restore_window()
        else:
            self.withdraw()

    # ─── Status Updater ────────────────────────────────────────

    def _start_status_updater(self):
        self._update_status()

    def _update_status(self):
        try:
            if self.clicker_engine.is_running:
                count = self.clicker_engine.click_count
                self.click_count_label.configure(
                    text=f"CLICKS: {count:,}"
                )
                cps = self._calculate_cps()
                self.cps_label.configure(text=f"CPS: {cps:.1f}")

                if self._mini_hud and self._mini_hud.winfo_exists():
                    self._mini_hud.update_status(True, cps, count)
        except Exception:
            pass

        self.after(200, self._update_status)

    # ─── Cleanup ───────────────────────────────────────────────

    def _on_close(self):
        try:
            config = self._collect_config_from_ui()
            self.profile_manager.save_last_session(config)
        except Exception:
            pass

        self.clicker_engine.stop()
        self.macro_engine.stop()
        self.hotkey_manager.stop()
        self._cleanup_picker()

        if self._recording_listener:
            self._recording_listener.stop()

        if self._hk_listener:
            try:
                self._hk_listener.stop()
            except Exception:
                pass

        if self._tray_manager:
            try:
                self._tray_manager.stop()
            except Exception:
                pass

        self.destroy()

    def exit_application(self):
        self._on_close()
