from shiny import App, render, ui

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
    ui.nav_panel("Startseite", graph_ui()),
    ui.nav_panel("Über das Projekt", project_information),

    ui.nav_spacer(),
    ui.nav_control(ui.input_selectize(
        "select_lang",
        label=None,
        choices={
            "lang_ger": "German 🇩🇪",
            "lang_eng": "English 🇺🇸 🇬🇧"
        },
        selected="lang_ger",
        width="auto",
    )),
    # ui.nav_control(ui.input_dark_mode()),
    title= "The Dijkstra Algorithm"
)


def server(input, output, session):
    graph_ui_server(input, output, session)


app = App(app_ui, server)
