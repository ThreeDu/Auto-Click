"""
Win32 SendInput wrapper using ctypes.
"""
import ctypes
from ctypes import wintypes
import time

# Win32 Constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_ABSOLUTE = 0x8000

# ctypes Structures
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]

class _INPUTunion(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", _INPUTunion)
    ]

class POINT(ctypes.Structure):
    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG)
    ]

def _precise_hold(duration_seconds: float):
    """Sub-millisecond precision hold using perf_counter busy-wait.
    Used for short hold durations (1-20ms) where time.sleep is too inaccurate."""
    target = time.perf_counter() + duration_seconds
    while time.perf_counter() < target:
        pass

def send_click(button: str = 'left', click_type: str = 'single', hold_ms: int = 0) -> None:
    """
    Sends mouse down and up events.
    
    Args:
        button: 'left', 'right', or 'middle'
        click_type: 'single', 'double', or 'triple'
        hold_ms: Milliseconds to hold button down before release (default 0 for instant CPS, >0 for macro reliability)
    """
    down_flag = MOUSEEVENTF_LEFTDOWN
    up_flag = MOUSEEVENTF_LEFTUP
    
    if button == 'right':
        down_flag = MOUSEEVENTF_RIGHTDOWN
        up_flag = MOUSEEVENTF_RIGHTUP
    elif button == 'middle':
        down_flag = MOUSEEVENTF_MIDDLEDOWN
        up_flag = MOUSEEVENTF_MIDDLEUP
        
    num_clicks = 1
    if click_type == 'double':
        num_clicks = 2
    elif click_type == 'triple':
        num_clicks = 3
        
    cbSize = ctypes.sizeof(INPUT)

    for i in range(num_clicks):
        down_input = INPUT(type=INPUT_MOUSE)
        down_input.union.mi = MOUSEINPUT(0, 0, 0, down_flag, 0, None)

        up_input = INPUT(type=INPUT_MOUSE)
        up_input.union.mi = MOUSEINPUT(0, 0, 0, up_flag, 0, None)

        if hold_ms > 0:
            pDown = (INPUT * 1)(down_input)
            ctypes.windll.user32.SendInput(1, pDown, cbSize)
            _precise_hold(hold_ms / 1000.0)
            pUp = (INPUT * 1)(up_input)
            ctypes.windll.user32.SendInput(1, pUp, cbSize)
        else:
            pBoth = (INPUT * 2)(down_input, up_input)
            ctypes.windll.user32.SendInput(2, pBoth, cbSize)

        if i < num_clicks - 1:
            time.sleep(0.02)

def move_cursor(x: int, y: int) -> None:
    """
    Moves cursor to absolute screen coordinates.
    """
    ctypes.windll.user32.SetCursorPos(int(x), int(y))

def get_cursor_pos() -> tuple[int, int]:
    """
    Returns current cursor position.
    """
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y
