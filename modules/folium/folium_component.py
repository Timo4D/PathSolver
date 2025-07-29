"""Folium map component for Shiny integration."""

from typing import Any, Dict

from htmltools import HTMLDependency
from shiny import ui
from shiny.module import resolve_id
from shiny.render.renderer import Renderer

# Folium HTML dependency (Folium generates its own HTML with all dependencies)
folium_dep = HTMLDependency(
    name="folium",
    version="0.14.0",
    source={"subdir": "modules/folium"},
    script={"src": "folium_component.js"},
)


class render_folium(Renderer[str]):
    """
    Renders a Folium map with NetworkX graph overlay
    """

    def auto_output_ui(self):
        return output_folium_map(self.output_name)
    
    async def transform(self, value: str) -> str:
        """Transform the Folium HTML for rendering."""
        return value


def output_folium_map(id, height="350px"):
    """Create output container for Folium map."""
    return ui.div(
        folium_dep,
        id=resolve_id(id),
        class_="shiny-folium-output",
        style=f"height: {height}; width: 100%; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 60px; overflow: hidden;"
    )