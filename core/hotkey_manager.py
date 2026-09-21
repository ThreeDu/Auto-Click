"""
Global hotkey listener for AutoClicker.
Handles both special keys (F1-F24, Ctrl, Shift, Space, etc.) and alphanumeric keys.
"""
from typing import Optional, Callable
from pynput import keyboard


def normalize_hotkey(hotkey_str: str) -> str:
    """
    Normalizes hotkey string into pynput-compatible format.
    - Special keys (F1-F24, ctrl, alt, shift, space, enter, etc.) wrapped in <...>
    - Regular characters (a-z, 0-9) left as single characters
    - Combinations with '+' are split and each part normalized
    """
    if not hotkey_str:
        return ""

    s = hotkey_str.strip().lower()
    parts = [p.strip().strip('<>') for p in s.split('+') if p.strip()]
    if not parts:
        return ""

    key_members = keyboard.Key.__members__
    aliases = {
        'control': 'ctrl',
        'escape': 'esc',
        'return': 'enter',
        'del': 'delete',
        'ins': 'insert',
        'capslock': 'caps_lock'
    }

    normalized_parts = []
    for p in parts:
        p = aliases.get(p, p)
        if p in key_members:
            normalized_parts.append(f"<{p}>")
        elif len(p) == 1:
            normalized_parts.append(p)
        elif p.startswith('f') and p[1:].isdigit() and 1 <= int(p[1:]) <= 24:
            normalized_parts.append(f"<{p}>")
        else:
            normalized_parts.append(p)

    return "+".join(normalized_parts)


def is_valid_hotkey(hotkey_str: str) -> bool:
    """Checks if a hotkey string can be parsed by pynput."""
    if not hotkey_str:
        return False
    try:
        norm = normalize_hotkey(hotkey_str)
        if not norm:
            return False
        keyboard.HotKey.parse(norm)
        return True
    except Exception:
        return False



class HotkeyManager:
    """Global hotkey listener."""

    def __init__(self):
        self.hotkey = '<f6>'
        self.macro_hotkey = '<f7>'
        self.mode = 'toggle'  # 'toggle' or 'hold'

        self.on_toggle: Optional[Callable[[], None]] = None
        self.on_macro_toggle: Optional[Callable[[], None]] = None
        self.on_hold_start: Optional[Callable[[], None]] = None
        self.on_hold_stop: Optional[Callable[[], None]] = None

        self._listener: Optional[keyboard.Listener | keyboard.GlobalHotKeys] = None

    def start(self):
        self.stop()

        try:
            if self.mode == 'toggle':
                hotkeys = {}
                norm_click = normalize_hotkey(self.hotkey)
                norm_macro = normalize_hotkey(self.macro_hotkey)

                if norm_click and self.on_toggle:
                    hotkeys[norm_click] = self.on_toggle
                if norm_macro and self.on_macro_toggle:
                    hotkeys[norm_macro] = self.on_macro_toggle

                if hotkeys:
                    self._listener = keyboard.GlobalHotKeys(hotkeys)
                    self._listener.start()
            elif self.mode == 'hold':
                target_norm = normalize_hotkey(self.hotkey).strip('<>').lower()

                def on_press(key):
                    try:
                        k_name = getattr(key, 'name', None) or getattr(key, 'char', None)
                        if k_name and str(k_name).lower() == target_norm:
                            if self.on_hold_start:
                                self.on_hold_start()
                    except Exception:
                        pass

                def on_release(key):
                    try:
                        k_name = getattr(key, 'name', None) or getattr(key, 'char', None)
                        if k_name and str(k_name).lower() == target_norm:
                            if self.on_hold_stop:
                                self.on_hold_stop()
                    except Exception:
                        pass

                self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
                self._listener.start()
        except Exception as e:
            print(f"[HotkeyManager] Failed to start listener for hotkeys ({self.hotkey}, {self.macro_hotkey}): {e}")
            self._listener = None

    def stop(self):
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def update_hotkey(self, new_hotkey: str, new_macro_hotkey: Optional[str] = None) -> bool:
        norm_hk = normalize_hotkey(new_hotkey)
        if not is_valid_hotkey(norm_hk):
            return False

        if new_macro_hotkey is not None:
            norm_macro = normalize_hotkey(new_macro_hotkey)
            if not is_valid_hotkey(norm_macro):
                return False
            self.macro_hotkey = norm_macro

        self.hotkey = norm_hk
        self.start()
        return True

