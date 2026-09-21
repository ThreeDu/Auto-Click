"""
Hallmark Design System — Theme Tokens for AutoClicker
Genre: Modern-Minimal / Utilitarian Technical Instrument (Raycast / Linear / Hardware synth aesthetic)
"""

# Surface Palettes (Obsidian & Technical Zinc)
BG_BASE = "#0D0F12"        # Deepest obsidian background
BG_PANEL = "#15181E"       # Cards & decks surface
BG_PANEL_ALT = "#1A1E26"   # Nested containers / input wells
BG_HOVER = "#252B36"       # Hover states / Active menu item
BORDER_SUBTLE = "#252B36"  # Precision hairline border (1px)
BORDER_FOCUS = "#3B4455"   # Active/focused input borders

# Typography Inks
TEXT_MAIN = "#F3F4F6"      # Primary crisp text
TEXT_MUTED = "#94A3B8"     # Technical labels & meta
TEXT_DIM = "#64748B"       # Dim indicators & disabled text

# Accent Signals (Strictly restrained <= 5% viewport)
ACCENT_PRIMARY = "#10B981" # Emerald phosphor (active / running)
ACCENT_PRIMARY_HOVER = "#059669"
ACCENT_ALERT = "#EF4444"   # Signal red (stop / delete)
ACCENT_ALERT_HOVER = "#DC2626"
ACCENT_AMBER = "#F59E0B"   # Technical amber (recording / hotkeys)
ACCENT_AMBER_HOVER = "#D97706"
ACCENT_CYAN = "#0EA5E9"    # Electric cyan (macro steps & highlights)
ACCENT_CYAN_HOVER = "#0284C7"

# Font Stacks & Sizes (Enhanced Legibility)
FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"

FONT_SIZE_XS = 10     # Fine tags, small hints
FONT_SIZE_SM = 11     # Secondary labels, mini buttons
FONT_SIZE_BASE = 12   # Standard labels, card headers, options
FONT_SIZE_MD = 13     # Inputs, counters, readouts
FONT_SIZE_LG = 14     # Primary trigger buttons


# Metric Scales
RADIUS_PANEL = 8
RADIUS_CONTROL = 5
PADDING_CARD = 14


def apply_theme_patches():
    """
    Patch CustomTkinter global theme for CTkOptionMenu and DropdownMenu
    to ensure seamless consistency with the Obsidian Zinc dark aesthetic on Windows.
    Eliminates native white 3D bevel box border and unifies popup colors.
    """
    import sys
    import customtkinter as ctk

    # 1. Update global theme dictionary for all dropdown popups and buttons
    if "DropdownMenu" in ctk.ThemeManager.theme:
        ctk.ThemeManager.theme['DropdownMenu']['fg_color'] = [BG_PANEL, BG_PANEL]
        ctk.ThemeManager.theme['DropdownMenu']['hover_color'] = [BG_HOVER, BG_HOVER]
        ctk.ThemeManager.theme['DropdownMenu']['text_color'] = [TEXT_MAIN, TEXT_MAIN]

    if "CTkOptionMenu" in ctk.ThemeManager.theme:
        ctk.ThemeManager.theme['CTkOptionMenu']['fg_color'] = [BG_PANEL_ALT, BG_PANEL_ALT]
        ctk.ThemeManager.theme['CTkOptionMenu']['button_color'] = [BORDER_SUBTLE, BORDER_SUBTLE]
        ctk.ThemeManager.theme['CTkOptionMenu']['button_hover_color'] = [BG_HOVER, BG_HOVER]
        ctk.ThemeManager.theme['CTkOptionMenu']['text_color'] = [TEXT_MAIN, TEXT_MAIN]
        ctk.ThemeManager.theme['CTkOptionMenu']['corner_radius'] = RADIUS_CONTROL

    # 2. Patch DropdownMenu platform configuration to remove Windows white 3D bevel box
    try:
        import customtkinter.windows.widgets.core_widget_classes.dropdown_menu as dm
        orig_configure = dm.DropdownMenu._configure_menu_for_platforms

        def patched_configure(self):
            orig_configure(self)
            if sys.platform.startswith("win"):
                self.configure(
                    tearoff=False,
                    relief="flat",
                    borderwidth=0,
                    activeborderwidth=0,
                    bg=BG_PANEL,
                    fg=TEXT_MAIN,
                    activebackground=BG_HOVER,
                    activeforeground=TEXT_MAIN,
                    font=(FONT_FAMILY, FONT_SIZE_SM),
                    cursor="hand2"
                )

        dm.DropdownMenu._configure_menu_for_platforms = patched_configure
    except Exception as e:
        print(f"Failed to patch DropdownMenu: {e}")
