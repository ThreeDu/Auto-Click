"""
Click engine worker thread.
"""
import threading
import time
import random
from typing import Optional, Callable

from .win32_input import send_click, move_cursor, get_cursor_pos
from .timer import setup_timer_resolution, restore_timer_resolution, high_precision_sleep

class ClickerEngine:
    """
    Click engine worker thread.
    """
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        
        # Config
        self.interval_ms = 100
        self.button = 'left'
        self.click_type = 'single'
        self.fixed_position: Optional[tuple[int, int]] = None
        self.repeat_count = 0  # 0 = infinite
        
        self.jitter_enabled = False
        self.jitter_interval_pct = 0.0
        self.jitter_position_px = 0
        
        # State
        self.click_count = 0
        
        # Callbacks
        self.on_click_update: Optional[Callable[[int], None]] = None
        self.on_stopped: Optional[Callable[[], None]] = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        """Starts the click loop in a daemon thread."""
        if self.is_running:
            return
            
        self._stop_event.clear()
        self.click_count = 0
        self._thread = threading.Thread(target=self._click_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops the click loop."""
        if not self.is_running:
            return
            
        self._stop_event.set()
        if self._thread:
            self._thread.join()
            self._thread = None

    def _click_loop(self):
        """Main click loop."""
        setup_timer_resolution()
        try:
            while not self._stop_event.is_set():
                # Position
                x, y = get_cursor_pos()
                if self.fixed_position:
                    x, y = self.fixed_position
                    
                if self.jitter_enabled and self.jitter_position_px > 0:
                    x += random.randint(-self.jitter_position_px, self.jitter_position_px)
                    y += random.randint(-self.jitter_position_px, self.jitter_position_px)
                    
                if self.fixed_position or self.jitter_enabled:
                    move_cursor(x, y)
                    
                # Click
                send_click(button=self.button, click_type=self.click_type)
                
                # Update count
                self.click_count += 1
                if self.on_click_update and self.click_count % 10 == 0:
                    self.on_click_update(self.click_count)
                    
                # Check limit
                if self.repeat_count > 0 and self.click_count >= self.repeat_count:
                    break
                    
                # Sleep
                if not self._stop_event.is_set():
                    sleep_ms = self.interval_ms
                    if self.jitter_enabled and self.jitter_interval_pct > 0:
                        variation = sleep_ms * self.jitter_interval_pct
                        sleep_ms = random.uniform(sleep_ms - variation, sleep_ms + variation)
                        
                    high_precision_sleep(max(0, sleep_ms) / 1000.0)
                    
        finally:
            restore_timer_resolution()
            if self.on_stopped:
                self.on_stopped()
