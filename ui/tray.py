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
        width = 64
        height = 64
        self.image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(self.image)
        draw.ellipse((8, 8, 56, 56), fill="#3B8ED0")
        
    def start(self):
        menu = pystray.Menu(
            pystray.MenuItem(t('show_hide'), self._toggle_window),
            pystray.MenuItem(t('run_macro'), self._trigger_start_stop),
            pystray.MenuItem(t('mini_hud'), self._trigger_hud),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(t('exit'), self._exit_app)
        )
        
        self.icon = pystray.Icon("AutoClickerPro", self.image, "AutoClicker Pro", menu)
        
        # Run icon in daemon thread
        self.thread = threading.Thread(target=self.icon.run, daemon=True)
        self.thread.start()
        
    def stop(self):
        if self.icon:
            self.icon.stop()
            
    def _toggle_window(self, icon, item):
        # We need to run this in the main thread
        self.app.after(0, self._do_toggle_window)
        
    def _do_toggle_window(self):
        if self.app.state() == "withdrawn":
            self.app.deiconify()
        else:
            self.app.withdraw()
            
    def _trigger_start_stop(self, icon, item):
        if self.on_toggle_click:
            self.app.after(0, self.on_toggle_click)
            
    def _trigger_hud(self, icon, item):
        if self.on_toggle_hud:
            self.app.after(0, self.on_toggle_hud)
            
    def _exit_app(self, icon, item):
        self.stop()
        self.app.after(0, self.app.destroy)
        
    def setup_close_override(self, root):
        def on_closing():
            root.withdraw()
        root.protocol("WM_DELETE_WINDOW", on_closing)
