"""
AutoClicker Pro — Main Application Window
Hallmark Utilitarian / Technical Redesign.
Connects all UI components with core engines in a precision hardware-instrument aesthetic.
"""

import time
import customtkinter as ctk
from typing import Optional

from config import ClickerConfig
from profile_manager import ProfileManager
from core.clicker_engine import ClickerEngine
from core.macro_engine import MacroEngine, MacroStep
from core.hotkey_manager import HotkeyManager
from core.win32_input import get_cursor_pos
from i18n.localization import t, set_language, get_language, get_available_languages
from ui.theme import (
    BG_BASE, BG_PANEL, BG_PANEL_ALT, BG_HOVER, BORDER_SUBTLE,
    TEXT_MAIN, TEXT_MUTED, TEXT_DIM, ACCENT_PRIMARY, ACCENT_PRIMARY_HOVER,
    ACCENT_ALERT, ACCENT_ALERT_HOVER, ACCENT_AMBER, ACCENT_CYAN,
    FONT_FAMILY, FONT_MONO, RADIUS_PANEL, RADIUS_CONTROL
)


class AutoClickerApp(ctk.CTk):
    """Main application window for AutoClicker Pro."""

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
        self._current_profile_name: str = "default"

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
        """Configure the main window."""
        self.title("AutoClicker Pro — Tactical Automation")
        self.geometry("540x740")
        self.minsize(500, 680)
        self.resizable(True, True)
        self.configure(fg_color=BG_BASE)

        if self.config.always_on_top:
            self.attributes("-topmost", True)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_theme(self):
        """Apply the color theme."""
        ctk.set_appearance_mode(self.config.theme)

    # ─── Build UI ──────────────────────────────────────────────

    def _build_ui(self):
        """Build the complete user interface."""
        # Top Instrument HUD
        self._build_status_bar()

        # Segmented Tab View
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=RADIUS_PANEL,
            fg_color=BG_BASE,
            segmented_button_fg_color=BG_PANEL_ALT,
            segmented_button_selected_color=BG_HOVER,
            segmented_button_selected_hover_color="#2A303C",
            segmented_button_unselected_color=BG_PANEL_ALT,
            segmented_button_unselected_hover_color=BG_HOVER,
            text_color=TEXT_MAIN
        )
        self.tabview.pack(fill="both", expand=True, padx=12, pady=(4, 6))

        # Tab 1: Auto Click
        tab_auto = self.tabview.add("AUTO CLICK")
        self._build_auto_click_tab(tab_auto)

        # Tab 2: Macro Workbench
        tab_macro = self.tabview.add("MACRO WORKBENCH")
        self._build_macro_tab(tab_macro)

        # Tab 3: Settings
        tab_settings = self.tabview.add("SETTINGS")
        self._build_settings_tab(tab_settings)

        # Bottom Profile & Utility Dock
        self._build_bottom_bar()

    def _build_status_bar(self):
        """Build the top instrument deck / status bar."""
        self.status_frame = ctk.CTkFrame(
            self,
            corner_radius=RADIUS_PANEL,
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER_SUBTLE,
            height=44
        )
        self.status_frame.pack(fill="x", padx=12, pady=(12, 4))
        self.status_frame.grid_columnconfigure(1, weight=1)

        # Status indicator
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="● STANDBY",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=TEXT_MUTED
        )
        self.status_label.grid(row=0, column=0, padx=(14, 10), pady=10, sticky="w")

        # Live Click counter
        self.click_count_label = ctk.CTkLabel(
            self.status_frame,
            text="CLICKS: 0",
            font=(FONT_MONO, 12, "bold"),
            text_color=TEXT_MAIN
        )
        self.click_count_label.grid(row=0, column=1, padx=8, pady=10)

        # Live CPS
        self.cps_label = ctk.CTkLabel(
            self.status_frame,
            text="CPS: 0.0",
            font=(FONT_MONO, 12, "bold"),
            text_color=ACCENT_CYAN
        )
        self.cps_label.grid(row=0, column=2, padx=10, pady=10)

        # Trigger hotkey pill
        self.hotkey_label = ctk.CTkLabel(
            self.status_frame,
            text=f"KEY: [{self.config.hotkey.upper()}]",
            font=(FONT_MONO, 11, "bold"),
            text_color=ACCENT_AMBER
        )
        self.hotkey_label.grid(row=0, column=3, padx=(6, 14), pady=10, sticky="e")

    def _build_auto_click_tab(self, parent):
        """Build the auto click tab with all precision cards."""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True)

        from ui.components.interval_card import IntervalCard
        from ui.components.options_card import OptionsCard
        from ui.components.location_card import LocationCard
        from ui.components.repeat_card import RepeatCard

        # Interval Card
        self.interval_card = IntervalCard(scroll)
        self.interval_card.pack(fill="x", pady=4)

        # Options Card
        self.options_card = OptionsCard(scroll)
        self.options_card.pack(fill="x", pady=4)

        # Location Card
        self.location_card = LocationCard(scroll)
        self.location_card.pack(fill="x", pady=4)
        self.location_card.on_pick_location = self._handle_pick_location

        # Repeat Card
        self.repeat_card = RepeatCard(scroll)
        self.repeat_card.pack(fill="x", pady=4)

        # Tactical Start/Stop Button
        self.start_button = ctk.CTkButton(
            scroll,
            text=f"▶  {t('start_clicking').upper()} ({self.config.hotkey.upper()})",
            font=(FONT_FAMILY, 14, "bold"),
            height=46,
            corner_radius=RADIUS_CONTROL,
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_PRIMARY_HOVER,
            text_color="#042F2E",
            command=self._toggle_clicking
        )
        self.start_button.pack(fill="x", pady=(10, 8))

    def _build_macro_tab(self, parent):
        """Build the macro tab."""
        from ui.components.macro_card import MacroCard

        self.macro_card = MacroCard(parent)
        self.macro_card.pack(fill="both", expand=True, pady=4)
        self.macro_card.on_run_macro = self._start_macro
        self.macro_card.on_stop_macro = self._stop_macro
        self.macro_card.on_record_start = self._start_recording
        self.macro_card.on_record_stop = self._stop_recording

    def _build_settings_tab(self, parent):
        """Build the settings tab."""
        settings_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent", corner_radius=0)
        settings_frame.pack(fill="both", expand=True)

        # Section: Preferences
        pref_card = ctk.CTkFrame(
            settings_frame,
            corner_radius=RADIUS_PANEL,
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        pref_card.pack(fill="x", pady=4)

        ctk.CTkLabel(
            pref_card,
            text="INTERFACE & REGIONAL",
            font=(FONT_FAMILY, 12, "bold"),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=16, pady=(14, 10))

        # Language Row
        lang_row = ctk.CTkFrame(pref_card, fg_color="transparent")
        lang_row.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(
            lang_row,
            text=t('language'),
            font=(FONT_FAMILY, 12),
            text_color=TEXT_MAIN
        ).pack(side="left")

        langs = get_available_languages()
        lang_names = [name for _, name in langs]
        current_lang_name = dict(langs).get(get_language(), "English")

        self.lang_menu = ctk.CTkOptionMenu(
            lang_row,
            values=lang_names,
            height=30,
            font=(FONT_FAMILY, 11, "bold"),
            fg_color=BG_PANEL_ALT,
            button_color=BG_PANEL_ALT,
            button_hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            corner_radius=RADIUS_CONTROL,
            command=self._on_language_changed
        )
        self.lang_menu.set(current_lang_name)
        self.lang_menu.pack(side="right")

        # Theme Row
        theme_row = ctk.CTkFrame(pref_card, fg_color="transparent")
        theme_row.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            theme_row,
            text=t('theme'),
            font=(FONT_FAMILY, 12),
            text_color=TEXT_MAIN
        ).pack(side="left")

        self.theme_menu = ctk.CTkOptionMenu(
            theme_row,
            values=[t("dark"), t("light")],
            height=30,
            font=(FONT_FAMILY, 11, "bold"),
            fg_color=BG_PANEL_ALT,
            button_color=BG_PANEL_ALT,
            button_hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            corner_radius=RADIUS_CONTROL,
            command=self._on_theme_changed
        )
        current_theme_name = t("dark") if self.config.theme == "dark" else t("light")
        self.theme_menu.set(current_theme_name)
        self.theme_menu.pack(side="right")

        # Section: Hotkeys
        hotkey_card = ctk.CTkFrame(
            settings_frame,
            corner_radius=RADIUS_PANEL,
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        hotkey_card.pack(fill="x", pady=8)

        ctk.CTkLabel(
            hotkey_card,
            text="HARDWARE HOTKEYS",
            font=(FONT_FAMILY, 12, "bold"),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=16, pady=(14, 10))

        # Auto-Click Hotkey
        hk1_row = ctk.CTkFrame(hotkey_card, fg_color="transparent")
        hk1_row.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(
            hk1_row,
            text="Auto Clicker Hotkey:",
            font=(FONT_FAMILY, 12),
            text_color=TEXT_MAIN
        ).pack(side="left")

        self.hotkey_entry = ctk.CTkEntry(
            hk1_row,
            width=80,
            height=30,
            font=(FONT_MONO, 12, "bold"),
            fg_color=BG_PANEL_ALT,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            text_color=ACCENT_AMBER,
            justify="center"
        )
        self.hotkey_entry.insert(0, self.config.hotkey.upper())
        self.hotkey_entry.pack(side="right")

        # Macro Hotkey
        hk2_row = ctk.CTkFrame(hotkey_card, fg_color="transparent")
        hk2_row.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            hk2_row,
            text="Macro Sequence Hotkey:",
            font=(FONT_FAMILY, 12),
            text_color=TEXT_MAIN
        ).pack(side="left")

        self.macro_hotkey_entry = ctk.CTkEntry(
            hk2_row,
            width=80,
            height=30,
            font=(FONT_MONO, 12, "bold"),
            fg_color=BG_PANEL_ALT,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            text_color=ACCENT_AMBER,
            justify="center"
        )
        self.macro_hotkey_entry.insert(0, self.config.macro_hotkey.upper())
        self.macro_hotkey_entry.pack(side="right")

        apply_hotkey_btn = ctk.CTkButton(
            hotkey_card,
            text="APPLY KEYBINDS",
            height=32,
            font=(FONT_FAMILY, 11, "bold"),
            fg_color=BG_PANEL_ALT,
            hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            command=self._apply_hotkey_settings
        )
        apply_hotkey_btn.pack(fill="x", padx=16, pady=(0, 14))

    def _build_bottom_bar(self):
        """Build the bottom profile and utility dock."""
        from ui.components.profile_card import ProfileCard

        self.profile_card = ProfileCard(self)
        self.profile_card.pack(fill="x", padx=12, pady=(0, 4))
        self.profile_card.on_save = self._save_profile
        self.profile_card.on_save_as = self._save_profile_as
        self.profile_card.on_load = self._load_profile
        self.profile_card.on_delete = self._delete_profile

        # Refresh profiles
        profiles = self.profile_manager.list_profiles()
        if not profiles:
            profiles = ["default"]
        self.profile_card.set_profiles(profiles, self._current_profile_name)

        # Quick Utility Buttons
        dock_frame = ctk.CTkFrame(
            self,
            corner_radius=RADIUS_PANEL,
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER_SUBTLE,
            height=40
        )
        dock_frame.pack(fill="x", padx=12, pady=(0, 12))

        self.aot_var = ctk.BooleanVar(value=self.config.always_on_top)
        self.aot_btn = ctk.CTkButton(
            dock_frame,
            text="PIN ON TOP",
            height=28,
            font=(FONT_FAMILY, 10, "bold"),
            fg_color=BG_PANEL_ALT,
            hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            command=self._toggle_always_on_top
        )
        self.aot_btn.pack(side="left", padx=(10, 4), pady=6)

        self.hud_btn = ctk.CTkButton(
            dock_frame,
            text="MINI HUD",
            height=28,
            font=(FONT_FAMILY, 10, "bold"),
            fg_color=BG_PANEL_ALT,
            hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            command=self._toggle_mini_hud
        )
        self.hud_btn.pack(side="left", padx=4, pady=6)

        self.tray_btn = ctk.CTkButton(
            dock_frame,
            text="TO TRAY",
            height=28,
            font=(FONT_FAMILY, 10, "bold"),
            fg_color="transparent",
            hover_color=BG_HOVER,
            text_color=TEXT_MUTED,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            command=self._minimize_to_tray
        )
        self.tray_btn.pack(side="right", padx=(4, 10), pady=6)

    # ─── Engine Setup ──────────────────────────────────────────

    def _setup_engines(self):
        """Configure engine callbacks."""
        self.clicker_engine.on_click_update = self._on_click_update
        self.clicker_engine.on_stopped = self._on_engine_stopped

        self.macro_engine.on_step_update = self._on_macro_step_update
        self.macro_engine.on_stopped = self._on_macro_stopped

    def _setup_hotkeys(self):
        """Configure and start global hotkeys."""
        self.hotkey_manager.hotkey = f"<{self.config.hotkey}>"
        self.hotkey_manager.macro_hotkey = f"<{self.config.macro_hotkey}>"
        self.hotkey_manager.mode = self.config.hotkey_mode
        self.hotkey_manager.on_toggle = self._toggle_clicking
        self.hotkey_manager.on_macro_toggle = self._toggle_macro
        self.hotkey_manager.on_hold_start = self._start_clicking
        self.hotkey_manager.on_hold_stop = self._stop_clicking
        self.hotkey_manager.start()

    def _setup_tray(self):
        """Initialize system tray."""
        try:
            from ui.tray import TrayManager
            self._tray_manager = TrayManager(self)
            self._tray_manager.on_toggle_click = self._toggle_clicking
            self._tray_manager.on_toggle_hud = self._toggle_mini_hud
            self._tray_manager.start()
            self._tray_manager.setup_close_override(self)
        except Exception as e:
            print(f"System tray initialization failed: {e}")

    # ─── Config ↔ UI ──────────────────────────────────────────

    def _load_config_to_ui(self):
        """Load config values into UI components."""
        c = self.config
        self.interval_card.set_values(
            c.interval_hours, c.interval_minutes,
            c.interval_seconds, c.interval_ms
        )
        self.options_card.set_values(c.mouse_button, c.click_type, c.hotkey_mode)
        self.location_card.set_values(c.location_mode, c.fixed_x, c.fixed_y)
        self.repeat_card.set_values(
            c.repeat_mode, c.repeat_count,
            c.jitter_enabled, c.jitter_interval_pct, c.jitter_position_px
        )
        if c.macro_steps:
            self.macro_card.set_steps(c.macro_steps)

    def _collect_config_from_ui(self) -> ClickerConfig:
        """Collect current config from all UI components."""
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
        )

    def _apply_config_to_engine(self):
        """Apply current UI config to the clicker engine."""
        config = self._collect_config_from_ui()
        self.clicker_engine.interval_ms = config.get_total_interval_ms()
        self.clicker_engine.button = config.mouse_button
        self.clicker_engine.click_type = config.click_type
        self.clicker_engine.jitter_enabled = config.jitter_enabled
        self.clicker_engine.jitter_interval_pct = config.jitter_interval_pct / 100.0
        self.clicker_engine.jitter_position_px = config.jitter_position_px

        if config.location_mode == 'fixed':
            self.clicker_engine.fixed_position = (config.fixed_x, config.fixed_y)
        else:
            self.clicker_engine.fixed_position = None

        if config.repeat_mode == 'count':
            self.clicker_engine.repeat_count = config.repeat_count
        else:
            self.clicker_engine.repeat_count = 0

    # ─── Click Control ─────────────────────────────────────────

    def _toggle_clicking(self):
        """Toggle the auto-clicker on/off."""
        if self.clicker_engine.is_running:
            self._stop_clicking()
        else:
            self._start_clicking()

    def _start_clicking(self):
        """Start the auto-clicker."""
        if self.clicker_engine.is_running:
            return

        self._apply_config_to_engine()
        self._cps_start_time = time.time()
        self._last_click_count = 0
        self.clicker_engine.start()

        self._update_ui_running(True)

    def _stop_clicking(self):
        """Stop the auto-clicker."""
        self.clicker_engine.stop()
        self._update_ui_running(False)

    def _update_ui_running(self, is_running: bool):
        """Update UI to reflect running state."""
        try:
            if is_running:
                self.status_label.configure(
                    text="● ACTIVE", text_color=ACCENT_PRIMARY
                )
                self.start_button.configure(
                    text=f"■  {t('stop_clicking').upper()} ({self.config.hotkey.upper()})",
                    fg_color=ACCENT_ALERT,
                    hover_color=ACCENT_ALERT_HOVER,
                    text_color="#FFFFFF"
                )
            else:
                self.status_label.configure(
                    text="● STANDBY", text_color=TEXT_MUTED
                )
                self.start_button.configure(
                    text=f"▶  {t('start_clicking').upper()} ({self.config.hotkey.upper()})",
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
        """Toggle macro execution."""
        if self.macro_engine.is_running:
            self._stop_macro()
        else:
            self._start_macro()

    def _start_macro(self):
        """Start macro execution."""
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

        self.macro_engine.start()
        self.macro_card.set_running(True)

    def _stop_macro(self):
        """Stop macro execution."""
        self.macro_engine.stop()
        self.macro_card.set_running(False)

    def _start_recording(self):
        """Start recording mouse clicks for macro."""
        self._is_recording_macro = True
        try:
            from pynput import mouse

            def on_click(x, y, button, pressed):
                if not self._is_recording_macro:
                    return False
                if pressed:
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
        """Stop recording mouse clicks."""
        self._is_recording_macro = False
        if self._recording_listener:
            self._recording_listener.stop()
            self._recording_listener = None

    # ─── Pick Location ─────────────────────────────────────────

    def _handle_pick_location(self):
        """Handle the pick location action."""
        self.withdraw()
        self.after(200, self._start_location_picker)

    def _start_location_picker(self):
        """Start listening for location pick."""
        try:
            from pynput import keyboard as kb

            def on_press(key):
                if key == kb.Key.space or key == kb.Key.enter:
                    x, y = get_cursor_pos()
                    self.after(0, lambda: self._finish_pick_location(x, y))
                    return False
                elif key == kb.Key.esc:
                    self.after(0, self._cancel_pick_location)
                    return False

            listener = kb.Listener(on_press=on_press)
            listener.start()
        except Exception as e:
            print(f"Pick location failed: {e}")
            self.deiconify()

    def _finish_pick_location(self, x: int, y: int):
        self.location_card.set_values('fixed', x, y)
        self.deiconify()

    def _cancel_pick_location(self):
        self.deiconify()

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
        set_language(lang_code)
        self.config.language = lang_code

        from tkinter import messagebox
        messagebox.showinfo(
            "Language Changed",
            "Please restart the application for the language change to take full effect."
        )

    def _on_theme_changed(self, value: str):
        if value == t("dark"):
            self.config.theme = "dark"
            ctk.set_appearance_mode("dark")
        else:
            self.config.theme = "light"
            ctk.set_appearance_mode("light")

    def _on_always_on_top_changed(self):
        self.config.always_on_top = self.aot_var.get()
        self.attributes("-topmost", self.config.always_on_top)

    def _toggle_always_on_top(self):
        new_val = not self.config.always_on_top
        self.config.always_on_top = new_val
        self.aot_var.set(new_val)
        self.attributes("-topmost", new_val)
        self.aot_btn.configure(
            fg_color=BG_HOVER if new_val else BG_PANEL_ALT,
            text_color=ACCENT_CYAN if new_val else TEXT_MAIN
        )

    def _apply_hotkey_settings(self):
        new_hotkey = self.hotkey_entry.get().strip().lower()
        new_macro_hotkey = self.macro_hotkey_entry.get().strip().lower()

        if new_hotkey:
            self.config.hotkey = new_hotkey
        if new_macro_hotkey:
            self.config.macro_hotkey = new_macro_hotkey

        self.hotkey_manager.hotkey = f"<{self.config.hotkey}>"
        self.hotkey_manager.macro_hotkey = f"<{self.config.macro_hotkey}>"
        self.hotkey_manager.update_hotkey(
            f"<{self.config.hotkey}>", f"<{self.config.macro_hotkey}>"
        )
        self.hotkey_label.configure(
            text=f"KEY: [{self.config.hotkey.upper()}]"
        )
        self.start_button.configure(
            text=f"▶  {t('start_clicking').upper()} ({self.config.hotkey.upper()})"
        )

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

    def toggle_visibility(self):
        if self.state() == 'withdrawn' or not self.winfo_viewable():
            self.deiconify()
            self.lift()
            self.focus_force()
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

        if self._recording_listener:
            self._recording_listener.stop()

        if self._tray_manager:
            try:
                self._tray_manager.stop()
            except Exception:
                pass

        self.destroy()

    def exit_application(self):
        self._on_close()
