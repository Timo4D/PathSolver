from typing import Any, Dict

from htmltools import HTMLDependency
from shiny import ui
from shiny.module import resolve_id
from shiny.render.renderer import Renderer

# Cytoscape.js core library
cytoscape_core_dep = HTMLDependency(
    name="cytoscape-core",
    version="3.26.0",
    source={"href": "https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/"},
    script={"src": "cytoscape.min.js"}
)

# Cytoscape cxtmenu extension
cytoscape_cxtmenu_dep = HTMLDependency(
    name="cytoscape-cxtmenu",
    version="3.5.0",
    source={"href": "https://unpkg.com/cytoscape-cxtmenu@3.5.0/"},
    script={"src": "cytoscape-cxtmenu.js"}
)

# Our custom component
cytoscape_dep = HTMLDependency(
    name="cytoscape",
    version="3.32.7",
    source={"subdir": "modules/cytoscape"},
    script={"src": "graph_component.js"},
)


class render_cytoscape(Renderer[Dict[str, Any]]):
    """
    Renders a networkx Graph with cytoscape
    """

    def auto_output_ui(self):
        return output_cytoscape_graph(self.output_name)
    
    async def transform(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """Transform the graph data for cytoscape rendering."""
        return value


def output_cytoscape_graph(id, height="400px"):
    return ui.div(
        cytoscape_core_dep,
        cytoscape_cxtmenu_dep,
        cytoscape_dep,
        id=resolve_id(id),
        class_="shiny-cytoscape-output",
        style=f"height: {height}",
    )
