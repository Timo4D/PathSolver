import networkx as nx
from shiny import ui, render


def graph_ui():
    return ui.page_fluid(
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_selectize(
                    "selectize_graph",
                    "Select a Graph",
                    {"random": "Random Graph", "koot_beispiel_deutschland": "Deutschland Beispiel"}
                ),
                ui.input_slider("n_slider", "Number of Nodes", 1, 30, 8),
                ui.input_slider("k_slider", "K", 2, 5, 3),
                ui.input_slider("p_slider", "P", 0, 1, 0.5),
                ui.input_numeric("start_node", "Start Node", value=1),
                ui.input_numeric("target_node", "Target Node", value=2),
                ui.input_numeric("layout_seed", "Layout Seed", value=1),
            ),
            ui.output_plot("graph_plot")
        ),
    )


def generate_random_graph(n, k, p):
    G = nx.connected_watts_strogatz_graph(n, k, p)
    return G


def draw_random_graph(G, pos, start, target):
    nx.draw_networkx_labels(G, pos)

    color_map = []
    for node in G:
        if node == start:
            color_map.append('green')
        elif node == target:
            color_map.append('red')
        else:
            color_map.append('blue')

    nx.draw_networkx_edges(G, pos)
    nx.draw_networkx_nodes(G, pos, node_color=color_map)


def graph_ui_server(input, output, session):
    graph_data = {
        "graph": None,
        "layout_seed": None,
    }

    @output
    @render.plot
    def graph_plot():
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

        draw_random_graph(
            graph_data["graph"],
            graph_data["pos"],
            input.start_node(),
            input.target_node(),
        )
