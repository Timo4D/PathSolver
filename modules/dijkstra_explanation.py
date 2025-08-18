from htmltools import TagList, tags
from localization import _

def get_dijkstra_explanation():
    """Get localized Dijkstra explanation content."""
    return TagList(
        tags.p(_("dijkstra_step_0")),
        tags.p(_("dijkstra_step_1")),
        tags.p(_("dijkstra_step_2")),
        tags.p(_("dijkstra_step_3")),
    )

# Create the Dijkstra explanation content - this will be updated when language changes
dijkstra_explanation = get_dijkstra_explanation()

def update_dijkstra_explanation():
    """Update the global dijkstra_explanation when language changes."""
    global dijkstra_explanation
    dijkstra_explanation = get_dijkstra_explanation()
