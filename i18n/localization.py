from .strings_en import STRINGS as STRINGS_EN
from .strings_vi import STRINGS as STRINGS_VI

_current_language: str = 'en'

_LANGUAGES = {
    'en': STRINGS_EN,
    'vi': STRINGS_VI
}

def set_language(lang: str):
    """Sets the current language ('en' or 'vi')."""
    global _current_language
    if lang in _LANGUAGES:
        _current_language = lang

def get_language() -> str:
    """Returns the current language code."""
    return _current_language

def t(key: str) -> str:
    """
    Returns the translated string for the current language.
    If the key is not found, returns the key itself as a fallback.
    """
    strings = _LANGUAGES.get(_current_language, STRINGS_EN)
    return strings.get(key, key)

def get_available_languages() -> list[tuple[str, str]]:
    """Returns a list of available languages as (code, name) tuples."""
    return [('en', 'English'), ('vi', 'Tiếng Việt')]
