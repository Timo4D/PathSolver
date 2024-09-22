import networkx as nx
import matplotlib.pyplot as plt
from shiny import ui


def graph_ui():
    return ui.page_fluid(
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_slider("nodes", "Number of Nodes", 1, 100, 10),
                ui.input_slider("edges", "Number of Edges", 1, 100, 10),
                ui.input_slider("probability", "Number of Edges", 1, 100, 10),
                ui.input_numeric("start_node", "Start Node", value=1),
                ui.input_numeric("target_node", "Target Node", value=1)

            ),
            ui.output_plot("graph_plot")
        ),
    )
