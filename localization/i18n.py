"""
Internationalization (i18n) system for PathSolver.

This module provides translation support for multiple languages.
"""

import json
import os
from typing import Dict, Optional
from pathlib import Path


class I18n:
    """Internationalization class for handling translations."""
    
    def __init__(self, default_language: str = "en"):
        """Initialize the i18n system with a default language."""
        self.current_language = default_language
        self.default_language = default_language
        self.translations: Dict[str, Dict[str, str]] = {}
        self.localization_dir = Path(__file__).parent / "translations"
        
        # Load available translations
        self._load_translations()
    
    def _load_translations(self):
        """Load all available translation files."""
        if not self.localization_dir.exists():
            self.localization_dir.mkdir(exist_ok=True)
            return
        
        for file_path in self.localization_dir.glob("*.json"):
            language_code = file_path.stem
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.translations[language_code] = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Warning: Could not load translation file {file_path}: {e}")
    
    def set_language(self, language_code: str):
        """Set the current language."""
        if language_code in self.translations or language_code == self.default_language:
            self.current_language = language_code
        else:
            print(f"Warning: Language '{language_code}' not available. Using {self.current_language}")
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get a dictionary of available languages with their display names."""
        languages = {
            "en": "English",
            "de": "Deutsch",
            "zh": "中文"
        }
        
        # Only return languages that have translation files (or default)
        available = {"en": languages["en"]}  # English is always available as default
        for lang_code in self.translations.keys():
            if lang_code in languages:
                available[lang_code] = languages[lang_code]
        
        return available
    
    def get_text(self, key: str, **kwargs) -> str:
        """
        Get translated text for the given key.
        
        Args:
            key: The translation key
            **kwargs: Format arguments to be inserted into the translated text
        
        Returns:
            The translated text, or the key itself if no translation is found
        """
        # Try current language first
        if self.current_language in self.translations:
            text = self.translations[self.current_language].get(key)
            if text:
                try:
                    return text.format(**kwargs) if kwargs else text
                except KeyError as e:
                    print(f"Warning: Missing format argument {e} for key '{key}'")
                    return text
        
        # Fall back to default language if available
        if (self.current_language != self.default_language and 
            self.default_language in self.translations):
            text = self.translations[self.default_language].get(key)
            if text:
                try:
                    return text.format(**kwargs) if kwargs else text
                except KeyError as e:
                    print(f"Warning: Missing format argument {e} for key '{key}'")
                    return text
        
        # If no translation found, return the key itself
        print(f"Warning: No translation found for key '{key}' in language '{self.current_language}'")
        return key


# Global i18n instance
_i18n_instance = I18n()

def get_text(key: str, **kwargs) -> str:
    """Global function to get translated text."""
    return _i18n_instance.get_text(key, **kwargs)

def set_language(language_code: str):
    """Global function to set the current language."""
    _i18n_instance.set_language(language_code)

def get_available_languages() -> Dict[str, str]:
    """Global function to get available languages."""
    return _i18n_instance.get_available_languages()

def get_current_language() -> str:
    """Global function to get the current language."""
    return _i18n_instance.current_language