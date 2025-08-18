# PathSolver Localization

This document describes the internationalization (i18n) features added to PathSolver, which now supports multiple languages including German.

## Features Added

### Language Support
- **English (en)**: Default language - all original text
- **German (de)**: Complete German translation of the user interface

### User Interface Changes
- **Language Selection**: Added to Settings page under "Display Settings"  
- **Real-time Switching**: Users can change language without restarting the app
- **Persistent Settings**: Language choice can be saved in configuration

## How to Use

### For End Users

1. **Change Language**: 
   - Navigate to the "Settings" tab
   - In the "Display Settings" section, select your preferred language from the "Application Language" dropdown
   - The interface will immediately update to show text in the selected language

2. **Available Languages**:
   - English (default)
   - Deutsch (German)

### For Developers

#### Architecture

The localization system is built around these key components:

```
localization/
├── __init__.py              # Main exports
├── i18n.py                  # Core I18n class
└── translations/
    ├── en.json              # English translations
    └── de.json              # German translations
```

#### Adding New Languages

1. Create a new JSON file in `localization/translations/` named with the language code (e.g., `fr.json` for French)

2. Copy the structure from `en.json` and translate all values:
```json
{
  "app_title": "PathSolver",
  "nav_start": "Démarrer",
  "nav_about": "À propos du projet",
  ...
}
```

3. Update the `get_available_languages()` function in `localization/i18n.py` to include the new language:
```python
languages = {
    "en": "English",
    "de": "Deutsch", 
    "fr": "Français"  # Add new language
}
```

#### Using Localized Text in Code

```python
from localization import _

# Simple text
ui.h1(_("settings_title"))

# Text with parameters
ui.p(_("language_changed", language="Deutsch"))
```

#### Translation Keys

All translation keys follow a consistent naming pattern:
- Navigation: `nav_*` (e.g., `nav_start`, `nav_settings`)
- UI Elements: descriptive names (e.g., `start_node`, `target_node`) 
- Error Messages: `error_*` (e.g., `error_invalid_input`)
- Step Titles: `step_*_title` (e.g., `step_0_title`)
- Settings: grouped by function (e.g., `display_settings`, `admin_settings`)

#### Key Components Modified

- **app.py**: Navigation tabs now use localized text
- **modules/state_manager.py**: Added language state management
- **modules/settings_ui.py**: Added language selector
- **modules/ui_components.py**: Updated UI components to use localized text
- **constants.py**: Added functions for localized constants

## Translation Coverage

The German translation includes:

### Navigation & Main Interface
- Navigation tabs (Start, About, Algorithm Info, Settings)
- Application title and headers
- Form labels (Start Node, Target Node, etc.)
- Button text (Previous Step, Next Step, etc.)

### Algorithm Interface  
- Step titles and explanations
- Algorithm progress messages
- Error messages and warnings
- Distance table headers

### Game Features
- Prediction game interface
- Difficulty levels and descriptions
- Scoring and feedback messages
- Game mode settings

### Settings Page
- All setting categories and options
- Help text and explanations
- Status messages and notifications
- Language selection interface

### Context Menus & Interactions
- Right-click menu options
- Node and edge editing prompts
- Confirmation dialogs
- Success/error notifications

## Testing

Run the localization test to verify all translations:

```bash
python3 test_localization.py
```

This will test:
- Loading of translation files
- English and German text rendering
- Error handling for missing keys
- Language switching functionality

## Configuration

The default language can be set in `config.json`:

```json
{
  "settings": {
    "language": "de"
  }
}
```

If no configuration exists, the system defaults to English.

## Future Enhancements

The localization system is designed for easy extension:

1. **Additional Languages**: Simply add new JSON files and update the language list
2. **Regional Variants**: Support for variants like `en-US` vs `en-GB`
3. **Pluralization**: Framework supports advanced plural rules
4. **Context-Aware Translations**: Different translations based on context
5. **Right-to-Left Languages**: CSS and layout adaptations for RTL languages

## Technical Notes

- **Encoding**: All translation files use UTF-8 encoding
- **Fallback**: Missing translations fall back to English, then to the translation key
- **Performance**: Translations are loaded once at startup and cached
- **Memory**: Minimal memory footprint - only active language is kept in memory
- **Reactivity**: Language changes trigger reactive UI updates throughout the app

The system handles missing translations gracefully and provides clear warnings in the console for developers.