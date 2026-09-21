import pystray
from PIL import Image, ImageDraw
from i18n.localization import t
import threading
from typing import Callable, Optional

class TrayManager:
    def __init__(self, app):
        self.app = app
        self.icon = None
        self._create_icon_image()
        
        self.on_toggle_click: Optional[Callable] = None
        self.on_toggle_hud: Optional[Callable] = None
        
    def _create_icon_image(self):
        import os
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'icon.png')
        if os.path.exists(icon_path):
            try:
                self.image = Image.open(icon_path).resize((64, 64), Image.Resampling.LANCZOS)
                return
            except Exception:
                pass
        width = 64
        height = 64
        self.image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(self.image)
        draw.ellipse((8, 8, 56, 56), fill="#10B981")
        
    def start(self):
        menu = pystray.Menu(
            pystray.MenuItem(t('show_hide'), self._toggle_window, default=True),
            pystray.MenuItem(t('run_macro'), self._trigger_start_stop),
            pystray.MenuItem(t('mini_hud'), self._trigger_hud),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(t('exit'), self._exit_app)
        )
        
        self.icon = pystray.Icon("AutoClicker", self.image, "AutoClicker", menu)
        
        # Run icon in daemon thread
        self.thread = threading.Thread(target=self.icon.run, daemon=True)
        self.thread.start()
        
    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            
    def _toggle_window(self, icon=None, item=None):
        self.app.after(0, self._do_toggle_window)
        
    def _do_toggle_window(self):
        if hasattr(self.app, 'toggle_visibility'):
            self.app.toggle_visibility()
        elif self.app.state() == "withdrawn":
            self.app.deiconify()
        else:
            self.app.withdraw()
            
    def _trigger_start_stop(self, icon=None, item=None):
        if self.on_toggle_click:
            self.app.after(0, self.on_toggle_click)
            
    def _trigger_hud(self, icon=None, item=None):
        if self.on_toggle_hud:
            self.app.after(0, self.on_toggle_hud)
            
    def _exit_app(self, icon=None, item=None):
        self.stop()
        if hasattr(self.app, '_on_close'):
            self.app.after(0, self.app._on_close)
        else:
            self.app.after(0, self.app.destroy)

    def notify(self, title: str, message: str):
        """Show balloon notification if supported."""
        try:
            if self.icon and hasattr(self.icon, 'notify'):
                self.icon.notify(message, title)
        except Exception:
            pass

