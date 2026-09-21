"""
Multi-point macro runner.
"""
import threading
from dataclasses import dataclass
from typing import Optional, Callable

from .win32_input import send_click, move_cursor
from .timer import setup_timer_resolution, restore_timer_resolution, high_precision_sleep

@dataclass
class MacroStep:
    action: str  # 'click_left', 'click_right', 'click_middle', 'move', 'wait'
    x: int
    y: int
    delay_ms: int

class MacroEngine:
    """Multi-point macro runner."""
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        
        self.steps: list[MacroStep] = []
        self.repeat_count = 0  # 0 = infinite
        
        self.total_iterations = 0
        
        self.on_step_update: Optional[Callable[[int, int], None]] = None
        self.on_stopped: Optional[Callable[[], None]] = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.is_running or not self.steps:
            return
        
        self._stop_event.clear()
        self.total_iterations = 0
        self._thread = threading.Thread(target=self._macro_loop, daemon=True)
        self._thread.start()

    def stop(self):
        if not self.is_running:
            return
            
        self._stop_event.set()
        if self._thread and self._thread != threading.current_thread():
            self._thread.join(timeout=0.5)
            self._thread = None

    def _macro_loop(self):
        setup_timer_resolution()
        try:
            while not self._stop_event.is_set():
                total_steps = len(self.steps)
                
                for i, step in enumerate(self.steps):
                    if self._stop_event.is_set():
                        break
                        
                    if self.on_step_update:
                        self.on_step_update(i + 1, total_steps)
                        
                    if step.action == 'move':
                        move_cursor(step.x, step.y)
                    elif step.action.startswith('click_'):
                        button = step.action.split('_')[1]
                        move_cursor(step.x, step.y)
                        send_click(button=button, click_type='single')
                        
                    if step.delay_ms > 0:
                        high_precision_sleep(step.delay_ms / 1000.0, stop_event=self._stop_event)
                        
                self.total_iterations += 1
                if self.repeat_count > 0 and self.total_iterations >= self.repeat_count:
                    break
        finally:
            restore_timer_resolution()
            if self.on_stopped:
                self.on_stopped()
