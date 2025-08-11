from htmltools import TagList, tags
from localization import _

def get_project_information():
    """Get localized project information content."""
    return TagList(
        tags.p(_("about_thesis")),
        tags.p(_("about_goal")),
        tags.p(_("about_functionality")),
        tags.p(_("about_usage")),
        tags.p(_("about_technology")),
        tags.p(_("about_research")),
        tags.p(_("about_connection")),
        tags.p(_("about_source"))
    )

# Create the project information content - this will be updated when language changes
project_information = get_project_information()

def update_project_information():
    """Update the global project_information when language changes."""
    global project_information
    project_information = get_project_information()
