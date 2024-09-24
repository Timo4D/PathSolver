from enum import Enum

import networkx as nx
import pandas as pd
from shiny import ui, render, reactive

from modules.djikstra_explanation import djikstra_explanation

distances_df = reactive.Value(pd.DataFrame(columns=["Node", "Distance"]))


class GraphType(Enum):
    RANDOM_GRAPH = "random_graph"
    KOOT_EXAMPLE_DEUTSCHLAND = "koot_example_deutschland"


def graph_ui():
    return ui.page_fluid(
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_selectize(
                    "selectize_graph",
                    "Select a Graph",
                    {GraphType.RANDOM_GRAPH.value: "Random Graph",
                     GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value: "Deutschland Beispiel"}
                ),
                ui.output_ui("random_graph_sliders"),
                ui.input_numeric("start_node", "Start Node", value=1),
                ui.input_numeric("target_node", "Target Node", value=2),
                ui.input_numeric("layout_seed", "Layout Seed", value=1),
            ),
            ui.output_ui("display_graph"),
            ui.output_data_frame("display_distances"),
            djikstra_explanation
        ),
    )


def generate_random_graph(n, k, p):
    G = nx.connected_watts_strogatz_graph(n, k, p)
    return G


def draw_graph(G, pos, start, target, weights=None):
    nx.draw_networkx_labels(G, pos)

    color_map = []
    for node in G:
        if node == start:
            color_map.append('tab:green')
        elif node == target:
            color_map.append('tab:red')
        else:
            color_map.append('tab:blue')

    nx.draw_networkx_edges(G, pos)
    nx.draw_networkx_nodes(G, pos, node_color=color_map)
    edge_labels = nx.get_edge_attributes(G, 'weight')

    # Draw the weight of the edges
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)


def graph_ui_server(input, output, session):
    graph_data = {
        "graph": nx.Graph(),
        "layout_seed": None,
    }

    def update_distances_df(graph, start_node):
        distances = nx.single_source_dijkstra_path_length(graph, start_node)
        df = pd.DataFrame(list(distances.items()), columns=["Node", "Distance"])
        distances_df.set(df)

    @output
    @render.data_frame
    def display_distances():
        return distances_df.get()

    @output
    @render.ui
    def display_graph():
        """Controls which graph is shown."""
        return ui.output_plot(input.selectize_graph())

    @output
    @render.ui
    def random_graph_sliders():
        if input.selectize_graph() == GraphType.RANDOM_GRAPH.value:
            return ui.TagList(
                ui.input_slider("n_slider", "Number of Nodes", 1, 30, 8),
                ui.input_slider("k_slider", "K", 2, 5, 3),
                ui.input_slider("p_slider", "P", 0, 1, 0.5),
            )

    @output
    @render.plot
    def koot_example_deutschland():
        edges = [
            (0, 6, 35), (0, 7, 224), (1, 2, 291), (1, 3, 128), (1, 4, 137),
            (2, 4, 292), (3, 5, 99), (3, 7, 112), (4, 6, 270), (5, 7, 151)
        ]

        node_labels = {
            0: "Berlin", 1: "Bremen", 2: "Düsseldorf", 3: "Hamburg",
            4: "Hannover", 5: "Kiel", 6: "Potsdam", 7: "Schwerin"
        }

        G = nx.Graph()
        for u, v, d in edges:
            G.add_edge(u, v, weight=d)

        pos = nx.spring_layout(G, seed=input.layout_seed())
        draw_graph(
            G,
            pos,
            input.start_node(),
            input.target_node(),
        )
        label_pos = {node: (coords[0], coords[1] - 0.12) for node, coords in pos.items()}
        update_distances_df(G, input.start_node())
        nx.draw_networkx_labels(G, label_pos, labels=node_labels)

    @output
    @render.plot
    def random_graph():
        redo_layout = False
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
            redo_layout = True

        if (graph_data["layout_seed"] is None
                or input.layout_seed() != graph_data["layout_seed"]
                or redo_layout):
            graph_data["pos"] = nx.spring_layout(graph_data["graph"], seed=input.layout_seed())
            graph_data["layout_seed"] = input.layout_seed()

        draw_graph(
            graph_data["graph"],
            graph_data["pos"],
            input.start_node(),
            input.target_node(),
        )
        update_distances_df(graph_data["graph"], input.start_node())
