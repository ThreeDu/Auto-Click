"""Repeat conditions configuration card component — Utilitarian / Technical redesign."""

import customtkinter as ctk
from i18n.localization import t
from ui.theme import (
    BG_PANEL, BG_PANEL_ALT, BORDER_SUBTLE,
    TEXT_MAIN, TEXT_MUTED, TEXT_DIM, ACCENT_AMBER, ACCENT_CYAN,
    FONT_FAMILY, FONT_MONO, RADIUS_PANEL, RADIUS_CONTROL
)


class RepeatCard(ctk.CTkFrame):
    """Card for configuring click repetition limits and anti-bot jitter."""

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
            text=t('repeat_title').upper(),
            font=(FONT_FAMILY, 12, "bold"),
            text_color=TEXT_MUTED
        )
        self.title_label.pack(side="left")

        # Repeat Rule Selection
        self.mode_var = ctk.StringVar(value="infinite")

        repeat_row = ctk.CTkFrame(self, fg_color="transparent")
        repeat_row.pack(fill="x", padx=16, pady=(0, 10))

        self.infinite_rb = ctk.CTkRadioButton(
            repeat_row,
            text=t('until_stopped'),
            variable=self.mode_var,
            value="infinite",
            font=(FONT_FAMILY, 12),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER,
            command=self.toggle_count_input
        )
        self.infinite_rb.pack(side="left", padx=(0, 20))

        self.count_rb = ctk.CTkRadioButton(
            repeat_row,
            text=t('repeat_times'),
            variable=self.mode_var,
            value="count",
            font=(FONT_FAMILY, 12),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER,
            command=self.toggle_count_input
        )
        self.count_rb.pack(side="left", padx=(0, 8))

        vcmd = (self.register(self.validate_number), '%P')
        self.count_entry = ctk.CTkEntry(
            repeat_row,
            width=70,
            height=28,
            font=(FONT_MONO, 12, "bold"),
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

        # Hairline separator
        sep = ctk.CTkFrame(self, height=1, fg_color=BORDER_SUBTLE)
        sep.pack(fill="x", padx=16, pady=(4, 10))

        # Anti-Detection Jitter Section
        self.jitter_var = ctk.BooleanVar(value=False)
        self.jitter_cb = ctk.CTkCheckBox(
            self,
            text=f"{t('jitter_enable')} (Anti-Bot Randomizer)",
            variable=self.jitter_var,
            font=(FONT_FAMILY, 12, "bold"),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER,
            command=self.toggle_jitter_inputs
        )
        self.jitter_cb.pack(anchor="w", padx=16, pady=(0, 8))

        # Jitter Controls Container
        self.jitter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.jitter_frame.pack(fill="x", padx=16, pady=(0, 14))
        self.jitter_frame.grid_columnconfigure(1, weight=1)

        # Interval Jitter
        ctk.CTkLabel(
            self.jitter_frame,
            text=t('jitter_interval'),
            font=(FONT_FAMILY, 11),
            text_color=TEXT_MUTED
        ).grid(row=0, column=0, padx=(0, 10), pady=(0, 6), sticky="w")

        self.j_int_slider = ctk.CTkSlider(
            self.jitter_frame,
            from_=1, to=50, number_of_steps=49,
            height=16,
            button_color=ACCENT_CYAN,
            progress_color=ACCENT_CYAN,
            command=self.update_j_int_val
        )
        self.j_int_slider.grid(row=0, column=1, padx=(0, 10), pady=(0, 6), sticky="ew")

        self.j_int_val_label = ctk.CTkLabel(
            self.jitter_frame,
            text="±10%",
            font=(FONT_MONO, 11, "bold"),
            text_color=ACCENT_CYAN,
            width=45
        )
        self.j_int_val_label.grid(row=0, column=2, pady=(0, 6), sticky="e")
        self.j_int_slider.set(10)

        # Position Jitter
        ctk.CTkLabel(
            self.jitter_frame,
            text=t('jitter_position'),
            font=(FONT_FAMILY, 11),
            text_color=TEXT_MUTED
        ).grid(row=1, column=0, padx=(0, 10), sticky="w")

        self.j_pos_slider = ctk.CTkSlider(
            self.jitter_frame,
            from_=1, to=20, number_of_steps=19,
            height=16,
            button_color=ACCENT_CYAN,
            progress_color=ACCENT_CYAN,
            command=self.update_j_pos_val
        )
        self.j_pos_slider.grid(row=1, column=1, padx=(0, 10), sticky="ew")

        self.j_pos_val_label = ctk.CTkLabel(
            self.jitter_frame,
            text="±3 px",
            font=(FONT_MONO, 11, "bold"),
            text_color=ACCENT_CYAN,
            width=45
        )
        self.j_pos_val_label.grid(row=1, column=2, sticky="e")
        self.j_pos_slider.set(3)

        self.toggle_count_input()
        self.toggle_jitter_inputs()

    def validate_number(self, p: str) -> bool:
        """Validate numeric input."""
        return str.isdigit(p) or p == ""

    def toggle_count_input(self) -> None:
        """Enable/disable count input based on mode."""
        state = "normal" if self.mode_var.get() == "count" else "disabled"
        self.count_entry.configure(state=state)

    def toggle_jitter_inputs(self) -> None:
        """Enable/disable jitter inputs."""
        state = "normal" if self.jitter_var.get() else "disabled"
        self.j_int_slider.configure(state=state)
        self.j_pos_slider.configure(state=state)

    def update_j_int_val(self, val) -> None:
        self.j_int_val_label.configure(text=f"±{int(val)}%")

    def update_j_pos_val(self, val) -> None:
        self.j_pos_val_label.configure(text=f"±{int(val)} px")

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
