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


def get_bundle_dir() -> str:
    """Get the bundle directory where internal resources/scripts are located."""
    if "NUITKA_ONEFILE_DIRECTORY" in os.environ:
        return os.environ["NUITKA_ONEFILE_DIRECTORY"]
    if getattr(sys, '_MEIPASS', None):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_app_dir() -> str:
    """Get the application directory (where the persistent files live, next to the exe or script)."""
    # 1. Check if compiled with Nuitka
    main_mod = sys.modules.get("__main__")
    compiled = getattr(main_mod, "__compiled__", getattr(sys, "__compiled__", globals().get("__compiled__")))
    if compiled is not None:
        if hasattr(compiled, "original_argv0") and compiled.original_argv0:
            candidate = os.path.dirname(os.path.abspath(compiled.original_argv0))
            if os.path.isdir(candidate):
                return candidate
        if hasattr(compiled, "containing_dir") and compiled.containing_dir:
            candidate = str(compiled.containing_dir)
            if os.path.isdir(candidate):
                return candidate

    if "NUITKA_ORIGINAL_ARGV0" in os.environ:
        cand = os.path.dirname(os.path.abspath(os.environ["NUITKA_ORIGINAL_ARGV0"]))
        if os.path.isdir(cand):
            return cand

    # 2. PyInstaller frozen
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))

    # 3. Standalone binary fallback via sys.argv[0]
    if sys.argv and sys.argv[0]:
        candidate = os.path.dirname(os.path.abspath(sys.argv[0]))
        if os.path.isdir(candidate):
            temp_dir = os.path.abspath(os.environ.get("TEMP", "")).lower()
            if not temp_dir or temp_dir not in candidate.lower():
                return candidate

    # 4. Running as python script
    return os.path.dirname(os.path.abspath(__file__))


def get_app_executable() -> tuple[str, list[str]]:
    """Returns (executable_path, args) for cleanly restarting the app."""
    # Nuitka onefile
    main_mod = sys.modules.get("__main__")
    compiled = getattr(main_mod, "__compiled__", getattr(sys, "__compiled__", globals().get("__compiled__")))
    if compiled is not None:
        if hasattr(compiled, "original_argv0") and compiled.original_argv0 and os.path.exists(compiled.original_argv0):
            return compiled.original_argv0, sys.argv[1:]

    if "NUITKA_ORIGINAL_ARGV0" in os.environ and os.path.exists(os.environ["NUITKA_ORIGINAL_ARGV0"]):
        return os.environ["NUITKA_ORIGINAL_ARGV0"], sys.argv[1:]

    if getattr(sys, 'frozen', False):
        return sys.executable, sys.argv[1:]

    if sys.argv and sys.argv[0] and os.path.exists(sys.argv[0]):
        candidate = os.path.abspath(sys.argv[0])
        temp_dir = os.path.abspath(os.environ.get("TEMP", "")).lower()
        if not temp_dir or temp_dir not in candidate.lower():
            return candidate, sys.argv[1:]

    exe_name = os.path.basename(sys.executable).lower()
    if exe_name.startswith("python"):
        return sys.executable, sys.argv
    else:
        return sys.executable, sys.argv[1:]


import socket
import threading

SINGLE_INSTANCE_PORT = 47829
_MUTEX_NAME = "AutoClicker_SingleInstance_Mutex_v1"
_ERROR_ALREADY_EXISTS = 0xB7


def acquire_single_instance_mutex():
    """Try to acquire a named mutex. Returns handle if first instance, None if already running."""
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    if kernel32.GetLastError() == _ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(mutex)
        return None
    return mutex


def try_signal_existing_instance() -> bool:
    """If an instance is already running, signals it to show its window and returns True."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(0.3)
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
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
    # Fast mutex check for single instance (< 0.05ms vs 300ms socket timeout)
    mutex_handle = acquire_single_instance_mutex()
    if mutex_handle is None:
        # Another instance running — try to signal it to show its window
        try_signal_existing_instance()
        print("AutoClicker is already running. Restored existing window.")
        sys.exit(0)

    # Set DPI awareness before any GUI operations
    enable_high_dpi_awareness()

    # Ensure bundle directory and app directory are in path for imports
    bundle_dir = get_bundle_dir()
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)

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

    instance_server = None
    try:
        # Create and run the application
        app = AutoClickerApp(config, profile_manager)
        instance_server = start_instance_server(app)
        app.instance_server = instance_server
        app.mainloop()
    except Exception:
        import traceback
        import tkinter.messagebox as mb
        mb.showerror("AutoClicker Error", f"Startup Error:\n\n{traceback.format_exc()}")
    finally:
        if instance_server:
            try:
                instance_server.close()
            except Exception:
                pass


if __name__ == '__main__':
    main()
