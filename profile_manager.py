import os
from typing import Optional
from config import ClickerConfig

class ProfileManager:
    """Manages saving, loading, and listing user profiles."""
    
    def __init__(self, profiles_dir: str):
        """Initialize the profile manager, creates directory if it doesn't exist."""
        self.profiles_dir = profiles_dir
        try:
            os.makedirs(self.profiles_dir, exist_ok=True)
            # Test write permission
            test_file = os.path.join(self.profiles_dir, '.write_test')
            with open(test_file, 'w') as f:
                f.write('ok')
            os.remove(test_file)
        except Exception:
            # Fallback to APPDATA if directory is read-only
            appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
            self.profiles_dir = os.path.join(appdata, 'AutoClicker', 'profiles')
            os.makedirs(self.profiles_dir, exist_ok=True)
            
    @staticmethod
    def is_valid_name(name: str) -> bool:
        """True if name is safe as a Windows filename and doesn't clash with internal files."""
        name = name.strip()
        if not name or len(name) > 64 or name.startswith('_') or name.endswith('.'):
            return False
        if any(c in '<>:"/\\|?*' or ord(c) < 32 for c in name):
            return False
        reserved = {'con', 'prn', 'aux', 'nul'} | {f'{p}{i}' for p in ('com', 'lpt') for i in range(1, 10)}
        return name.split('.')[0].lower() not in reserved

    def list_profiles(self) -> list[str]:
        """Returns a list of profile names (without .json extension)."""
        profiles = []
        if os.path.exists(self.profiles_dir):
            for file in os.listdir(self.profiles_dir):
                if file.endswith('.json') and file != '_last_session.json':
                    profiles.append(file[:-5])
        return sorted(profiles)
        
    def save_profile(self, name: str, config: ClickerConfig) -> bool:
        """Saves a profile to the profiles_dir/name.json. Returns False if the name is invalid or the write fails."""
        if not self.is_valid_name(name):
            return False
        path = os.path.join(self.profiles_dir, f"{name.strip()}.json")
        return config.save_to_file(path)
        
    def load_profile(self, name: str) -> ClickerConfig:
        """Loads a profile from the profiles directory."""
        path = os.path.join(self.profiles_dir, f"{name}.json")
        return ClickerConfig.load_from_file(path)
        
    def delete_profile(self, name: str):
        """Deletes a profile file from the profiles directory."""
        path = os.path.join(self.profiles_dir, f"{name}.json")
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError as e:
                print(f"Error deleting profile {name}: {e}")
                
    def save_last_session(self, config: ClickerConfig):
        """Saves the current configuration as _last_session.json."""
        path = os.path.join(self.profiles_dir, "_last_session.json")
        config.save_to_file(path)
        
    def load_last_session(self) -> Optional[ClickerConfig]:
        """Loads the last session config, returns None if it does not exist."""
        path = os.path.join(self.profiles_dir, "_last_session.json")
        if os.path.exists(path):
            return ClickerConfig.load_from_file(path)
        return None
