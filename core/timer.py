"""
High-precision timer utilities.
"""
import time
import ctypes
from contextlib import contextmanager

# winmm library
winmm = ctypes.windll.winmm

def setup_timer_resolution():
    """Sets the timer resolution to 1ms."""
    winmm.timeBeginPeriod(1)

def restore_timer_resolution():
    """Restores the timer resolution."""
    winmm.timeEndPeriod(1)

def high_precision_sleep(duration_seconds: float):
    """
    Hybrid approach: time.sleep() for coarse wait, then busy-wait with time.perf_counter() 
    for sub-ms precision.
    """
    target = time.perf_counter() + duration_seconds
    
    # Coarse sleep if duration is long enough (>3ms)
    # Sleep duration minus a 2ms margin
    if duration_seconds > 0.003:
        time.sleep(duration_seconds - 0.002)
        
    # Busy wait for the remainder
    while time.perf_counter() < target:
        pass

@contextmanager
def timer_resolution():
    """Context manager for high precision timer."""
    setup_timer_resolution()
    try:
        yield
    finally:
        restore_timer_resolution()
