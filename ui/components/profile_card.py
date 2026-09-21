"""Profile management bar component — Utilitarian / Technical redesign."""

import customtkinter as ctk
from typing import Callable, Optional
from i18n.localization import t
from ui.theme import (
    BG_PANEL, BG_PANEL_ALT, BG_HOVER, BORDER_SUBTLE,
    TEXT_MAIN, TEXT_MUTED, TEXT_DIM, ACCENT_ALERT,
    FONT_FAMILY, RADIUS_PANEL, RADIUS_CONTROL
)


class ProfileCard(ctk.CTkFrame):
    """Profile management bar for saving/loading/deleting profiles."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=RADIUS_PANEL,
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER_SUBTLE,
            **kwargs
        )

        self.on_save: Optional[Callable] = None
        self.on_save_as: Optional[Callable] = None
        self.on_load: Optional[Callable] = None
        self.on_delete: Optional[Callable] = None

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)

        # Label
        lbl = ctk.CTkLabel(
            self,
            text=t('profile').upper(),
            font=(FONT_FAMILY, 10, "bold"),
            text_color=TEXT_MUTED
        )
        lbl.grid(row=0, column=0, padx=(14, 8), pady=8, sticky="w")

        # Profile Dropdown
        self.profile_var = ctk.StringVar(value="")
        self.profile_menu = ctk.CTkOptionMenu(
            self,
            variable=self.profile_var,
            height=28,
            font=(FONT_FAMILY, 11, "bold"),
            fg_color=BG_PANEL_ALT,
            button_color=BG_PANEL_ALT,
            button_hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            corner_radius=RADIUS_CONTROL,
            command=self._on_profile_selected
        )
        self.profile_menu.grid(row=0, column=1, padx=4, pady=8, sticky="ew")

        # Action Buttons
        self.btn_save = ctk.CTkButton(
            self,
            text="SAVE",
            width=50,
            height=28,
            font=(FONT_FAMILY, 10, "bold"),
            fg_color=BG_PANEL_ALT,
            hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            command=self._handle_save
        )
        self.btn_save.grid(row=0, column=2, padx=3, pady=8)

        self.btn_save_as = ctk.CTkButton(
            self,
            text="+ NEW",
            width=50,
            height=28,
            font=(FONT_FAMILY, 10, "bold"),
            fg_color=BG_PANEL_ALT,
            hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            command=self._handle_save_as
        )
        self.btn_save_as.grid(row=0, column=3, padx=3, pady=8)

        self.btn_delete = ctk.CTkButton(
            self,
            text="DEL",
            width=42,
            height=28,
            font=(FONT_FAMILY, 10, "bold"),
            fg_color="transparent",
            hover_color=ACCENT_ALERT,
            text_color=TEXT_DIM,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            command=self._handle_delete
        )
        self.btn_delete.grid(row=0, column=4, padx=(3, 12), pady=8)

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
