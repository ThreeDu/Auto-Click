"""
AutoClicker — Entry Point
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


import socket
import threading

SINGLE_INSTANCE_PORT = 47829


def try_signal_existing_instance() -> bool:
    """If an instance is already running, signals it to show its window and returns True."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(1.0)
        client.connect(('127.0.0.1', SINGLE_INSTANCE_PORT))
        client.sendall(b"SHOW\n")
        client.close()
        return True
    except Exception:
        return False


def start_instance_server(app):
    """Starts listening on single-instance port to bring window to front when triggered."""
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('127.0.0.1', SINGLE_INSTANCE_PORT))
        server.listen(2)

        def listen_loop():
            while True:
                try:
                    conn, _ = server.accept()
                    data = conn.recv(64)
                    if b"SHOW" in data:
                        app.after(0, app.restore_window)
                    conn.close()
                except Exception:
                    break

        t = threading.Thread(target=listen_loop, daemon=True)
        t.start()
        return server
    except Exception as e:
        print(f"Single instance server start failed: {e}")
        return None


def main():
    """Application entry point."""
    # Check if another instance is already running
    if try_signal_existing_instance():
        print("AutoClicker is already running. Restored existing window.")
        sys.exit(0)

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
    from ui.theme import apply_theme_patches
    from ui.app import AutoClickerApp

    # Apply global theme patches (fixes dropdown styling and removes Windows white border)
    apply_theme_patches()

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
    instance_server = start_instance_server(app)

    try:
        app.mainloop()
    finally:
        if instance_server:
            try:
                instance_server.close()
            except Exception:
                pass


if __name__ == '__main__':
    main()
