"""Options configuration card component — Utilitarian / Technical redesign."""

import customtkinter as ctk
from i18n.localization import t
from ui.theme import (
    BG_PANEL, BG_PANEL_ALT, BORDER_SUBTLE,
    TEXT_MAIN, TEXT_MUTED, TEXT_DIM, ACCENT_AMBER,
    FONT_FAMILY, FONT_MONO, RADIUS_PANEL, RADIUS_CONTROL
)


class OptionsCard(ctk.CTkFrame):
    """Card for configuring click action and trigger mode."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=RADIUS_PANEL,
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER_SUBTLE,
            **kwargs
        )

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(14, 10))

        self.title_label = ctk.CTkLabel(
            header_frame,
            text=t('options_title').upper(),
            font=(FONT_FAMILY, 12, "bold"),
            text_color=TEXT_MUTED
        )
        self.title_label.pack(side="left")

        # Row 1: Mouse Button & Click Type (2 equal columns)
        cols_frame = ctk.CTkFrame(self, fg_color="transparent")
        cols_frame.pack(fill="x", padx=16, pady=(0, 12))
        cols_frame.grid_columnconfigure((0, 1), weight=1)

        # Mouse Button
        btn_cell = ctk.CTkFrame(cols_frame, fg_color="transparent")
        btn_cell.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkLabel(
            btn_cell,
            text=t('mouse_button').upper(),
            font=(FONT_FAMILY, 10, "bold"),
            text_color=TEXT_DIM
        ).pack(anchor="w", pady=(0, 3))

        self.btn_var = ctk.StringVar(value="left")
        self.btn_menu = ctk.CTkOptionMenu(
            btn_cell,
            variable=self.btn_var,
            values=[t('left'), t('right'), t('middle')],
            height=32,
            font=(FONT_FAMILY, 12, "bold"),
            fg_color=BG_PANEL_ALT,
            button_color=BG_PANEL_ALT,
            button_hover_color="#252B36",
            text_color=TEXT_MAIN,
            corner_radius=RADIUS_CONTROL
        )
        self.btn_menu.pack(fill="x")

        # Click Type
        type_cell = ctk.CTkFrame(cols_frame, fg_color="transparent")
        type_cell.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        ctk.CTkLabel(
            type_cell,
            text=t('click_type').upper(),
            font=(FONT_FAMILY, 10, "bold"),
            text_color=TEXT_DIM
        ).pack(anchor="w", pady=(0, 3))

        self.type_var = ctk.StringVar(value="single")
        self.type_menu = ctk.CTkOptionMenu(
            type_cell,
            variable=self.type_var,
            values=[t('single'), t('double'), t('triple')],
            height=32,
            font=(FONT_FAMILY, 12, "bold"),
            fg_color=BG_PANEL_ALT,
            button_color=BG_PANEL_ALT,
            button_hover_color="#252B36",
            text_color=TEXT_MAIN,
            corner_radius=RADIUS_CONTROL
        )
        self.type_menu.pack(fill="x")

        # Row 2: Activation Mode (Toggle vs Hold)
        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            mode_frame,
            text=t('mode').upper(),
            font=(FONT_FAMILY, 10, "bold"),
            text_color=TEXT_DIM
        ).pack(anchor="w", pady=(0, 4))

        radio_row = ctk.CTkFrame(mode_frame, fg_color="transparent")
        radio_row.pack(fill="x")

        self.mode_var = ctk.StringVar(value="toggle")

        self.mode_toggle = ctk.CTkRadioButton(
            radio_row,
            text=f"{t('toggle')} (Press to start/stop)",
            variable=self.mode_var,
            value="toggle",
            font=(FONT_FAMILY, 12),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER
        )
        self.mode_toggle.pack(side="left", padx=(0, 16))

        self.mode_hold = ctk.CTkRadioButton(
            radio_row,
            text=f"{t('hold')} (Active while held)",
            variable=self.mode_var,
            value="hold",
            font=(FONT_FAMILY, 12),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER
        )
        self.mode_hold.pack(side="left")

    def get_button(self) -> str:
        """Get selected button."""
        val = self.btn_var.get()
        if val == t('right'): return 'right'
        if val == t('middle'): return 'middle'
        return 'left'

    def get_click_type(self) -> str:
        """Get selected click type."""
        val = self.type_var.get()
        if val == t('double'): return 'double'
        if val == t('triple'): return 'triple'
        return 'single'

    def get_mode(self) -> str:
        """Get selected mode."""
        return self.mode_var.get()

    def set_values(self, button: str, click_type: str, mode: str) -> None:
        """Set values."""
        if button == 'right':
            self.btn_var.set(t('right'))
        elif button == 'middle':
            self.btn_var.set(t('middle'))
        else:
            self.btn_var.set(t('left'))

        if click_type == 'double':
            self.type_var.set(t('double'))
        elif click_type == 'triple':
            self.type_var.set(t('triple'))
        else:
            self.type_var.set(t('single'))

        self.mode_var.set(mode)
