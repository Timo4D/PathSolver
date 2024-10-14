from enum import Enum

import networkx as nx
import pandas as pd
from htmltools import TagList
from shiny import ui, render, reactive

from modules.djikstra_explanation import djikstra_explanation
from utils.graph_generators import generate_random_graph, generate_koot_example, generate_from_edge_list
from utils.graph_utils import plot_graph

distances_df = reactive.Value(pd.DataFrame())
graph = reactive.Value(nx.Graph())
seed = reactive.Value(1)
step_counter = reactive.Value(0)
step_explanation = reactive.Value("Here will be the explanations of every step")
current_node = reactive.Value(None)
current_edges = reactive.Value([])
distance = reactive.Value(0)
nodes_visited = reactive.Value([])
state_history = reactive.Value([])


class GraphType(Enum):
    RANDOM_GRAPH = "random_graph"
    KOOT_EXAMPLE_DEUTSCHLAND = "koot_example_deutschland"
    EDGE_LIST = "edge_list"


def graph_ui():
    return ui.page_fluid(
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_action_button("tutorial", "Tutorial"),

                ui.input_selectize(
                    "selectize_graph",
                    "Select a Graph",
                    {GraphType.RANDOM_GRAPH.value: "Random Graph",
                     GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value: "Deutschland Beispiel",
                     GraphType.EDGE_LIST.value: "Import from Edgelist"},
                    selected=GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value
                ),
                ui.output_ui("graph_generator_settings"),
                ui.input_numeric("start_node", "Start Node", value=0, min=0),
                ui.input_numeric("target_node", "Target Node", value=1, min=0),
                ui.input_numeric("layout_seed", "Layout Seed", value=1, min=0),
            ),
            ui.layout_column_wrap(
                ui.input_action_button("prev_step", "Previous Step"),
                ui.input_action_button("next_step", "Next Step"),
            ),
            ui.output_ui("explain"),
            ui.output_plot("graph_plot"),
            ui.row(
                ui.column(
                    6,
                    ui.card(
                        ui.card_header("Distances between nodes"),
                        ui.card_body(
                            ui.output_data_frame("display_distances"),
                        )
                    )
                ),
                ui.column(
                    6,
                    ui.card(
                        ui.card_header("Explanaiton of the Algorithm"),
                        ui.card_body(
                            djikstra_explanation

                        )
                    )
                )
            )
        ),
    )


def save_state():
    state = {
        "distances_df": distances_df.get().copy(),
        "step_counter": step_counter.get(),
        "nodes_visited": nodes_visited.get().copy(),
        "current_edges": current_edges.get().copy(),
        "current_node": current_node.get(),
        "step_explanation": step_explanation.get()
    }
    state_history.get().append(state)


def restore_state():
    if state_history.get():
        state = state_history.get().pop()
        distances_df.set(state["distances_df"])
        step_counter.set(state["step_counter"])
        nodes_visited.set(state["nodes_visited"])
        current_edges.set(state["current_edges"])
        current_node.set(state["current_node"])
        step_explanation.set(state["step_explanation"])


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

        distance_matrix = pd.DataFrame(index=nodes, columns=["Cost", "Previous"])
        distance_matrix["Cost"] = float('inf')

        distance_matrix.index.name = index_name
        distance_matrix.reset_index(inplace=True)
        distances_df.set(distance_matrix)
        step_counter.set(0)
        nodes_visited.set([])
        current_edges.set([])
        current_node.set(None)
        step_explanation.set("Here will be the explanations of every step")


def init_df():
    reset_df()


def graph_ui_server(input, output, session):
    @output
    @render.ui
    def explain():
        step = step_counter.get()
        return TagList(
            ui.card(
                ui.p(step_explanation.get()),
                style = "border: 5px solid green;" if step == 3 else ""
            )
        )

    @reactive.Effect
    @reactive.event(input.prev_step)
    def prev_step():
        restore_state()

    @reactive.Effect
    @reactive.event(input.next_step)
    def next_step():
        step = step_counter.get()
        if step == 3:
            # Step 3 means its done
            return

        save_state()
        df = distances_df.get()
        G = graph.get()
        neighbors = []
        edges = []
        print("Step", step)
        if step == 0:  # Init
            step_explanation.set("Step 1: Set distance to start node to 0")
            if not df.empty:
                start_node = input.start_node()
                if 0 <= start_node < len(df):
                    df.iloc[start_node, 1] = 0
                    if "label" in G.nodes[0]:
                        df.iloc[start_node, 2] = nx.get_node_attributes(G, "label")[start_node]
                    else:
                        df.iloc[start_node, 2] = start_node
                    distances_df.set(df)
                    nodes_visited.get().append(start_node)
                    current_node.set(start_node)
                    step_counter.set(step + 1)
                else:
                    print(f"Invalid start node: {start_node}")
        elif step == 1:  # Look at neighbors
            prev_cost = df.iloc[current_node.get(), 1]

            for n in G.neighbors(current_node.get()):
                if n not in nodes_visited.get():
                    new_weight = G[n][current_node.get()]['weight'] + prev_cost

                    neighbors.append({"node": n, "weight": (G[n][current_node.get()]['weight'] + prev_cost)})

                    if new_weight < df.iloc[n, 1]:
                        df.iloc[n, 1] = new_weight
                        if "label" in G.nodes[0]:
                            df.iloc[n, 2] = nx.get_node_attributes(G, "label")[current_node.get()]
                        else:
                            df.iloc[n, 2] = current_node.get()

                    edges.append(sorted((n, current_node.get())))

            distances_df.set(df.copy())
            current_edges.set(current_edges.get() + edges)

            step_explanation.set(
                "Lets again look at the possible neighbours that we have not visited yet."
                "Lets get the cumulative distance to that node calculated and if its lower that wits in it already, put in the new lower cost and update its previous node"
                f"We will leave {nodes_visited.get()} out as we have already visited"
            )

            step_counter.set(step_counter.get() + 1)

        elif step == 2:  # set new current node

            current_edges.set([])

            unvisited_nodes = df[~df.index.isin(nodes_visited.get())]
            min_cost_node = unvisited_nodes["Cost"].idxmin()
            current_node.set(min_cost_node)

            if current_node.get() == input.target_node():
                step_explanation.set(
                    "We have now arrived at our Target node, that means we are done and have found the shortest possible distance to it"
                )
                step_counter.set(step_counter.get() + 1)
            else:
                step_explanation.set(
                    f"You can see that {min_cost_node} is the shortest path to the next node so lets make {current_node.get()} our new Node. "
                    f"Also notice that {current_node.get()} is not our Target Node, so we need to continue and do the previous step again"
                )
                step_counter.set(step_counter.get() - 1)
            nodes_visited.get().append(current_node.get())
        elif step == 3:
            return

    @reactive.Effect
    def update_graph():
        if input.selectize_graph() == GraphType.RANDOM_GRAPH.value:
            graph.set(generate_random_graph(input.n_slider(), input.k_slider(), input.p_slider()))
        elif input.selectize_graph() == GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value:
            graph.set(generate_koot_example())
        elif input.selectize_graph() == GraphType.EDGE_LIST.value:
            edge_list_input = input.edge_list_input()
            if isinstance(edge_list_input, str):
                result = generate_from_edge_list(edge_list_input)
                if isinstance(result, str):
                    step_explanation.set(result)
                else:
                    graph.set(result)
            else:
                graph.set(edge_list_input)

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
                    "cols": [0],
                    "style": {"background-color": "#2ca02c"},
                },
                # Highlight target node red
                {
                    "rows": [input.target_node()],
                    "cols": [0],
                    "style": {"background-color": "#d62728"},
                },
            ]
        )

    @reactive.Effect
    @reactive.event(input.target_node, input.start_node)
    def reset_djikstra():
        reset_df()

    @reactive.Effect
    def initialize_distances():
        init_df()

    @output
    @render.ui
    def graph_generator_settings():
        if input.selectize_graph() == GraphType.RANDOM_GRAPH.value:
            return ui.TagList(
                ui.input_slider("n_slider", "Number of Nodes", 2, 30, 8),
                ui.input_slider("k_slider", "K", 2, 5, 3),
                ui.input_slider("p_slider", "P", 0, 1, 0.5),
            )
        if input.selectize_graph() == GraphType.EDGE_LIST.value:
            return ui.TagList(
                ui.input_text_area("edge_list_input", "Edge List", "(0,1, 10),\n(1,2, 10),\n(2,0,20)")
            )

    @output
    @render.plot
    @reactive.event(input.selectize_graph, graph, input.layout_seed, input.start_node, input.target_node, current_node,
                    current_edges)
    def graph_plot():
        plot_graph(graph.get(), input.start_node(), input.target_node(), input.layout_seed(), current_node.get(),
                   current_edges.get())

    @reactive.effect
    @reactive.event(input.tutorial)
    def show_important_message():
        m = ui.modal(
            "This will be a short introduction into the Application",
            easy_close=True,
            footer=None,
        )
        ui.modal_show(m)
