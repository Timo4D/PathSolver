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
    version="3.33.0",
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
    resolved_id = resolve_id(id)
    return ui.div(
        cytoscape_core_dep,
        cytoscape_cxtmenu_dep,
        cytoscape_dep,
        ui.tags.style(f"""
            .resizable-cytoscape-container {{
                border: 2px solid #ddd;
                border-radius: 8px;
                position: relative;
                overflow: hidden;
                min-height: 300px;
                min-width: 400px;
                max-height: 800px;
                max-width: 100%;
                background: #f8f9fa;
            }}
            
            .resizable-cytoscape-container:hover {{
                border-color: #007bff;
            }}
            
            .shiny-cytoscape-output {{
                width: 100% !important;
                height: calc(100% - 18px) !important;
                border: none;
                border-radius: 6px 6px 0 0;
                display: block;
                box-sizing: border-box;
                position: relative;
                z-index: 1;
            }}
            
            .resize-handle {{
                position: absolute;
                background: #007bff;
                z-index: 1050;
                pointer-events: auto;
            }}
            
            .resize-handle:hover {{
                background: #0056b3;
            }}
            
            .resize-handle.bottom {{
                bottom: -2px;
                left: 2px;
                right: 2px;
                height: 14px;
                cursor: s-resize;
                border-radius: 0 0 6px 6px;
                transition: all 0.2s ease;
                border: 2px solid #007bff;
                border-top: none;
            }}
            
            .resize-handle.bottom:hover {{
                background: #0056b3 !important;
                height: 18px;
                bottom: -4px;
            }}
            
            .resize-handle.bottom::before {{
                content: "⋯";
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: white;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 6px;
                pointer-events: none;
            }}
            
            .resize-instructions {{
                position: absolute;
                top: 10px;
                right: 10px;
                background: rgba(0, 123, 255, 0.1);
                color: #007bff;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.3s ease;
            }}
            
            .resizable-cytoscape-container:hover .resize-instructions {{
                opacity: 1;
            }}
        """),
        ui.div(
            ui.div(
                id=resolved_id,
                class_="shiny-cytoscape-output",
                style=f"height: {height}",
            ),
            ui.div("Drag bottom edge to resize vertically", class_="resize-instructions"),
            ui.div(class_="resize-handle bottom"),
            class_="resizable-cytoscape-container",
            style=f"height: {height}; width: 100%;",
            id=f"{resolved_id}_container"
        )
    )
