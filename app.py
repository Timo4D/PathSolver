from shiny import App, render, ui
from shiny.templates.chat.production.openai.app_utils import app_dir

from modules.graph_ui import graph_ui, graph_ui_server
from modules.plot import create_plot
from modules.simple_graph import create_graph

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
    ui.nav_panel("Über das Projekt", simple_graph),

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

    @render.plot
    def plot():
        return create_plot()

    @output
    @render.plot
    def graph():
        return create_graph()


app = App(app_ui, server)
