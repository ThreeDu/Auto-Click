"""Repeat conditions configuration card component — Compact & Utilitarian."""

import customtkinter as ctk
from i18n.localization import t
from ui.theme import (
    BG_PANEL, BG_PANEL_ALT, BORDER_SUBTLE,
    TEXT_MAIN, TEXT_MUTED, TEXT_DIM, ACCENT_AMBER, ACCENT_CYAN,
    FONT_FAMILY, FONT_MONO, RADIUS_PANEL, RADIUS_CONTROL,
    FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_MD
)


class RepeatCard(ctk.CTkFrame):
    """Compact card for repetition rules and anti-bot jitter."""

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
            text=f"{t('repeat_title').upper()} & JITTER",
            font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=10, pady=(8, 4))

        # Row 1: Repeat Rule
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(0, 4))

        self.mode_var = ctk.StringVar(value="infinite")

        self.infinite_rb = ctk.CTkRadioButton(
            row1,
            text=t('until_stopped'),
            variable=self.mode_var,
            value="infinite",
            font=(FONT_FAMILY, FONT_SIZE_BASE),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER,
            radiobutton_width=16,
            radiobutton_height=16,
            command=self.toggle_count_input
        )
        self.infinite_rb.pack(side="left", padx=(0, 14))

        self.count_rb = ctk.CTkRadioButton(
            row1,
            text=f"{t('repeat_times')}:",
            variable=self.mode_var,
            value="count",
            font=(FONT_FAMILY, FONT_SIZE_BASE),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER,
            radiobutton_width=16,
            radiobutton_height=16,
            command=self.toggle_count_input
        )
        self.count_rb.pack(side="left", padx=(0, 4))

        vcmd = (self.register(self.validate_number), '%P')
        self.count_entry = ctk.CTkEntry(
            row1,
            width=58,
            height=26,
            font=(FONT_MONO, FONT_SIZE_BASE, "bold"),
            fg_color=BG_PANEL_ALT,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            text_color=TEXT_MAIN,
            justify="center",
            validate="key",
            validatecommand=vcmd
        )
        self.count_entry.insert(0, "100")
        self.count_entry.pack(side="left")

        # Row 2: Anti-Detection Jitter
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(0, 8))

        self.jitter_var = ctk.BooleanVar(value=False)
        self.jitter_cb = ctk.CTkCheckBox(
            row2,
            text="Jitter:",
            variable=self.jitter_var,
            font=(FONT_FAMILY, FONT_SIZE_BASE, "bold"),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER,
            checkbox_width=16,
            checkbox_height=16,
            command=self.toggle_jitter_inputs
        )
        self.jitter_cb.pack(side="left", padx=(0, 6))

        # Sliders inline
        self.j_int_slider = ctk.CTkSlider(
            row2, from_=1, to=50, number_of_steps=49, width=70, height=14,
            button_color=ACCENT_CYAN, progress_color=ACCENT_CYAN,
            command=self.update_j_int_val
        )
        self.j_int_slider.pack(side="left", padx=(0, 2))

        self.j_int_val_label = ctk.CTkLabel(row2, text="±10%", font=(FONT_MONO, FONT_SIZE_XS, "bold"), text_color=ACCENT_CYAN, width=38)
        self.j_int_val_label.pack(side="left", padx=(0, 6))
        self.j_int_slider.set(10)

        self.j_pos_slider = ctk.CTkSlider(
            row2, from_=1, to=20, number_of_steps=19, width=60, height=14,
            button_color=ACCENT_CYAN, progress_color=ACCENT_CYAN,
            command=self.update_j_pos_val
        )
        self.j_pos_slider.pack(side="left", padx=(0, 2))

        self.j_pos_val_label = ctk.CTkLabel(row2, text="±3px", font=(FONT_MONO, FONT_SIZE_XS, "bold"), text_color=ACCENT_CYAN, width=35)
        self.j_pos_val_label.pack(side="left")
        self.j_pos_slider.set(3)

        self.toggle_count_input()
        self.toggle_jitter_inputs()

    def validate_number(self, p: str) -> bool:
        return str.isdigit(p) or p == ""

    def toggle_count_input(self) -> None:
        state = "normal" if self.mode_var.get() == "count" else "disabled"
        self.count_entry.configure(state=state)

    def toggle_jitter_inputs(self) -> None:
        state = "normal" if self.jitter_var.get() else "disabled"
        self.j_int_slider.configure(state=state)
        self.j_pos_slider.configure(state=state)

    def update_j_int_val(self, val) -> None:
        self.j_int_val_label.configure(text=f"±{int(val)}%")

    def update_j_pos_val(self, val) -> None:
        self.j_pos_val_label.configure(text=f"±{int(val)}px")

    def get_repeat_mode(self) -> str:
        return self.mode_var.get()

    def get_repeat_count(self) -> int:
        try:
            return int(self.count_entry.get()) if self.count_entry.get() else 0
        except ValueError:
            return 0

    def is_jitter_enabled(self) -> bool:
        return self.jitter_var.get()

    def get_jitter_values(self) -> tuple[int, int]:
        return (int(self.j_int_slider.get()), int(self.j_pos_slider.get()))

    def set_values(self, mode: str, count: int, jitter_enabled: bool, jitter_interval: int, jitter_position: int) -> None:
        self.mode_var.set(mode)
        self.count_entry.configure(state="normal")
        self.count_entry.delete(0, 'end')
        self.count_entry.insert(0, str(count))
        self.toggle_count_input()

        self.jitter_var.set(jitter_enabled)
        self.toggle_jitter_inputs()

        self.j_int_slider.set(jitter_interval)
        self.update_j_int_val(jitter_interval)

        self.j_pos_slider.set(jitter_position)
        self.update_j_pos_val(jitter_position)
