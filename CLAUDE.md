# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Windows-only auto clicker + mouse macro app (customtkinter GUI, pynput hotkeys, raw Win32 input via ctypes). README and some commit messages are in Vietnamese. No linter config or CI; `tests/` has unittest tests for the non-GUI code only.

## Commands

```bash
pip install -r requirements.txt   # customtkinter, pynput, pystray, Pillow
python main.py                    # run from source
build_nuitka.bat                  # build onefile AutoClicker.exe (Nuitka) into repo root
python -m unittest discover -s tests -v                    # all tests
python -m unittest discover -s tests -k TestProfileNames   # one test class
```

The built exe has no console: `print()` output and tracebacks go to `autoclicker.log` next to the exe (see `redirect_output_to_log` in `main.py`).

Build outputs (`main.build/`, `main.dist/`, `main.onefile-build/`, `*.exe`) and user data (`profiles/*.json`) are gitignored.

## Architecture

- **`main.py`** — entry point. Enforces single instance (named mutex + localhost socket on port 47829 that tells the running instance to `restore_window`), sets per-monitor DPI awareness *before* any GUI import, and resolves paths. `get_app_dir()` / `get_app_executable()` contain Nuitka-onefile / PyInstaller / script fallbacks — persistent files must live next to the exe, not in the onefile temp dir. `ui/app.py` imports these back from `main` to restart the app (used for language changes).
- **`config.py`** — `ClickerConfig` dataclass is the single settings schema. `from_dict` drops unknown keys and defaults missing ones, so adding a field is backward compatible with old profile JSON. `macro_steps` is stored as a list of plain dicts.
- **`profile_manager.py`** — profiles are `profiles/<name>.json`; `_last_session.json` is autosaved on close and loaded at startup. Falls back to `%APPDATA%\AutoClicker\profiles` if the app dir isn't writable.
- **`core/`** — UI-independent engines, each running a daemon thread with a `threading.Event` stop signal and `on_*` callbacks:
  - `ClickerEngine`: drift-compensated click loop, jitter, fixed position, restore cursor.
  - `MacroEngine`: runs `MacroStep(action, x, y, delay_ms)` lists; `delay_ms` is a *pre-action* delay. Copies steps at `start()` so UI edits don't affect a running macro.
  - `timer.py`: `timeBeginPeriod(1)` + hybrid sleep/busy-wait (`high_precision_sleep`) that checks the stop event. Use it instead of `time.sleep` in engine loops.
  - `win32_input.py`: `SendInput`-based clicks/moves; `hotkey_manager.py`: pynput global hotkeys (toggle/hold modes, separate macro hotkey) with `normalize_hotkey` for config strings like `f6` / `ctrl+shift+a`.
- **`ui/app.py`** (`AutoClickerApp`, the large file) — owns the engines, hotkey manager, tray, and cards in `ui/components/`. Data flow: `ClickerConfig` → `_load_config_to_ui()` → cards; cards → `_collect_config_from_ui()` → `_apply_config_to_engine()` before each start. A new setting must be wired through `ClickerConfig`, both of those methods, and the engine.
- **Threading rule**: engine, pynput, tray, and socket callbacks run off the Tk thread — they must marshal UI work via `self.after(0, ...)` (see `_setup_hotkeys`, `_on_click_update`).
- **`i18n/`** — `t(key)` looks up `strings_en.py` / `strings_vi.py` (returns the key if missing). Add every new UI string to both files. Changing language restarts the app.
- **Design** — `design.md` defines the locked visual system (dark obsidian palette, Segoe UI + Consolas numerals, no emojis); its tokens live in `ui/theme.py` as constants. Use those constants rather than hardcoded colors.
