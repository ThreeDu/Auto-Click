"""
AutoClicker Pro — Entry Point
High-DPI aware, loads last session, launches main application.
"""
import ctypes
import sys
import os


def enable_high_dpi_awareness():
    """Set process DPI awareness for accurate coordinates on high-DPI displays."""
    try:
        # Per-Monitor DPI Aware v2 (Windows 10 1703+)
        ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)
    except Exception:
        try:
            # Per-Monitor DPI Aware (Windows 8.1+)
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                # System DPI Aware (Windows Vista+)
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def get_app_dir() -> str:
    """Get the application directory (where main.py lives)."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def main():
    """Application entry point."""
    # Set DPI awareness before any GUI operations
    enable_high_dpi_awareness()

    # Ensure app directory is in path for imports
    app_dir = get_app_dir()
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    # Import after path setup
    from config import ClickerConfig
    from profile_manager import ProfileManager
    from i18n.localization import set_language
    from ui.app import AutoClickerApp

    # Setup profiles directory
    profiles_dir = os.path.join(app_dir, 'profiles')
    profile_manager = ProfileManager(profiles_dir)

    # Load last session or defaults
    config = profile_manager.load_last_session()
    if config is None:
        config = ClickerConfig()

    # Apply saved language preference
    set_language(config.language)

    # Create and run the application
    app = AutoClickerApp(config, profile_manager)
    app.mainloop()


if __name__ == '__main__':
    main()
