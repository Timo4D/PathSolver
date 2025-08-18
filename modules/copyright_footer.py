from htmltools import TagList, tags

def copyright_footer():
    """Create a reusable copyright footer component."""
    return tags.footer(
        tags.hr(style="margin-top: 3rem; margin-bottom: 1rem;"),
        tags.p(
            "© 2025 Timo Gerstenhauer. ",
            tags.a("Licensed under GPL-3.0", href="https://www.gnu.org/licenses/gpl-3.0.html", target="_blank"),
            ".",
            style="text-align: center; color: #666; font-size: 0.9em; margin-bottom: 1rem;"
        ),
        style="margin-top: auto;"
    )