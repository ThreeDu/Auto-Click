# ⚡ AutoClicker Pro

A modern, high-performance desktop auto-clicker for Windows with multi-language support (EN/VI), macro recording, and customizable profiles.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

### Auto Click
- ⏱️ **Precise Interval Control** — Hours, Minutes, Seconds, Milliseconds
- 🎯 **CPS Presets** — Quick buttons for 10, 50, 100, Max CPS
- 🖱️ **Mouse Button** — Left, Right, Middle
- 👆 **Click Type** — Single, Double, Triple
- 📍 **Target Location** — Follow cursor or Fixed coordinate with Pick Location tool
- 🔁 **Repeat Mode** — Infinite or limited count
- 🎲 **Humanizer Jitter** — Randomize interval & position to avoid bot detection
- ⌨️ **Global Hotkey** — Toggle (F6) or Hold mode, works when minimized

### Macro
- 🔄 **Multi-Point Macro** — Create sequences of clicks at different positions
- 🔴 **Record Mode** — Record your clicks to create macros automatically
- ♻️ **Loop Control** — Run macros N times or infinitely

### Advanced
- 🌐 **Bilingual UI** — English / Tiếng Việt
- 🗔 **Mini HUD** — Floating overlay showing CPS & click count
- 📁 **Profile System** — Save/Load configurations as JSON profiles
- 🔽 **System Tray** — Minimize to tray, runs in background
- 📌 **Always on Top** — Keep window above other apps
- 🎨 **Dark/Light Theme** — Modern CustomTkinter UI

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Windows 10/11

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Auto-Click.git
cd Auto-Click

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Default Hotkeys

| Hotkey | Action |
|:---|:---|
| `F6` | Start/Stop Auto Click |
| `F7` | Start/Stop Macro |

## 📁 Project Structure

```
Auto-Click/
├── core/                    # Core engine modules
│   ├── win32_input.py       # Win32 SendInput wrapper (high-speed clicks)
│   ├── timer.py             # High-precision timer (1ms resolution)
│   ├── clicker_engine.py    # Auto-click worker thread
│   ├── macro_engine.py      # Multi-point macro runner
│   └── hotkey_manager.py    # Global hotkey listener (pynput)
├── ui/                      # GUI components (CustomTkinter)
│   ├── app.py               # Main application window & controller
│   ├── tray.py              # System tray integration (pystray)
│   └── components/          # UI cards
│       ├── interval_card.py # Click interval configuration
│       ├── options_card.py  # Mouse button & click type
│       ├── location_card.py # Target location & coordinate picker
│       ├── repeat_card.py   # Repeat rules & jitter settings
│       ├── macro_card.py    # Macro step editor & recorder
│       ├── profile_card.py  # Profile save/load bar
│       └── mini_hud.py      # Floating mini overlay
├── i18n/                    # Internationalization
│   ├── localization.py      # Translation engine
│   ├── strings_en.py        # English strings
│   └── strings_vi.py        # Vietnamese strings
├── profiles/                # Saved user profiles (JSON)
├── config.py                # Configuration dataclass
├── profile_manager.py       # Profile CRUD manager
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
└── build_nuitka.bat         # Build standalone .exe
```

## 🔧 Technical Details

- **Click Speed**: Up to 1000+ CPS using Win32 `SendInput` via `ctypes`
- **Timer Precision**: 1ms resolution via `winmm.timeBeginPeriod(1)` + hybrid busy-wait
- **High-DPI**: Per-Monitor DPI Aware v2 for accurate coordinates on 4K displays
- **Threading**: Isolated GUI, Engine, Hotkey, and Tray threads for responsive UI
- **Antivirus**: Build with Nuitka (native C compilation) to minimize false positives

## 📦 Building Standalone Executable

```bash
# Install Nuitka
pip install nuitka

# Build
build_nuitka.bat
```

The executable will be created at `main.dist/AutoClickerPro.exe`.

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.