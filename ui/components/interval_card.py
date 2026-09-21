"""Interval configuration card component — Utilitarian / Technical redesign."""

import customtkinter as ctk
from i18n.localization import t
from ui.theme import (
    BG_PANEL, BG_PANEL_ALT, BG_HOVER, BORDER_SUBTLE,
    TEXT_MAIN, TEXT_MUTED, TEXT_DIM, ACCENT_CYAN,
    FONT_FAMILY, FONT_MONO, RADIUS_PANEL, RADIUS_CONTROL
)


class IntervalCard(ctk.CTkFrame):
    """Card for configuring auto-click interval with precision instrumentation."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=RADIUS_PANEL,
            fg_color=BG_PANEL,
            border_width=1,
            border_color=BORDER_SUBTLE,
            **kwargs
        )

        # Header with technical title
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(14, 10))

        self.title_label = ctk.CTkLabel(
            header_frame,
            text=t('interval_title').upper(),
            font=(FONT_FAMILY, 12, "bold"),
            text_color=TEXT_MUTED
        )
        self.title_label.pack(side="left")

        # Calculated Frequency readout
        self.freq_readout = ctk.CTkLabel(
            header_frame,
            text="10.0 CPS (100ms)",
            font=(FONT_MONO, 11, "bold"),
            text_color=ACCENT_CYAN
        )
        self.freq_readout.pack(side="right")

        # Numeric entries grid
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="x", padx=16, pady=(0, 12))

        vcmd = (self.register(self.validate_number), '%P')

        # 4 units: HR, MIN, SEC, MS
        units = [
            ("hr", t('hours'), "0", 0),
            ("min", t('minutes'), "0", 1),
            ("sec", t('seconds'), "0", 2),
            ("ms", t('milliseconds'), "100", 3),
        ]

        self.entries = {}
        for key, label, default, col in units:
            cell = ctk.CTkFrame(grid_frame, fg_color="transparent")
            cell.grid(row=0, column=col, padx=(0 if col == 0 else 6, 0), sticky="ew")
            grid_frame.grid_columnconfigure(col, weight=1)

            lbl = ctk.CTkLabel(
                cell,
                text=label.upper(),
                font=(FONT_FAMILY, 10, "bold"),
                text_color=TEXT_DIM
            )
            lbl.pack(anchor="w", pady=(0, 3))

            entry = ctk.CTkEntry(
                cell,
                height=34,
                font=(FONT_MONO, 13, "bold"),
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
            entry.pack(fill="x")
            entry.bind("<KeyRelease>", lambda e: self._on_entry_changed())
            self.entries[key] = entry

        self.hr_entry = self.entries["hr"]
        self.min_entry = self.entries["min"]
        self.sec_entry = self.entries["sec"]
        self.ms_entry = self.entries["ms"]

        # CPS Quick Preset Pills
        preset_frame = ctk.CTkFrame(self, fg_color="transparent")
        preset_frame.pack(fill="x", padx=16, pady=(0, 14))

        preset_label = ctk.CTkLabel(
            preset_frame,
            text=t('cps_presets').upper(),
            font=(FONT_FAMILY, 10, "bold"),
            text_color=TEXT_DIM
        )
        preset_label.pack(side="left", padx=(0, 10))

        presets = [("10 CPS", 100), ("50 CPS", 20), ("100 CPS", 10), ("MAX (1ms)", 1)]
        for text, ms in presets:
            btn = ctk.CTkButton(
                preset_frame,
                text=text,
                height=26,
                font=(FONT_MONO, 11, "bold"),
                fg_color=BG_PANEL_ALT,
                hover_color=BG_HOVER,
                text_color=TEXT_MAIN,
                border_color=BORDER_SUBTLE,
                border_width=1,
                corner_radius=RADIUS_CONTROL,
                command=lambda m=ms: self.apply_preset(m)
            )
            btn.pack(side="left", padx=3)

    def validate_number(self, p: str) -> bool:
        """Validate numeric input."""
        return str.isdigit(p) or p == ""

    def _on_entry_changed(self):
        """Update live frequency readout."""
        hr, mn, sc, ms = self.get_values()
        total_ms = (hr * 3600000) + (mn * 60000) + (sc * 1000) + ms
        if total_ms <= 0:
            self.freq_readout.configure(text="MAX SPEED")
        elif total_ms < 1000:
            cps = 1000.0 / total_ms
            self.freq_readout.configure(text=f"{cps:.1f} CPS ({total_ms}ms)")
        else:
            sec = total_ms / 1000.0
            self.freq_readout.configure(text=f"1 click / {sec:.1f}s")

    def apply_preset(self, ms: int) -> None:
        """Apply preset milliseconds."""
        self.set_values(0, 0, 0, ms)
        self._on_entry_changed()

    def get_values(self) -> tuple[int, int, int, int]:
        """Get interval values (hr, min, sec, ms)."""
        try:
            hr = int(self.hr_entry.get()) if self.hr_entry.get() else 0
            mn = int(self.min_entry.get()) if self.min_entry.get() else 0
            sc = int(self.sec_entry.get()) if self.sec_entry.get() else 0
            ms = int(self.ms_entry.get()) if self.ms_entry.get() else 0
            return (hr, mn, sc, ms)
        except ValueError:
            return (0, 0, 0, 100)

    def set_values(self, hours: int, minutes: int, seconds: int, milliseconds: int) -> None:
        """Set interval values."""
        for entry, val in [
            (self.hr_entry, hours),
            (self.min_entry, minutes),
            (self.sec_entry, seconds),
            (self.ms_entry, milliseconds)
        ]:
            entry.delete(0, 'end')
            entry.insert(0, str(val))
        self._on_entry_changed()
