"""Example Shiny for Python app with Cytoscape.js integration."""

from shiny import App, ui

from modules.dijkstra_info import dijkstra_info
from modules.graph_ui_cytoscape import cytoscape_graph_ui, cytoscape_graph_ui_server
from modules.project_information import project_information

# App UI with Cytoscape integration
app_ui = ui.page_navbar(
    ui.nav_panel("Dijkstra with Cytoscape", cytoscape_graph_ui()),
    ui.nav_panel("About the Project", project_information),
    ui.nav_panel("More about the Dijkstra-Algorithm", dijkstra_info),
    title="PathSolver with Cytoscape.js by Timo Gerstenhauer"
)


def server(input, output, session):
    """Server function with Cytoscape integration."""
    cytoscape_graph_ui_server(input, output, session)


app = App(app_ui, server)

if __name__ == "__main__":
    app.run()