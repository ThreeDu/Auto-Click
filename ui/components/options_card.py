"""Options configuration card component — Compact & Utilitarian."""

import customtkinter as ctk
from i18n.localization import t
from ui.theme import (
    BG_PANEL, BG_PANEL_ALT, BG_HOVER, BORDER_SUBTLE,
    TEXT_MAIN, TEXT_MUTED, TEXT_DIM, ACCENT_AMBER,
    FONT_FAMILY, RADIUS_PANEL, RADIUS_CONTROL,
    FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_MD
)


class OptionsCard(ctk.CTkFrame):
    """Compact card for click action and trigger mode."""

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
        ctk.CTkLabel(
            self,
            text=t('options_title').upper(),
            font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=10, pady=(8, 4))

        # Main controls row: Dropdowns on left, Mode Radios on right
        body_row = ctk.CTkFrame(self, fg_color="transparent")
        body_row.pack(fill="x", padx=10, pady=(0, 8))

        # Left side: Button selector + Type selector
        left_box = ctk.CTkFrame(body_row, fg_color="transparent")
        left_box.pack(side="left")

        self.btn_var = ctk.StringVar(value="left")
        self.btn_menu = ctk.CTkOptionMenu(
            left_box,
            variable=self.btn_var,
            values=[t('left'), t('right'), t('middle')],
            width=105,
            height=28,
            font=(FONT_FAMILY, FONT_SIZE_BASE, "bold"),
            fg_color=BG_PANEL_ALT,
            button_color=BORDER_SUBTLE,
            button_hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            dropdown_fg_color=BG_PANEL,
            dropdown_hover_color=BG_HOVER,
            dropdown_text_color=TEXT_MAIN,
            dropdown_font=(FONT_FAMILY, FONT_SIZE_SM),
            corner_radius=RADIUS_CONTROL
        )
        self.btn_menu.pack(side="left", padx=(0, 6))

        self.type_var = ctk.StringVar(value="single")
        self.type_menu = ctk.CTkOptionMenu(
            left_box,
            variable=self.type_var,
            values=[t('single'), t('double'), t('triple')],
            width=105,
            height=28,
            font=(FONT_FAMILY, FONT_SIZE_BASE, "bold"),
            fg_color=BG_PANEL_ALT,
            button_color=BORDER_SUBTLE,
            button_hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            dropdown_fg_color=BG_PANEL,
            dropdown_hover_color=BG_HOVER,
            dropdown_text_color=TEXT_MAIN,
            dropdown_font=(FONT_FAMILY, FONT_SIZE_SM),
            corner_radius=RADIUS_CONTROL
        )
        self.type_menu.pack(side="left")

        # Right side: Trigger Mode (Toggle / Hold)
        right_box = ctk.CTkFrame(body_row, fg_color="transparent")
        right_box.pack(side="right")

        self.mode_var = ctk.StringVar(value="toggle")
        self.on_mode_changed = None

        self.mode_toggle = ctk.CTkRadioButton(
            right_box,
            text=t('toggle'),
            variable=self.mode_var,
            value="toggle",
            font=(FONT_FAMILY, FONT_SIZE_BASE),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER,
            radiobutton_width=16,
            radiobutton_height=16,
            command=self._on_mode_radio_changed
        )
        self.mode_toggle.pack(side="left", padx=(0, 10))

        self.mode_hold = ctk.CTkRadioButton(
            right_box,
            text=t('hold'),
            variable=self.mode_var,
            value="hold",
            font=(FONT_FAMILY, FONT_SIZE_BASE),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER,
            radiobutton_width=16,
            radiobutton_height=16,
            command=self._on_mode_radio_changed
        )
        self.mode_hold.pack(side="left")

    def _on_mode_radio_changed(self):
        if self.on_mode_changed:
            self.on_mode_changed(self.mode_var.get())

    def get_button(self) -> str:
        val = self.btn_var.get()
        if val == t('right'): return 'right'
        if val == t('middle'): return 'middle'
        return 'left'

    def get_click_type(self) -> str:
        val = self.type_var.get()
        if val == t('double'): return 'double'
        if val == t('triple'): return 'triple'
        return 'single'

    def get_mode(self) -> str:
        return self.mode_var.get()

    def set_values(self, button: str, click_type: str, mode: str) -> None:
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
