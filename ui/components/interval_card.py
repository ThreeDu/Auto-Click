"""Interval configuration card component — Compact & Utilitarian."""

import customtkinter as ctk
from i18n.localization import t
from ui.theme import (
    BG_PANEL, BG_PANEL_ALT, BG_HOVER, BORDER_SUBTLE,
    TEXT_MAIN, TEXT_MUTED, TEXT_DIM, ACCENT_CYAN,
    FONT_FAMILY, FONT_MONO, RADIUS_PANEL, RADIUS_CONTROL,
    FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_MD
)


class IntervalCard(ctk.CTkFrame):
    """Compact precision interval configuration."""

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
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 4))

        self.title_label = ctk.CTkLabel(
            header,
            text=t('interval_title').upper(),
            font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            text_color=TEXT_MUTED
        )
        self.title_label.pack(side="left")

        self.freq_readout = ctk.CTkLabel(
            header,
            text="10.0 CPS (100ms)",
            font=(FONT_MONO, FONT_SIZE_SM, "bold"),
            text_color=ACCENT_CYAN
        )
        self.freq_readout.pack(side="right")

        # Main Row: Inputs + Presets side-by-side
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=10, pady=(0, 8))

        vcmd = (self.register(self.validate_number), '%P')

        # 4 inputs
        inputs_frame = ctk.CTkFrame(body, fg_color="transparent")
        inputs_frame.pack(side="left")

        self.entries = {}
        for key, label, default in [("hr", "H", "0"), ("min", "M", "0"), ("sec", "S", "0"), ("ms", "MS", "100")]:
            col = ctk.CTkFrame(inputs_frame, fg_color="transparent")
            col.pack(side="left", padx=(0, 4))

            ctk.CTkLabel(
                col, text=label, font=(FONT_FAMILY, FONT_SIZE_XS, "bold"), text_color=TEXT_DIM
            ).pack(pady=(0, 1))

            w = 58 if key == "ms" else 40
            entry = ctk.CTkEntry(
                col,
                width=w,
                height=28,
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
            entry.insert(0, default)
            entry.pack()
            entry.bind("<KeyRelease>", lambda e: self._on_entry_changed())
            self.entries[key] = entry

        self.hr_entry = self.entries["hr"]
        self.min_entry = self.entries["min"]
        self.sec_entry = self.entries["sec"]
        self.ms_entry = self.entries["ms"]

        # Presets on the right
        presets_frame = ctk.CTkFrame(body, fg_color="transparent")
        presets_frame.pack(side="right", fill="y", padx=(10, 0))

        ctk.CTkLabel(
            presets_frame, text="PRESET", font=(FONT_FAMILY, FONT_SIZE_XS, "bold"), text_color=TEXT_DIM
        ).pack(pady=(0, 1), anchor="e")

        pill_row = ctk.CTkFrame(presets_frame, fg_color="transparent")
        pill_row.pack(anchor="e")

        presets = [("10", 100), ("50", 20), ("100", 10), ("MAX", 1)]
        for text, ms in presets:
            btn = ctk.CTkButton(
                pill_row,
                text=text,
                width=38,
                height=28,
                font=(FONT_MONO, FONT_SIZE_SM, "bold"),
                fg_color=BG_PANEL_ALT,
                hover_color=BG_HOVER,
                text_color=TEXT_MAIN,
                border_color=BORDER_SUBTLE,
                border_width=1,
                corner_radius=RADIUS_CONTROL,
                command=lambda m=ms: self.apply_preset(m)
            )
            btn.pack(side="left", padx=2)

    def validate_number(self, p: str) -> bool:
        return str.isdigit(p) or p == ""

    def _on_entry_changed(self):
        hr, mn, sc, ms = self.get_values()
        total_ms = (hr * 3600000) + (mn * 60000) + (sc * 1000) + ms
        if total_ms <= 0:
            self.freq_readout.configure(text="MAX SPEED (1ms)")
        elif total_ms < 1000:
            cps = 1000.0 / total_ms
            self.freq_readout.configure(text=f"{cps:.1f} CPS ({total_ms}ms)")
        else:
            sec = total_ms / 1000.0
            self.freq_readout.configure(text=f"1 click / {sec:.1f}s")

    def apply_preset(self, ms: int) -> None:
        self.set_values(0, 0, 0, ms)

    def get_values(self) -> tuple[int, int, int, int]:
        try:
            hr = int(self.hr_entry.get()) if self.hr_entry.get() else 0
            mn = int(self.min_entry.get()) if self.min_entry.get() else 0
            sc = int(self.sec_entry.get()) if self.sec_entry.get() else 0
            ms = int(self.ms_entry.get()) if self.ms_entry.get() else 0
            return (hr, mn, sc, ms)
        except ValueError:
            return (0, 0, 0, 100)

    def set_values(self, hours: int, minutes: int, seconds: int, milliseconds: int) -> None:
        for entry, val in [
            (self.hr_entry, hours),
            (self.min_entry, minutes),
            (self.sec_entry, seconds),
            (self.ms_entry, milliseconds)
        ]:
            entry.delete(0, 'end')
            entry.insert(0, str(val))
        self._on_entry_changed()
