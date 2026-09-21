"""Profile management bar component — Compact & Utilitarian."""

import customtkinter as ctk
from typing import Callable, Optional
from i18n.localization import t
from ui.theme import (
    BG_PANEL, BG_PANEL_ALT, BG_HOVER, BORDER_SUBTLE,
    TEXT_MAIN, TEXT_MUTED, TEXT_DIM, ACCENT_ALERT,
    FONT_FAMILY, RADIUS_PANEL, RADIUS_CONTROL,
    FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_BASE
)


class ProfileCard(ctk.CTkFrame):
    """Compact profile management bar."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", RADIUS_PANEL)
        kwargs.setdefault("fg_color", BG_PANEL)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", BORDER_SUBTLE)
        kwargs.setdefault("height", 34)
        super().__init__(master, **kwargs)

        self.on_save: Optional[Callable] = None
        self.on_save_as: Optional[Callable] = None
        self.on_load: Optional[Callable] = None
        self.on_delete: Optional[Callable] = None

        self._build_ui()

    def _build_ui(self):
        lbl = ctk.CTkLabel(
            self,
            text=t('profile').upper(),
            font=(FONT_FAMILY, FONT_SIZE_XS, "bold"),
            text_color=TEXT_MUTED
        )
        lbl.pack(side="left", padx=(8, 4), pady=3)

        self.profile_var = ctk.StringVar(value="")
        self.profile_menu = ctk.CTkOptionMenu(
            self,
            variable=self.profile_var,
            width=95,
            height=26,
            font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            fg_color=BG_PANEL_ALT,
            button_color=BORDER_SUBTLE,
            button_hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            dropdown_fg_color=BG_PANEL,
            dropdown_hover_color=BG_HOVER,
            dropdown_text_color=TEXT_MAIN,
            dropdown_font=(FONT_FAMILY, FONT_SIZE_SM),
            corner_radius=RADIUS_CONTROL,
            command=self._on_profile_selected
        )
        self.profile_menu.pack(side="left", padx=2, pady=3)

        self.btn_save = ctk.CTkButton(
            self,
            text="SAVE",
            width=46,
            height=26,
            font=(FONT_FAMILY, FONT_SIZE_XS, "bold"),
            fg_color=BG_PANEL_ALT,
            hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            command=self._handle_save
        )
        self.btn_save.pack(side="left", padx=2, pady=3)

        self.btn_save_as = ctk.CTkButton(
            self,
            text="+NEW",
            width=48,
            height=26,
            font=(FONT_FAMILY, FONT_SIZE_XS, "bold"),
            fg_color=BG_PANEL_ALT,
            hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            command=self._handle_save_as
        )
        self.btn_save_as.pack(side="left", padx=2, pady=3)

        self.btn_delete = ctk.CTkButton(
            self,
            text="DEL",
            width=40,
            height=26,
            font=(FONT_FAMILY, FONT_SIZE_XS, "bold"),
            fg_color="transparent",
            hover_color=ACCENT_ALERT,
            text_color=TEXT_DIM,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            command=self._handle_delete
        )
        self.btn_delete.pack(side="right", padx=(2, 8), pady=3)

    def set_profiles(self, names: list[str], current: str):
        self.profile_menu.configure(values=names)
        self.profile_var.set(current)

    def get_selected_profile(self) -> str:
        return self.profile_var.get()

    def _on_profile_selected(self, choice: str):
        if self.on_load:
            self.on_load()

    def _handle_save(self):
        if self.on_save:
            self.on_save()

    def _handle_save_as(self):
        if self.on_save_as:
            self.on_save_as()

    def _handle_delete(self):
        if self.on_delete:
            self.on_delete()
