from typing import Any, Dict

from htmltools import HTMLDependency
from shiny import ui
from shiny.module import resolve_id
from shiny.render.renderer import Renderer

cytoscape_dep = HTMLDependency(
    name="cytoscape",
    version="3.32.3",
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
        cytoscape_dep,
        id=resolve_id(id),
        class_="shiny-cytoscape-output",
        style=f"height: {height}",
    )
