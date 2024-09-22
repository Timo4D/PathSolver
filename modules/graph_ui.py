import networkx as nx
from shiny import ui


def graph_ui():
    return ui.page_fluid(
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_slider("n_slider", "Number of Nodes", 1, 100, 15),
                ui.input_slider("k_slider", "K", 2, 5, 3),
                ui.input_slider("p_slider", "P", 0, 1, 0.5),
                ui.input_numeric("start_node", "Start Node", value=1),
                ui.input_numeric("target_node", "Target Node", value=1)

            ),
            ui.output_plot("graph_plot")
        ),
    )


def generate_random_graph(n, k, p):
    G = nx.connected_watts_strogatz_graph(n, k, p)
    return G


def draw_random_graph(G):
    pos = nx.spring_layout(G, seed=1)
    nx.draw_networkx_labels(G, pos)
    nx.draw(G, pos)
