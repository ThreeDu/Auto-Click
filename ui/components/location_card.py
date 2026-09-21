"""Location configuration card component — Compact & Utilitarian."""

import customtkinter as ctk
from typing import Optional, Callable
from i18n.localization import t
from core.win32_input import get_cursor_pos
from ui.theme import (
    BG_PANEL, BG_PANEL_ALT, BG_HOVER, BORDER_SUBTLE,
    TEXT_MAIN, TEXT_MUTED, TEXT_DIM, ACCENT_AMBER, ACCENT_CYAN,
    FONT_FAMILY, FONT_MONO, RADIUS_PANEL, RADIUS_CONTROL,
    FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_MD
)


class LocationCard(ctk.CTkFrame):
    """Compact card for target coordinates and live location monitor."""

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
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            header,
            text=t('location_title').upper(),
            font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            text_color=TEXT_MUTED
        ).pack(side="left")

        self.preview_label = ctk.CTkLabel(
            header,
            text="0, 0",
            font=(FONT_MONO, FONT_SIZE_SM, "bold"),
            text_color=ACCENT_CYAN
        )
        self.preview_label.pack(side="right")

        # Mode Radio
        self.mode_var = ctk.StringVar(value="cursor")
        mode_row = ctk.CTkFrame(self, fg_color="transparent")
        mode_row.pack(fill="x", padx=10, pady=(0, 6))

        self.cursor_rb = ctk.CTkRadioButton(
            mode_row,
            text=t('follow_cursor'),
            variable=self.mode_var,
            value="cursor",
            font=(FONT_FAMILY, FONT_SIZE_BASE),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER,
            radiobutton_width=16,
            radiobutton_height=16,
            command=self.toggle_fixed_inputs
        )
        self.cursor_rb.pack(side="left", padx=(0, 20))

        self.fixed_rb = ctk.CTkRadioButton(
            mode_row,
            text=t('fixed_coordinate'),
            variable=self.mode_var,
            value="fixed",
            font=(FONT_FAMILY, FONT_SIZE_BASE),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER,
            radiobutton_width=16,
            radiobutton_height=16,
            command=self.toggle_fixed_inputs
        )
        self.fixed_rb.pack(side="left")

        # Inputs Row (X, Y, Pick)
        self.fixed_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.fixed_frame.pack(fill="x", padx=10, pady=(0, 8))

        vcmd = (self.register(self.validate_number), '%P')

        ctk.CTkLabel(self.fixed_frame, text="X", font=(FONT_MONO, FONT_SIZE_SM, "bold"), text_color=TEXT_DIM).pack(side="left", padx=(0, 4))
        self.x_entry = ctk.CTkEntry(
            self.fixed_frame, width=56, height=28,
            font=(FONT_MONO, FONT_SIZE_SM, "bold"), fg_color=BG_PANEL_ALT, border_color=BORDER_SUBTLE,
            border_width=1, corner_radius=RADIUS_CONTROL, text_color=TEXT_MAIN,
            justify="center", validate="key", validatecommand=vcmd
        )
        self.x_entry.insert(0, "0")
        self.x_entry.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(self.fixed_frame, text="Y", font=(FONT_MONO, FONT_SIZE_SM, "bold"), text_color=TEXT_DIM).pack(side="left", padx=(0, 4))
        self.y_entry = ctk.CTkEntry(
            self.fixed_frame, width=56, height=28,
            font=(FONT_MONO, FONT_SIZE_SM, "bold"), fg_color=BG_PANEL_ALT, border_color=BORDER_SUBTLE,
            border_width=1, corner_radius=RADIUS_CONTROL, text_color=TEXT_MAIN,
            justify="center", validate="key", validatecommand=vcmd
        )
        self.y_entry.insert(0, "0")
        self.y_entry.pack(side="left", padx=(0, 12))

        self.pick_btn = ctk.CTkButton(
            self.fixed_frame,
            text=f"🎯 {t('pick_location')}",
            width=120,
            height=28,
            font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            fg_color=BG_PANEL_ALT,
            hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            command=self.handle_pick_location
        )
        self.pick_btn.pack(side="left")

        # Restore Cursor Checkbox
        self.restore_cursor_var = ctk.BooleanVar(value=False)
        self.restore_cursor_cb = ctk.CTkCheckBox(
            self.fixed_frame,
            text=t('restore_cursor'),
            variable=self.restore_cursor_var,
            font=(FONT_FAMILY, FONT_SIZE_SM),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER,
            checkbox_width=16,
            checkbox_height=16
        )
        self.restore_cursor_cb.pack(side="right", padx=(10, 0))

        self.toggle_fixed_inputs()
        self.update_pos()

    def validate_number(self, p: str) -> bool:
        return str.isdigit(p) or p == ""

    def toggle_fixed_inputs(self) -> None:
        state = "normal" if self.mode_var.get() == "fixed" else "disabled"
        self.x_entry.configure(state=state)
        self.y_entry.configure(state=state)
        self.restore_cursor_cb.configure(state=state)

    def handle_pick_location(self) -> None:
        if self.mode_var.get() != "fixed":
            self.mode_var.set("fixed")
            self.toggle_fixed_inputs()
        if self.on_pick_location:
            self.on_pick_location()

    def update_pos(self) -> None:
        try:
            x, y = get_cursor_pos()
            self.preview_label.configure(text=f"{x}, {y}")
        except Exception:
            pass
        self.after(100, self.update_pos)

    def get_mode(self) -> str:
        return self.mode_var.get()

    def get_fixed_pos(self) -> tuple[int, int]:
        try:
            x = int(self.x_entry.get()) if self.x_entry.get() else 0
            y = int(self.y_entry.get()) if self.y_entry.get() else 0
            return (x, y)
        except ValueError:
            return (0, 0)

    def is_restore_cursor(self) -> bool:
        return self.restore_cursor_var.get()

    def set_restore_cursor(self, value: bool) -> None:
        self.restore_cursor_var.set(value)

    def set_values(self, mode: str, x: int, y: int, restore_cursor: Optional[bool] = None) -> None:
        self.mode_var.set(mode)
        self.x_entry.configure(state="normal")
        self.x_entry.delete(0, 'end')
        self.x_entry.insert(0, str(x))

        self.y_entry.configure(state="normal")
        self.y_entry.delete(0, 'end')
        self.y_entry.insert(0, str(y))

        if restore_cursor is not None:
            self.restore_cursor_var.set(restore_cursor)

        self.toggle_fixed_inputs()
