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

        self._canonical_button = "left"
        self._canonical_click_type = "single"

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
            corner_radius=RADIUS_CONTROL,
            command=self._on_btn_selected
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
            corner_radius=RADIUS_CONTROL,
            command=self._on_type_selected
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

    def _on_btn_selected(self, choice: str):
        choice_lower = choice.strip().lower()
        if choice_lower in ('right', 'phải'):
            self._canonical_button = 'right'
        elif choice_lower in ('middle', 'giữa'):
            self._canonical_button = 'middle'
        else:
            self._canonical_button = 'left'

    def _on_type_selected(self, choice: str):
        choice_lower = choice.strip().lower()
        if choice_lower in ('double', 'đúp'):
            self._canonical_click_type = 'double'
        elif choice_lower in ('triple', 'ba'):
            self._canonical_click_type = 'triple'
        else:
            self._canonical_click_type = 'single'

    def _on_mode_radio_changed(self):
        if self.on_mode_changed:
            self.on_mode_changed(self.mode_var.get())

    def get_button(self) -> str:
        if hasattr(self, '_canonical_button'):
            return self._canonical_button
        val = self.btn_var.get().strip().lower()
        if val in ('right', 'phải'): return 'right'
        if val in ('middle', 'giữa'): return 'middle'
        return 'left'

    def get_click_type(self) -> str:
        if hasattr(self, '_canonical_click_type'):
            return self._canonical_click_type
        val = self.type_var.get().strip().lower()
        if val in ('double', 'đúp'): return 'double'
        if val in ('triple', 'ba'): return 'triple'
        return 'single'

    def get_mode(self) -> str:
        return self.mode_var.get()

    def set_values(self, button: str, click_type: str, mode: str) -> None:
        self._canonical_button = button if button in ('left', 'right', 'middle') else 'left'
        self._canonical_click_type = click_type if click_type in ('single', 'double', 'triple') else 'single'

        self.btn_var.set(t(self._canonical_button))
        self.type_var.set(t(self._canonical_click_type))
        self.mode_var.set(mode)
