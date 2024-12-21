from shiny import App, ui

from modules.dijkstra_info import dijkstra_info
from modules.graph_ui import graph_ui, graph_ui_server
from modules.project_information import project_information

example_page = ui.page_fluid(
    ui.panel_title("Djikstra Shiny!"),
    ui.input_slider("n", "N", 0, 100, 20),
    ui.output_text_verbatim("txt"),
)

simple_plot = ui.page_fluid(
    ui.output_plot("plot")
)

simple_graph = ui.page_fluid(
    ui.output_plot("graph")
)

app_ui = ui.page_navbar(
    ui.nav_panel("Start", graph_ui()),
    ui.nav_panel("About the Project", project_information),
    ui.nav_panel("More about the Dijkstra-Algorithm", dijkstra_info),
    title= "The Dijkstra Algorithm"
)


def server(input, output, session):
    graph_ui_server(input, output, session)


app = App(app_ui, server)
