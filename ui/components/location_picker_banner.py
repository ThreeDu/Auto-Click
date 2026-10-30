"""Floating banner shown while picking a screen location."""

import customtkinter as ctk
from i18n.localization import get_language
from ui.theme import (
    BG_PANEL, TEXT_MAIN, TEXT_MUTED, ACCENT_ALERT, ACCENT_CYAN,
    FONT_FAMILY, RADIUS_CONTROL
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
