import os
from typing import Optional
from config import ClickerConfig

class ProfileManager:
    """Manages saving, loading, and listing user profiles."""
    
    def __init__(self, profiles_dir: str):
        """Initialize the profile manager, creates directory if it doesn't exist."""
        self.profiles_dir = profiles_dir
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir, exist_ok=True)
            
    def list_profiles(self) -> list[str]:
        """Returns a list of profile names (without .json extension)."""
        profiles = []
        if os.path.exists(self.profiles_dir):
            for file in os.listdir(self.profiles_dir):
                if file.endswith('.json') and file != '_last_session.json':
                    profiles.append(file[:-5])
        return sorted(profiles)
        
    def save_profile(self, name: str, config: ClickerConfig):
        """Saves a profile to the profiles_dir/name.json."""
        path = os.path.join(self.profiles_dir, f"{name}.json")
        config.save_to_file(path)
        
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
