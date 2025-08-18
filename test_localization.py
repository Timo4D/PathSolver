#!/usr/bin/env python3
"""
Test script for PathSolver localization functionality.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from localization import get_text as _, set_language, get_available_languages

def test_localization():
    """Test the localization system."""
    print("PathSolver Localization Test")
    print("=" * 40)
    
    # Test available languages
    languages = get_available_languages()
    print(f"Available languages: {languages}")
    print()
    
    # Test English translations
    print("Testing English translations:")
    set_language('en')
    test_keys = [
        'app_title', 'nav_start', 'nav_about', 'nav_settings',
        'start_node', 'target_node', 'select_graph', 'distances_header',
        'prev_step', 'next_step', 'settings_title', 'display_settings'
    ]
    
    for key in test_keys:
        print(f"  {key}: {_(key)}")
    print()
    
    # Test German translations
    print("Testing German translations:")
    set_language('de')
    for key in test_keys:
        print(f"  {key}: {_(key)}")
    print()
    
    # Test error handling
    print("Testing missing translation:")
    print(f"  missing_key: {_('missing_key')}")
    print()
    
    print("All tests completed successfully!")

if __name__ == "__main__":
    test_localization()