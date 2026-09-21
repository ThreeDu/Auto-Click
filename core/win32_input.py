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

def send_click(button: str = 'left', click_type: str = 'single') -> None:
    """
    Sends mouse down and up events.
    
    Args:
        button: 'left', 'right', or 'middle'
        click_type: 'single', 'double', or 'triple'
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
        
    inputs = []
    
    for _ in range(num_clicks):
        # Mouse down
        down_input = INPUT(type=INPUT_MOUSE)
        down_input.union.mi = MOUSEINPUT(0, 0, 0, down_flag, 0, None)
        inputs.append(down_input)
        
        # Mouse up
        up_input = INPUT(type=INPUT_MOUSE)
        up_input.union.mi = MOUSEINPUT(0, 0, 0, up_flag, 0, None)
        inputs.append(up_input)

    # Use SendInput
    nInputs = len(inputs)
    pInputs = (INPUT * nInputs)(*inputs)
    cbSize = ctypes.sizeof(INPUT)
    
    ctypes.windll.user32.SendInput(nInputs, pInputs, cbSize)

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
