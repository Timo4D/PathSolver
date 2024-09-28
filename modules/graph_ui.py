import random
from enum import Enum

import networkx as nx
import pandas as pd
from shiny import ui, render, reactive

from modules.djikstra_explanation import djikstra_explanation

distances_df = reactive.Value(pd.DataFrame())
graph = reactive.Value(nx.Graph())
seed = reactive.Value(1)
step_counter = reactive.Value(0)


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
                     GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value: "Deutschland Beispiel"},
                    selected=GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value
                ),
                ui.output_ui("random_graph_sliders"),
                ui.input_numeric("start_node", "Start Node", value=0, min=0),
                ui.input_numeric("target_node", "Target Node", value=1, min=0),
                ui.input_numeric("layout_seed", "Layout Seed", value=1, min=0),
            ),
            ui.input_action_button("next_step", "Next Step"),
            ui.output_plot("graph_plot"),
            ui.output_data_frame("display_distances"),
            djikstra_explanation
        ),
    )


def reset_df():
    print("reset_df")
    G = graph.get()
    if G:
        if "label" in G.nodes[0]:
            nodes = dict(sorted(nx.get_node_attributes(G, "label").items())).values()
            index_name = "Cities"
        else:
            nodes = [str(node) for node in G.nodes]
            index_name = "Node"

        distance_matrix = pd.DataFrame(float('inf'), index=nodes, columns=nodes)
        distance_matrix.index.name = index_name
        distance_matrix.reset_index(inplace=True)
        distances_df.set(distance_matrix)
        step_counter.set(0)


def init_df():
    print("init df")
    reset_df()


def graph_ui_server(input, output, session):
    @reactive.Effect
    @reactive.event(input.next_step)
    def next_step():
        print("next step")
        df = distances_df.get()
        if not df.empty:
            start_node = input.start_node()
            if 0 <= start_node < len(df):
                df.iloc[start_node, start_node + 1] = 1
                distances_df.set(df)
                print(f"Updated distance for node {start_node} to 1")
                step_counter.set(step_counter.get() + 1)
                # print(df)
            else:
                print(f"Invalid start node: {start_node}")

    @reactive.Effect
    def update_graph():
        if input.selectize_graph() == GraphType.RANDOM_GRAPH.value:
            generate_random_graph()
        elif input.selectize_graph() == GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value:
            generate_koot_example()

    @output
    @render.data_frame
    @reactive.event(distances_df, step_counter, input.start_node, input.target_node)
    def display_distances():
        df = distances_df.get()
        if df.empty or df.shape[1] < 2:
            return render.DataGrid(df)

        return render.DataGrid(
            df,
            styles=[
                # Bold the first column
                {
                    "cols": [0],
                    "style": {"font-weight": "bold"},
                },
                # Highlight start node green
                {
                    "rows": [input.start_node()],
                    "cols": [input.start_node() + 1],
                    "style": {"background-color": "#2ca02c"},
                },
                # Highlight target node red
                {
                    "rows": [input.target_node()],
                    "cols": [input.target_node() + 1],
                    "style": {"background-color": "#d62728"},
                },
            ]
        )

    @reactive.Effect
    @reactive.event(input.target_node, input.start_node)
    def reset_djikstra():
        print("reset djikstra")
        reset_df()


    @reactive.Effect
    def initialize_distances():
        print("update distances")
        init_df()

    def generate_random_graph():
        print("random")
        n = input.n_slider()
        k = input.k_slider()
        p = input.p_slider()

        G = nx.connected_watts_strogatz_graph(n, k, p)

        # Add random integer weights to edges
        for (u, v) in G.edges():
            G[u][v]['weight'] = random.randint(1, 100)

        graph.set(G)

    def generate_koot_example():

        print("koot")
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

        nx.set_node_attributes(G, node_labels, "label")
        graph.set(G)

    @output
    @render.ui
    def random_graph_sliders():
        if input.selectize_graph() == GraphType.RANDOM_GRAPH.value:
            return ui.TagList(
                ui.input_slider("n_slider", "Number of Nodes", 2, 30, 8),
                ui.input_slider("k_slider", "K", 2, 5, 3),
                ui.input_slider("p_slider", "P", 0, 1, 0.5),
            )

    @output
    @render.plot
    @reactive.event(input.selectize_graph, graph, input.layout_seed, input.start_node, input.target_node)
    def graph_plot():
        G = graph.get()
        if not G:
            return None

        pos = nx.spring_layout(G, seed=input.layout_seed())

        # Draw Node Color
        color_map = []
        for node in G:
            if node == input.start_node():
                color_map.append('tab:green')
            elif node == input.target_node():
                color_map.append('tab:red')
            else:
                color_map.append('tab:blue')

        nx.draw_networkx_edges(G, pos)
        nx.draw_networkx_nodes(G, pos, node_color=color_map)

        # Draw labels
        if "label" in G.nodes[0]:
            nx.draw_networkx_labels(G, pos)
            labels = dict(sorted(nx.get_node_attributes(G, "label").items()))
            label_pos = {node: (coords[0], coords[1] - 0.12) for node, coords in pos.items()}
            nx.draw_networkx_labels(G, label_pos, labels)
        else:
            labels = {node: str(node) for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels)

        # Draw weights
        edge_labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
