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

def high_precision_sleep(duration_seconds: float, stop_event=None):
    """
    Hybrid approach: time.sleep() for coarse wait, then busy-wait with time.perf_counter() 
    for sub-ms precision. Checks stop_event periodically for instant responsiveness.
    """
    target = time.perf_counter() + duration_seconds
    
    while duration_seconds > 0.003 and (stop_event is None or not stop_event.is_set()):
        remaining = target - time.perf_counter()
        if remaining <= 0.002:
            break
        # Sleep in small slices so stop_event is detected rapidly
        slice_time = min(0.02, remaining - 0.002)
        time.sleep(slice_time)
        
    # Busy wait for the sub-millisecond remainder
    while time.perf_counter() < target:
        if stop_event and stop_event.is_set():
            break

@contextmanager
def timer_resolution():
    """Context manager for high precision timer."""
    setup_timer_resolution()
    try:
        yield
    finally:
        restore_timer_resolution()
