"""
Global hotkey listener.
"""
from typing import Optional, Callable
from pynput import keyboard

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
        
        if self.mode == 'toggle':
            hotkeys = {}
            if self.hotkey and self.on_toggle:
                hotkeys[self.hotkey] = self.on_toggle
            if self.macro_hotkey and self.on_macro_toggle:
                hotkeys[self.macro_hotkey] = self.on_macro_toggle
                
            if hotkeys:
                self._listener = keyboard.GlobalHotKeys(hotkeys)
                self._listener.start()
        elif self.mode == 'hold':
            def on_press(key):
                try:
                    if hasattr(key, 'name') and str(key.name) == self.hotkey.strip('<>'):
                        if self.on_hold_start:
                            self.on_hold_start()
                    elif hasattr(key, 'char') and key.char == self.hotkey.strip('<>'):
                        if self.on_hold_start:
                            self.on_hold_start()
                except AttributeError:
                    pass
                    
            def on_release(key):
                try:
                    if hasattr(key, 'name') and str(key.name) == self.hotkey.strip('<>'):
                        if self.on_hold_stop:
                            self.on_hold_stop()
                    elif hasattr(key, 'char') and key.char == self.hotkey.strip('<>'):
                        if self.on_hold_stop:
                            self.on_hold_stop()
                except AttributeError:
                    pass
                    
            self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None

    def update_hotkey(self, new_hotkey: str, new_macro_hotkey: Optional[str] = None):
        self.hotkey = new_hotkey
        if new_macro_hotkey is not None:
            self.macro_hotkey = new_macro_hotkey
        
        if self._listener is not None:
            self.start()
