from shiny import App, render, ui

from modules.graph_ui import graph_ui, draw_random_graph, generate_random_graph
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
    ui.nav_panel("Über den Algorithmus", simple_plot),
    ui.nav_panel("Über das Projekt", simple_graph),
    title="Djikstra",
    id="navbar"
)


def server(input, output, session):
    graph_data = {"graph": None}

    @render.plot
    def plot():
        return create_plot()

    @output
    @render.plot
    def graph():
        return create_graph()

    @output
    @render.plot
    def graph_plot():
        if (graph_data["graph"] is None
                or input.n_slider() != graph_data.get("n")
                or input.k_slider() != graph_data.get("k")
                or input.p_slider() != graph_data.get("p")):
            graph_data["graph"] = generate_random_graph(
                input.n_slider(),
                input.k_slider(),
                input.p_slider(),
            )
            graph_data["n"] = input.n_slider()
            graph_data["k"] = input.k_slider()
            graph_data["p"] = input.p_slider()

        draw_random_graph(
            graph_data["graph"],
            input.start_node(),
            input.target_node(),
            input.layout_seed()
        )

    @render.text
    def txt():
        return f"n*2 is {input.n() * 2}"


app = App(app_ui, server)
