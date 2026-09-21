import json
import os
from dataclasses import dataclass, field, asdict

@dataclass
class ClickerConfig:
    """Data class for storing AutoClicker Pro configuration."""
    interval_hours: int = 0
    interval_minutes: int = 0
    interval_seconds: int = 0
    interval_ms: int = 100
    mouse_button: str = 'left'
    click_type: str = 'single'
    hotkey: str = 'f6'
    macro_hotkey: str = 'f7'
    hotkey_mode: str = 'toggle'
    location_mode: str = 'cursor'
    fixed_x: int = 0
    fixed_y: int = 0
    repeat_mode: str = 'infinite'
    repeat_count: int = 100
    jitter_enabled: bool = False
    jitter_interval_pct: int = 10
    jitter_position_px: int = 3
    always_on_top: bool = False
    language: str = 'en'
    theme: str = 'dark'
    macro_steps: list = field(default_factory=list)
    macro_repeat_mode: str = 'count'
    macro_repeat_count: int = 1

    def get_total_interval_ms(self) -> int:
        """Calculate and return the total interval in milliseconds."""
        return (self.interval_hours * 3600000 +
                self.interval_minutes * 60000 +
                self.interval_seconds * 1000 +
                self.interval_ms)

    def to_dict(self) -> dict:
        """Serialize the configuration to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'ClickerConfig':
        """Deserialize from a dictionary, with defaults for missing keys."""
        field_names = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)

    def save_to_file(self, path: str):
        """Write the configuration to a JSON file."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=4)
        except Exception as e:
            print(f"Error saving config to {path}: {e}")

    @classmethod
    def load_from_file(cls, path: str) -> 'ClickerConfig':
        """Read configuration from a JSON file, handle missing file gracefully."""
        if not os.path.exists(path):
            return cls()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return cls.from_dict(data)
        except Exception as e:
            print(f"Error loading config from {path}: {e}")
            return cls()
