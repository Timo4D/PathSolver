from enum import Enum
from operator import contains

import networkx as nx
import pandas as pd
from htmltools import TagList
from shiny import ui, render, reactive
from shiny.types import FileInfo

from modules.djikstra_explanation import djikstra_explanation
from modules.solution_quiz import render_solution_quiz
from modules.tutorial_modal import tutorial_modal, tutorial_modal_server
from utils.graph_generators import generate_random_graph, generate_koot_example, generate_from_edge_list
from utils.graph_utils import plot_graph, dijkstra_solution
from utils.icons import warning as warning_icon

distances_df = reactive.Value(pd.DataFrame())
graph = reactive.Value(nx.Graph())
seed = reactive.Value(1)
step_counter = reactive.Value(0)
step_explanation = reactive.Value(TagList("Here will be the explanations of every step"))
current_node = reactive.Value(None)
current_edges = reactive.Value([])
distance = reactive.Value(0)
nodes_visited = reactive.Value([])
state_history = reactive.Value([])
invalid_edge_list = reactive.Value(False)
solution = reactive.Value()
start_node_error = reactive.Value(False)
target_node_error = reactive.Value(False)


class GraphType(Enum):
    RANDOM_GRAPH = "random_graph"
    KOOT_EXAMPLE_DEUTSCHLAND = "koot_example_deutschland"
    EDGE_LIST = "edge_list"
    CSV_FILE = "csv_file"


def graph_ui():
    return ui.page_fluid(
        ui.layout_sidebar(
            ui.sidebar(
                tutorial_modal(),
                graph_selection_ui(),
                ui.output_ui("graph_generator_settings"),
                ui.input_numeric("start_node", ui.span("Start Node", ui.output_ui("start_node_error_message")), value=0,
                                 min=0),
                ui.input_numeric("target_node", ui.span("Target Node", ui.output_ui("target_node_error_message")),
                                 value=1, min=0),
                ui.input_numeric("layout_seed", "Layout Seed", value=1, min=0),
            ),
            ui.output_ui("explain"),
            ui.output_ui("progress_bar"),
            ui.output_plot("graph_plot"),
            ui.row(
                ui.column(6, ui.output_ui("render_solution_quiz_ui"), distances_ui()),
                ui.column(6, visited_nodes_ui(), algorithm_explanation_ui())
            )
        ),
    )


def graph_selection_ui():
    return ui.input_selectize(
        "selectize_graph",
        "Select a Graph",
        {GraphType.RANDOM_GRAPH.value: "Random Graph",
         GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value: "Deutschland Beispiel",
         GraphType.EDGE_LIST.value: "Import from Edgelist",
         GraphType.CSV_FILE.value: "Upload a CSV file"},
        selected=GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value
    )

def distances_ui():
    return ui.card(
        ui.card_header("Distances between nodes"),
        ui.card_body(
            ui.output_data_frame("display_distances"),
        )
    )


def visited_nodes_ui():
    return ui.card(
        ui.card_header("Visited Nodes"),
        ui.card_body(ui.output_ui("visited_nodes"))
    )


def algorithm_explanation_ui():
    return ui.card(
        ui.card_header("Explanaiton of the Algorithm"),
        ui.card_body(
            djikstra_explanation

        )
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
    G = graph.get()
    if G:
        nodes, index_name = get_graph_nodes_and_index_name(G)
        distance_matrix = pd.DataFrame(index=nodes, columns=["Cost", "Previous"])
        distance_matrix["Cost"] = float('inf')

        distance_matrix.index.name = index_name
        distance_matrix.reset_index(inplace=True)
        distances_df.set(distance_matrix)
        step_counter.set(0)
        nodes_visited.set([])
        current_edges.set([])
        current_node.set(None)
        solution.set(None)
        step_explanation.set(TagList("Here will be the explanations of every step"))


def get_graph_nodes_and_index_name(G):
    if "label" in G.nodes[0]:
        nodes = dict(sorted(nx.get_node_attributes(G, "label").items())).values()
        index_name = "Cities"
    else:
        nodes = [str(node) for node in G.nodes]
        index_name = "Node"
    return nodes, index_name


def graph_ui_server(input, output, session):
    @output
    @render.ui
    def render_solution_quiz_ui():
        if step_counter.get() == 3:
            return render_solution_quiz()

    @output
    @render.ui
    def progress_bar():
        return create_progress_bar()

    @output
    @render.ui
    def explain():
        return create_explanation_ui()

    @output
    @render.ui
    @reactive.event(nodes_visited)
    def visited_nodes():
        nodes = ", ".join(
            [str(int(node)) for node in nodes_visited.get()]) if nodes_visited.get() else "No nodes visited yet"
        return TagList(nodes)

    @reactive.Effect
    @reactive.event(input.prev_step)
    def prev_step():
        restore_state()

    @reactive.Effect
    @reactive.event(input.next_step)
    def next_step():
        handle_next_step(input)

    @reactive.Effect
    def update_graph():
        update_graph_based_on_selection(input)

    @output
    @render.data_frame
    @reactive.event(distances_df, step_counter, input.start_node, input.target_node)
    def display_distances():
        return render_distances(input)

    @reactive.Effect
    @reactive.event(input.target_node, input.start_node)
    def reset_djikstra():
        reset_df()

    @reactive.Effect
    def initialize_distances():
        reset_df()

    @output
    @render.ui
    def graph_generator_settings():
        return render_graph_generator_settings(input)

    @output
    @render.ui
    def start_node_error_message():
        return ui.tooltip(warning_icon, "Your input is invalid") if start_node_error.get() else None

    @output
    @render.ui
    def target_node_error_message():
        return ui.tooltip(warning_icon, "Your input is invalid") if target_node_error.get() else None

    @output
    @render.ui
    def edge_list_error_message():
        return ui.tooltip(warning_icon, "Your input is invalid") if invalid_edge_list.get() else None
        # return ui.p("Your Input edge list is not Valid!",
        #             style="border: 3px solid red;") if invalid_edge_list.get() else None,

    @output
    @render.plot
    @reactive.event(input.selectize_graph, graph, input.layout_seed, input.start_node, input.target_node,
                    input.dark_mode_switch, current_node,
                    current_edges)
    def graph_plot():
        if step_counter.get() == 3:
            final_step = True
        else:
            final_step = False

        plot_graph(graph.get(), input.start_node(), input.target_node(), input.layout_seed(), distances_df.get(),
                   current_node.get(),
                   current_edges.get(), input.dark_mode_switch(), final_step)

    tutorial_modal_server(input, output, session)

    @reactive.Effect
    @reactive.event(input.submit_solution)
    def check_user_solution():
        user_input = input.user_solution().strip()
        try:
            user_solution = [int(node) for node in user_input.split(",")]
        except ValueError:
            user_solution = None


        correct_solution = solution.get()

        if user_solution == correct_solution:
            step_counter.set(4)
            # to draw the solution
            handle_next_step(input)
        else:
            step_explanation.set(TagList("Sorry, your solution is incorrect. Please try again."))

    @reactive.calc
    def parsed_edge_list():
        file: list[FileInfo] | None = input.edge_list_file()
        if file is None:
            print("File is None")
            return None
        else:
            print(f"File: {file}")
            return file[0]["datapath"]

    @reactive.Effect
    def use_parsed_edge_list():
        edge_list = parsed_edge_list()
        if edge_list is not None:
            print(edge_list)
            with open('/home/timo/shiny/dijkstra/edgelist.txt', 'r') as file:
                edge_list_str = file.read()
            print(edge_list_str)
            result = generate_from_edge_list(edge_list_str)
            if isinstance(result, str):
                invalid_edge_list.set(True)
                step_explanation.set(TagList(result))
            else:
                invalid_edge_list.set(False)
                graph.set(result)


def create_progress_bar():
    return TagList(
        ui.layout_columns(
            ui.input_action_button("prev_step", "Previous Step"),
            *[ui.div(
                style=f"background-color: {'red' if step_counter.get() >= i else '#d9d9d9'}; height: 30px; width: 100%; margin: auto; display: flex; align-items: center; justify-content: center;")
                for i in range(4)],
            ui.input_action_button("next_step", "Next Step"),
        )
    )


def create_explanation_ui():
    step = step_counter.get()
    headings = {
        0: "Step 0: Initialize",
        1: "Step 1: Visit Nodes",
        2: "Step 2: Look For Next Node",
        3: "Step 3: Finish",
        4: "Congratulations! Your solution is correct."
    }
    return TagList(
        ui.h1(headings.get(step), style="margin-bottom: 0;"),
        ui.p(step_explanation.get(), style="margin-top: 0;"),
    )

def update_graph_based_on_selection(input):
    if input.selectize_graph() == GraphType.RANDOM_GRAPH.value:
        if input.k_slider() > input.n_slider():
            step_explanation.set(TagList("Please select make sure that k is not smaller than n"))
        else:
            graph.set(generate_random_graph(input.n_slider(), input.k_slider(), input.p_slider()))
    elif input.selectize_graph() == GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value:
        graph.set(generate_koot_example())
    elif input.selectize_graph() == GraphType.EDGE_LIST.value:
        edge_list_input = input.edge_list_input()
        if isinstance(edge_list_input, str):
            result = generate_from_edge_list(input.edge_list_input())
            if isinstance(result, str):
                invalid_edge_list.set(True)
                step_explanation.set(TagList(result))
            else:
                invalid_edge_list.set(False)
                graph.set(result)
        else:
            graph.set(edge_list_input)


def render_graph_generator_settings(input):
    if input.selectize_graph() == GraphType.RANDOM_GRAPH.value:
        return ui.TagList(
            ui.input_slider("n_slider", "Number of Nodes", 2, 30, 8),
            ui.input_slider("k_slider", "Neighbors in a ring topology", 2, 5, 3),
            ui.input_slider("p_slider", "Probability of rewiring each edge", 0, 1, 0.5),
        )
    if input.selectize_graph() == GraphType.EDGE_LIST.value:
        return ui.TagList(
            ui.input_text_area("edge_list_input", ui.span("Edge List", ui.output_ui("edge_list_error_message")),
                               "0 1 10\n1 2 10\n2 0 20", rows=10, autoresize=True)
        )
    if input.selectize_graph() == GraphType.CSV_FILE.value:
        return ui.TagList(
            ui.input_file("edge_list_file", ui.span("Upload an edge list", ui.output_ui("edge_list_error_message")))
        )

def render_distances(input):
    df = distances_df.get()

    if contains(df.columns, "Node"):
        try:
            index_start = int(df.index[df['Node'].astype(int) == int(input.start_node())].item())
            index_target = int(df.index[df['Node'].astype(int) == int(input.target_node())].item())
        except ValueError:
            df = pd.DataFrame({"Error": ["Selected Node not on Graph"]})
            return render.DataTable(df, width="100%")

        try:
            styles = [
                {"rows": index_start, "style": {"background-color": "green"}},
                {"rows": index_target, "style": {"background-color": "red"}},
            ]
            return render.DataTable(distances_df.get(), width="100%", styles=styles)
        except TypeError:
            df = pd.DataFrame({"Error": ["Invalid data"]})
            return render.DataTable(df, width="100%")

    else:
        try:
            styles = [
                {"rows": [int(input.start_node())], "style": {"background-color": "green"}},
                {"rows": [int(input.target_node())], "style": {"background-color": "red"}},
            ]
            return render.DataTable(distances_df.get(), width="100%", styles=styles)
        except TypeError:
            df = pd.DataFrame({"Error": ["Invalid data"]})
            return render.DataTable(df, width="100%")



def handle_next_step(input):
    step = step_counter.get()
    save_state()
    df = distances_df.get()
    G = graph.get()
    if step == 0:
        initialize_step(input, df, G)
    elif step == 1:
        visit_neighbors(df, G)
    elif step == 2:
        set_new_current_node(df, G, input)
        if not solution.get():
            solution.set(dijkstra_solution(G, input.start_node(), input.target_node()))
    elif step == 4:
        show_solution(solution.get())
        step_explanation.set(TagList(""))


def initialize_step(input, df, G):
    step_explanation.set(TagList("First set distance to start node to 0 and every other node to infinity"))
    if not df.empty:
        start_node = input.start_node()
        target_node = input.target_node()
        if start_node in G.nodes:
            start_node_error.set(False)
        else:
            start_node_error.set(True)
            return

        if target_node in G.nodes:
            df.iloc[start_node, 1] = 0
            if "label" in G.nodes[0]:
                df.iloc[start_node, 2] = nx.get_node_attributes(G, "label")[start_node]
            else:
                df.iloc[start_node, 2] = start_node
            distances_df.set(df)
            nodes_visited.set(nodes_visited.get() + [start_node])
            current_node.set(start_node)
            step_counter.set(1)
            target_node_error.set(False)
        else:
            target_node_error.set(True)



def visit_neighbors(df, G):
    prev_cost = df.iloc[current_node.get(), 1]
    neighbors, edges = [], []
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
    nodes_visited_without_current = [int(node) for node in nodes_visited.get() if node != current_node.get()]
    # Casting everything to int do to different int classes: int vs np.int65

    nodes_visited_text = None
    if nodes_visited_without_current:
        nodes_visited_text = TagList(
            f"We will leave nodes {nodes_visited_without_current} out as we have already visited them", ui.br()
        )

    step_explanation.set(
        TagList(
            "Now look at the possible unvisited neighbours", ui.br(),
            nodes_visited_text,
            "You need to calculate the cost of all unvisited neighbours. To do this add the distance to your current node + the weight of the edge.",
            ui.br(),
            "If the weight is lower that whats already calculated we need to update it, otherwise we won't change it",
            ui.br(),
        )
    )
    step_counter.set(2)

def set_new_current_node(df, G, input):
    current_edges.set([])

    unvisited_nodes = df[~df.index.isin(nodes_visited.get())]
    min_cost_node = unvisited_nodes["Cost"].idxmin()
    current_node.set(min_cost_node)

    if current_node.get() == input.target_node():
        step_explanation.set(
            TagList(
                "We have now arrived at our Target node, that means we are done and have found the shortest possible distance to it",
                ui.br(),
                "You now have to enter your solution of the fastest path in new Box below. If it is correct you will see the path on the graph.",
                ui.br(),
                "The weights of the edges are now hidden, so try to get the solution with help of the table below.",
                ui.br(),
                "The Dijkstra Algorithm would trace the way from thr Target node via its previus node until it arrives at the start node",
            )
        )
        step_counter.set(step_counter.get() + 1)
    else:
        step_explanation.set(
            TagList(
                f"You can see that {min_cost_node} is the node with the lowest cost that we have not visited yet, so {current_node.get()} is our new Node. ",
                ui.br(),
                f"Also notice that {current_node.get()} is not our Target Node, so we need to continue and do the previous step again",
                ui.br()
            )
        )
        step_counter.set(step_counter.get() - 1)
    nodes_visited.set(nodes_visited.get() + [current_node.get()])

def show_solution(solution):
    current_edges.set([list(edge) for edge in zip(solution, solution[1:])])


