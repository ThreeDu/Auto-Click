"""Macro sequence workbench component — Utilitarian / Technical redesign."""

import customtkinter as ctk
from typing import Callable, Optional
from i18n.localization import t
from ui.theme import (
    BG_PANEL, BG_PANEL_ALT, BG_HOVER, BORDER_SUBTLE,
    TEXT_MAIN, TEXT_MUTED, TEXT_DIM, ACCENT_PRIMARY, ACCENT_PRIMARY_HOVER,
    ACCENT_ALERT, ACCENT_ALERT_HOVER, ACCENT_AMBER, ACCENT_CYAN,
    FONT_FAMILY, FONT_MONO, RADIUS_PANEL, RADIUS_CONTROL
)


class MacroCard(ctk.CTkFrame):
    """Pro-grade multi-point macro workbench for sequence automation."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=RADIUS_PANEL,
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER_SUBTLE,
            **kwargs
        )

        self.on_run_macro: Optional[Callable] = None
        self.on_stop_macro: Optional[Callable] = None
        self.on_record_start: Optional[Callable] = None
        self.on_record_stop: Optional[Callable] = None

        self.is_recording = False
        self.is_running = False
        self.step_rows = []

        self._build_ui()

    def _build_ui(self):
        # Header with sequence stats
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(14, 10))

        self.title_label = ctk.CTkLabel(
            header_frame,
            text=t('macro_title').upper(),
            font=(FONT_FAMILY, 12, "bold"),
            text_color=TEXT_MUTED
        )
        self.title_label.pack(side="left")

        self.stats_label = ctk.CTkLabel(
            header_frame,
            text="0 STEPS · 0 MS",
            font=(FONT_MONO, 11, "bold"),
            text_color=ACCENT_CYAN
        )
        self.stats_label.pack(side="right")

        # Action Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=16, pady=(0, 10))

        self.btn_add = ctk.CTkButton(
            toolbar,
            text=f"+ {t('add_step')}",
            height=28,
            font=(FONT_FAMILY, 11, "bold"),
            fg_color=BG_PANEL_ALT,
            hover_color=BG_HOVER,
            text_color=TEXT_MAIN,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            command=self._on_add_step_click
        )
        self.btn_add.pack(side="left", padx=(0, 6))

        self.btn_record = ctk.CTkButton(
            toolbar,
            text=f"● {t('record')}",
            height=28,
            font=(FONT_FAMILY, 11, "bold"),
            fg_color=BG_PANEL_ALT,
            hover_color=BG_HOVER,
            text_color=ACCENT_AMBER,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            command=self._toggle_record
        )
        self.btn_record.pack(side="left", padx=(0, 6))

        self.btn_clear = ctk.CTkButton(
            toolbar,
            text=t('clear_all'),
            height=28,
            font=(FONT_FAMILY, 11),
            fg_color="transparent",
            hover_color=BG_HOVER,
            text_color=TEXT_DIM,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            command=self._clear_all
        )
        self.btn_clear.pack(side="right")

        # Table Column Headers
        col_header = ctk.CTkFrame(self, height=24, fg_color=BG_PANEL_ALT, corner_radius=RADIUS_CONTROL)
        col_header.pack(fill="x", padx=16, pady=(0, 6))

        headers = [("#", 30), ("ACTION", 110), ("X", 55), ("Y", 55), ("DELAY", 65), ("", 30)]
        for label, width in headers:
            ctk.CTkLabel(
                col_header,
                text=label,
                font=(FONT_FAMILY, 10, "bold"),
                text_color=TEXT_DIM,
                width=width,
                anchor="center" if width <= 55 else "w"
            ).pack(side="left", padx=2)

        # Scrollable Steps Container
        self.steps_frame = ctk.CTkScrollableFrame(
            self,
            height=210,
            fg_color="transparent",
            corner_radius=RADIUS_CONTROL
        )
        self.steps_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        # Bottom Loop Control Row
        loop_frame = ctk.CTkFrame(self, fg_color="transparent")
        loop_frame.pack(fill="x", padx=16, pady=(0, 10))

        self.repeat_var = ctk.StringVar(value="count")

        rb_count = ctk.CTkRadioButton(
            loop_frame,
            text=f"{t('repeat')}:",
            variable=self.repeat_var,
            value="count",
            font=(FONT_FAMILY, 11),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER
        )
        rb_count.pack(side="left", padx=(0, 6))

        vcmd = (self.register(self.validate_number), '%P')
        self.repeat_count_entry = ctk.CTkEntry(
            loop_frame,
            width=55,
            height=26,
            font=(FONT_MONO, 11, "bold"),
            fg_color=BG_PANEL_ALT,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            text_color=TEXT_MAIN,
            justify="center",
            validate="key",
            validatecommand=vcmd
        )
        self.repeat_count_entry.insert(0, "1")
        self.repeat_count_entry.pack(side="left", padx=(0, 16))

        rb_infinite = ctk.CTkRadioButton(
            loop_frame,
            text=f"{t('repeat')} (∞ Continuous)",
            variable=self.repeat_var,
            value="infinite",
            font=(FONT_FAMILY, 11),
            text_color=TEXT_MAIN,
            fg_color=ACCENT_AMBER,
            hover_color=ACCENT_AMBER
        )
        rb_infinite.pack(side="left")

        # Tactical Run/Abort Button
        self.btn_run_stop = ctk.CTkButton(
            self,
            text=f"▶  {t('run_macro')} (F7)",
            height=42,
            font=(FONT_FAMILY, 13, "bold"),
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_PRIMARY_HOVER,
            text_color="#042F2E",
            corner_radius=RADIUS_CONTROL,
            command=self._toggle_run
        )
        self.btn_run_stop.pack(fill="x", padx=16, pady=(0, 14))

    def validate_number(self, p: str) -> bool:
        return str.isdigit(p) or p == ""

    def _on_add_step_click(self):
        self.add_step("click_left", 0, 0, 100)

    def add_step(self, action: str, x: int, y: int, delay_ms: int):
        idx = len(self.step_rows) + 1
        row_frame = ctk.CTkFrame(
            self.steps_frame,
            fg_color=BG_PANEL_ALT,
            corner_radius=RADIUS_CONTROL,
            height=34
        )
        row_frame.pack(fill="x", pady=2)

        idx_label = ctk.CTkLabel(
            row_frame,
            text=f"{idx:02d}",
            width=28,
            font=(FONT_MONO, 11, "bold"),
            text_color=TEXT_DIM
        )
        idx_label.pack(side="left", padx=4)

        action_var = ctk.StringVar(value=action)
        actions = ["click_left", "click_right", "click_middle", "move", "wait"]

        def action_changed(choice, r_frame=row_frame):
            self._update_row_state(r_frame)
            self._update_stats()

        action_dropdown = ctk.CTkOptionMenu(
            row_frame,
            values=actions,
            variable=action_var,
            width=110,
            height=26,
            font=(FONT_FAMILY, 11),
            fg_color=BG_PANEL,
            button_color=BG_PANEL,
            text_color=TEXT_MAIN,
            corner_radius=RADIUS_CONTROL,
            command=action_changed
        )
        action_dropdown.pack(side="left", padx=2)

        vcmd = (self.register(self.validate_number), '%P')

        x_entry = ctk.CTkEntry(
            row_frame,
            width=50,
            height=26,
            font=(FONT_MONO, 11),
            fg_color=BG_PANEL,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            text_color=TEXT_MAIN,
            justify="center",
            validate="key",
            validatecommand=vcmd
        )
        x_entry.insert(0, str(x))
        x_entry.pack(side="left", padx=2)

        y_entry = ctk.CTkEntry(
            row_frame,
            width=50,
            height=26,
            font=(FONT_MONO, 11),
            fg_color=BG_PANEL,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            text_color=TEXT_MAIN,
            justify="center",
            validate="key",
            validatecommand=vcmd
        )
        y_entry.insert(0, str(y))
        y_entry.pack(side="left", padx=2)

        delay_entry = ctk.CTkEntry(
            row_frame,
            width=55,
            height=26,
            font=(FONT_MONO, 11),
            fg_color=BG_PANEL,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_CONTROL,
            text_color=TEXT_MAIN,
            justify="center",
            validate="key",
            validatecommand=vcmd
        )
        delay_entry.insert(0, str(delay_ms))
        delay_entry.pack(side="left", padx=2)
        delay_entry.bind("<KeyRelease>", lambda e: self._update_stats())

        def on_delete(r=row_frame):
            r.destroy()
            self.step_rows = [row for row in self.step_rows if row['frame'] != r]
            self._reindex_rows()
            self._update_stats()

        del_btn = ctk.CTkButton(
            row_frame,
            text="×",
            width=24,
            height=24,
            font=(FONT_FAMILY, 12, "bold"),
            fg_color="transparent",
            hover_color=ACCENT_ALERT,
            text_color=TEXT_DIM,
            corner_radius=RADIUS_CONTROL,
            command=on_delete
        )
        del_btn.pack(side="right", padx=4)

        row_data = {
            'frame': row_frame,
            'label': idx_label,
            'action_var': action_var,
            'x_entry': x_entry,
            'y_entry': y_entry,
            'delay_entry': delay_entry
        }
        self.step_rows.append(row_data)
        self._update_row_state(row_frame)
        self._update_stats()

    def _update_row_state(self, row_frame):
        for row in self.step_rows:
            if row['frame'] == row_frame:
                if row['action_var'].get() == "wait":
                    row['x_entry'].configure(state="disabled", fg_color=BG_PANEL_ALT)
                    row['y_entry'].configure(state="disabled", fg_color=BG_PANEL_ALT)
                else:
                    row['x_entry'].configure(state="normal", fg_color=BG_PANEL)
                    row['y_entry'].configure(state="normal", fg_color=BG_PANEL)
                break

    def _reindex_rows(self):
        for i, row in enumerate(self.step_rows):
            row['label'].configure(text=f"{(i + 1):02d}")

    def _update_stats(self):
        count = len(self.step_rows)
        total_delay = 0
        for row in self.step_rows:
            try:
                total_delay += int(row['delay_entry'].get())
            except ValueError:
                pass
        self.stats_label.configure(text=f"{count} STEPS · {total_delay} MS")

    def get_steps(self) -> list[dict]:
        steps = []
        for row in self.step_rows:
            try:
                x = int(row['x_entry'].get()) if row['action_var'].get() != "wait" else 0
            except ValueError:
                x = 0
            try:
                y = int(row['y_entry'].get()) if row['action_var'].get() != "wait" else 0
            except ValueError:
                y = 0
            try:
                delay = int(row['delay_entry'].get())
            except ValueError:
                delay = 100

            steps.append({
                'action': row['action_var'].get(),
                'x': x,
                'y': y,
                'delay_ms': delay
            })
        return steps

    def set_steps(self, steps: list[dict]):
        self._clear_all(confirm=False)
        for s in steps:
            self.add_step(
                s.get('action', 'click_left'),
                s.get('x', 0),
                s.get('y', 0),
                s.get('delay_ms', 100)
            )

    def _clear_all(self, confirm=True):
        for row in self.step_rows:
            row['frame'].destroy()
        self.step_rows.clear()
        self._update_stats()

    def _toggle_record(self):
        if not self.is_recording:
            self.is_recording = True
            self.btn_record.configure(
                text=f"■ {t('stop')}",
                fg_color=ACCENT_ALERT,
                hover_color=ACCENT_ALERT_HOVER,
                text_color=TEXT_MAIN
            )
            if self.on_record_start:
                self.on_record_start()
        else:
            self.is_recording = False
            self.btn_record.configure(
                text=f"● {t('record')}",
                fg_color=BG_PANEL_ALT,
                hover_color=BG_HOVER,
                text_color=ACCENT_AMBER
            )
            if self.on_record_stop:
                self.on_record_stop()

    def _toggle_run(self):
        if not self.is_running:
            if self.on_run_macro:
                self.on_run_macro()
        else:
            if self.on_stop_macro:
                self.on_stop_macro()

    def get_repeat_mode(self) -> str:
        return self.repeat_var.get()

    def get_repeat_count(self) -> int:
        try:
            return int(self.repeat_count_entry.get())
        except ValueError:
            return 1

    def set_running(self, is_running: bool):
        self.is_running = is_running
        if is_running:
            self.btn_run_stop.configure(
                text=f"■  {t('stop_macro')} (F7)",
                fg_color=ACCENT_ALERT,
                hover_color=ACCENT_ALERT_HOVER,
                text_color=TEXT_MAIN
            )
        else:
            self.btn_run_stop.configure(
                text=f"▶  {t('run_macro')} (F7)",
                fg_color=ACCENT_PRIMARY,
                hover_color=ACCENT_PRIMARY_HOVER,
                text_color="#042F2E"
            )
