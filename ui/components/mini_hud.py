"""Mini floating HUD component — Utilitarian / Technical redesign."""

import customtkinter as ctk
from typing import Optional, Callable
from i18n.localization import t
from ui.theme import (
    BG_BASE, BG_PANEL, BG_PANEL_ALT, BORDER_SUBTLE,
    TEXT_MAIN, TEXT_MUTED, TEXT_DIM, ACCENT_PRIMARY, ACCENT_ALERT, ACCENT_CYAN,
    FONT_FAMILY, FONT_MONO, RADIUS_CONTROL
)


class MiniHUD(ctk.CTkToplevel):
    """Floating draggable mini-instrument HUD for real-time monitoring over games."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.on_stop_clicked: Optional[Callable] = None

        # Window properties
        self.geometry("460x44+100+100")
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.94)

        # Drag tracking
        self._offset_x = 0
        self._offset_y = 0

        self._build_ui()
        self._bind_drag()

    def _build_ui(self):
        self.main_frame = ctk.CTkFrame(
            self,
            corner_radius=RADIUS_CONTROL,
            fg_color=BG_BASE,
            border_color=BORDER_SUBTLE,
            border_width=1
        )
        self.main_frame.pack(fill="both", expand=True)

        # Status indicator pill
        self.status_pill = ctk.CTkLabel(
            self.main_frame,
            text="● STANDBY",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=TEXT_DIM,
            width=80,
            anchor="w"
        )
        self.status_pill.pack(side="left", padx=(12, 6), pady=8)

        # CPS Readout
        self.cps_label = ctk.CTkLabel(
            self.main_frame,
            text="CPS: 0.0",
            font=(FONT_MONO, 12, "bold"),
            text_color=ACCENT_CYAN,
            width=90,
            anchor="center"
        )
        self.cps_label.pack(side="left", padx=4, pady=8)

        # Hairline separator
        sep = ctk.CTkFrame(self.main_frame, width=1, height=18, fg_color=BORDER_SUBTLE)
        sep.pack(side="left", padx=6, pady=10)

        # Click Count Readout
        self.clicks_label = ctk.CTkLabel(
            self.main_frame,
            text="CLICKS: 0",
            font=(FONT_MONO, 12, "bold"),
            text_color=TEXT_MAIN,
            anchor="w"
        )
        self.clicks_label.pack(side="left", fill="x", expand=True, padx=8, pady=8)

        # Stop Button
        self.btn_stop = ctk.CTkButton(
            self.main_frame,
            text=t('stop').upper(),
            width=55,
            height=26,
            font=(FONT_FAMILY, 10, "bold"),
            fg_color=ACCENT_ALERT,
            hover_color="#DC2626",
            text_color=TEXT_MAIN,
            corner_radius=RADIUS_CONTROL,
            command=self._on_stop
        )
        self.btn_stop.pack(side="right", padx=(4, 10), pady=8)

    def _bind_drag(self):
        for widget in [self.main_frame, self.status_pill, self.cps_label, self.clicks_label]:
            widget.bind("<Button-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._do_drag)

    def _start_drag(self, event):
        self._offset_x = event.x_root - self.winfo_x()
        self._offset_y = event.y_root - self.winfo_y()

    def _do_drag(self, event):
        x = event.x_root - self._offset_x
        y = event.y_root - self._offset_y
        self.geometry(f"+{x}+{y}")

    def update_status(self, is_running: bool, cps: float, click_count: int):
        if is_running:
            self.status_pill.configure(text="● RUNNING", text_color=ACCENT_PRIMARY)
            self.cps_label.configure(text=f"CPS: {cps:.1f}")
            self.clicks_label.configure(text=f"CLICKS: {click_count:,}")
        else:
            self.status_pill.configure(text="● STANDBY", text_color=TEXT_DIM)
            self.cps_label.configure(text="CPS: 0.0")
            self.clicks_label.configure(text=f"CLICKS: {click_count:,}")

    def _on_stop(self):
        if self.on_stop_clicked:
            self.on_stop_clicked()

    def toggle(self):
        if self.winfo_viewable():
            self.withdraw()
        else:
            self.deiconify()
            self.lift()
