"""
Localization system for PathSolver application.

This module provides internationalization (i18n) support for the PathSolver
web application, allowing for multiple language support.
"""

from .i18n import I18n, get_text, set_language, get_available_languages, get_current_language

# Convenience alias
_ = get_text

__all__ = ['I18n', 'get_text', '_', 'set_language', 'get_available_languages', 'get_current_language']