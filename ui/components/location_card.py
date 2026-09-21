"""Location configuration card component — Utilitarian / Technical redesign."""

import customtkinter as ctk
from typing import Optional, Callable
from i18n.localization import t
from core.win32_input import get_cursor_pos
from ui.theme import (
    BG_PANEL, BG_PANEL_ALT, BG_HOVER, BORDER_SUBTLE,
    TEXT_MAIN, TEXT_MUTED, TEXT_DIM, ACCENT_AMBER, ACCENT_CYAN,
    FONT_FAMILY, FONT_MONO, RADIUS_PANEL, RADIUS_CONTROL
)


class LocationCard(ctk.CTkFrame):
    """Card for configuring target coordinates and location picking."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=RADIUS_PANEL,
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER_SUBTLE,
            **kwargs
        )
        self.on_pick_location: Optional[Callable] = None

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(14, 10))

        self.title_label = ctk.CTkLabel(
            header_frame,
            text=t('location_title').upper(),
            font=(FONT_FAMILY, 12, "bold"),
            text_color=TEXT_MUTED
        )
        self.title_label.pack(side="left")

        # Live Coordinate Monitor
        self.preview_label = ctk.CTkLabel(
            header_frame,
            text="POS: X: ----  Y: ----",
            font=(FONT_MONO, 11, "bold"),
            text_color=ACCENT_CYAN
        )
        self.preview_label.pack(side="right")

        # Mode Selection
        self.mode_var = ctk.StringVar(value="cursor")

        options_row = ctk.CTkFrame(self, fg_color="transparent")
        options_row.pack(fill="x", padx=16, pady=(0, 10))

        self.cursor_rb = ctk.CTkRadioButton(
            options_row,
            text=t('follow_cursor'),
            variable=self.mode_var,
            value="cursor",
            font=(FONT_FAMILY, 12),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER,
            command=self.toggle_fixed_inputs
        )
        self.cursor_rb.pack(side="left", padx=(0, 20))

        self.fixed_rb = ctk.CTkRadioButton(
            options_row,
            text=t('fixed_coordinate'),
            variable=self.mode_var,
            value="fixed",
            font=(FONT_FAMILY, 12),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER,
            command=self.toggle_fixed_inputs
        )
        self.fixed_rb.pack(side="left")

        # Fixed Inputs Row
        self.fixed_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.fixed_frame.pack(fill="x", padx=16, pady=(0, 14))

        vcmd = (self.register(self.validate_number), '%P')

        # X input
        ctk.CTkLabel(
            self.fixed_frame,
            text="X:",
            font=(FONT_MONO, 12, "bold"),
            text_color=TEXT_DIM
        ).pack(side="left", padx=(0, 4))

        self.x_entry = ctk.CTkEntry(
            self.fixed_frame,
            width=70,
            height=32,
            font=(FONT_MONO, 13, "bold"),
            fg_color=BG_PANEL_ALT,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            text_color=TEXT_MAIN,
            justify="center",
            validate="key",
            validatecommand=vcmd
        )
        self.x_entry.insert(0, "0")
        self.x_entry.pack(side="left", padx=(0, 12))

        # Y input
        ctk.CTkLabel(
            self.fixed_frame,
            text="Y:",
            font=(FONT_MONO, 12, "bold"),
            text_color=TEXT_DIM
        ).pack(side="left", padx=(0, 4))

        self.y_entry = ctk.CTkEntry(
            self.fixed_frame,
            width=70,
            height=32,
            font=(FONT_MONO, 13, "bold"),
            fg_color=BG_PANEL_ALT,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            text_color=TEXT_MAIN,
            justify="center",
            validate="key",
            validatecommand=vcmd
        )
        self.y_entry.insert(0, "0")
        self.y_entry.pack(side="left", padx=(0, 14))

        # Pick Location Button
        self.pick_btn = ctk.CTkButton(
            self.fixed_frame,
            text=f"🎯 {t('pick_location')}",
            height=32,
            font=(FONT_FAMILY, 11, "bold"),
            fg_color=BG_PANEL_ALT,
            hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            command=self.handle_pick_location
        )
        self.pick_btn.pack(side="left", fill="x", expand=True)

        self.toggle_fixed_inputs()
        self.update_pos()

    def validate_number(self, p: str) -> bool:
        """Validate numeric input."""
        return str.isdigit(p) or p == ""

    def toggle_fixed_inputs(self) -> None:
        """Enable/disable fixed inputs."""
        state = "normal" if self.mode_var.get() == "fixed" else "disabled"
        self.x_entry.configure(state=state)
        self.y_entry.configure(state=state)
        self.pick_btn.configure(state=state)

    def handle_pick_location(self) -> None:
        """Trigger coordinate picker."""
        if self.on_pick_location:
            self.on_pick_location()

    def update_pos(self) -> None:
        """Periodically update live mouse monitor."""
        try:
            x, y = get_cursor_pos()
            self.preview_label.configure(text=f"X: {x:4d}  Y: {y:4d}")
        except Exception:
            pass
        self.after(100, self.update_pos)

    def get_mode(self) -> str:
        """Get location mode."""
        return self.mode_var.get()

    def get_fixed_pos(self) -> tuple[int, int]:
        """Get coordinates."""
        try:
            x = int(self.x_entry.get()) if self.x_entry.get() else 0
            y = int(self.y_entry.get()) if self.y_entry.get() else 0
            return (x, y)
        except ValueError:
            return (0, 0)

    def set_values(self, mode: str, x: int, y: int) -> None:
        """Set location values."""
        self.mode_var.set(mode)
        self.x_entry.configure(state="normal")
        self.x_entry.delete(0, 'end')
        self.x_entry.insert(0, str(x))

        self.y_entry.configure(state="normal")
        self.y_entry.delete(0, 'end')
        self.y_entry.insert(0, str(y))
        self.toggle_fixed_inputs()
