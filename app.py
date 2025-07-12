from shiny import App, render, ui

from modules.graph_ui import graph_ui, graph_ui_server

app_ui = ui.page_navbar(
    ui.nav_panel("Home", graph_ui()),
    ui.nav_panel("About the Project"),
    title="PathSolver",
)


def server(input, output, session):
    graph_ui_server(input, output, session)


app = App(app_ui, server)
