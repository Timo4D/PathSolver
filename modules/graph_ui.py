"""Refactored graph UI module with improved organization."""

from htmltools import TagList
from shiny import ui, render, reactive
from shiny.types import FileInfo

from constants import DEFAULT_EDGE_LIST_PATH, STEP_FINISH
from modules.state_manager import state_manager
from modules.ui_components import (
    main_ui, GraphType, create_progress_bar, create_explanation_ui,
    render_graph_generator_settings, render_error_tooltip, render_distances_table
)
from modules.algorithm_logic import DijkstraStepHandler
from modules.solution_quiz import render_solution_quiz
from modules.tutorial_modal import tutorial_modal_server
from utils.graph_generators import generate_random_graph, generate_koot_example, generate_from_edge_list
from utils.graph_utils import plot_graph


def graph_ui():
    """Main graph UI function."""
    return main_ui()


def graph_ui_server(input, output, session):
    """Main server logic for the graph UI."""
    # Initialize algorithm handler
    algorithm_handler = DijkstraStepHandler(state_manager)
    
    @output
    @render.ui
    def render_solution_quiz_ui():
        if state_manager.step_counter.get() == STEP_FINISH:
            return render_solution_quiz()

    @output
    @render.ui
    def progress_bar():
        return create_progress_bar(state_manager.step_counter.get())

    @output
    @render.ui
    def explain():
        return create_explanation_ui(
            state_manager.step_counter.get(),
            state_manager.step_explanation.get()
        )

    @output
    @render.ui
    @reactive.event(state_manager.nodes_visited)
    def visited_nodes():
        nodes = ", ".join(
            [str(int(node)) for node in state_manager.nodes_visited.get()]
        ) if state_manager.nodes_visited.get() else "No nodes visited yet"
        return TagList(nodes)

    @reactive.Effect
    @reactive.event(input.prev_step)
    def prev_step():
        state_manager.restore_state()

    @reactive.Effect
    @reactive.event(input.next_step)
    def next_step():
        algorithm_handler.handle_next_step(input)

    @reactive.Effect
    def update_graph():
        _update_graph_based_on_selection(input)

    @output
    @render.data_frame
    @reactive.event(
        state_manager.distances_df, state_manager.step_counter, 
        input.start_node, input.target_node
    )
    def display_distances():
        return render_distances_table(
            state_manager.distances_df.get(),
            input.start_node(),
            input.target_node()
        )

    @reactive.Effect
    @reactive.event(input.target_node, input.start_node)
    def reset_dijkstra():
        state_manager.reset_algorithm_state()

    @reactive.Effect
    def initialize_distances():
        state_manager.reset_algorithm_state()

    @output
    @render.ui
    def graph_generator_settings():
        return render_graph_generator_settings(input.selectize_graph())

    @output
    @render.ui
    def start_node_error_message():
        return render_error_tooltip(state_manager.start_node_error.get())

    @output
    @render.ui
    def target_node_error_message():
        return render_error_tooltip(state_manager.target_node_error.get())

    @output
    @render.ui
    def edge_list_error_message():
        return render_error_tooltip(state_manager.invalid_edge_list.get())

    @output
    @render.plot
    @reactive.event(
        input.selectize_graph, state_manager.graph, input.layout_seed, 
        input.start_node, input.target_node, state_manager.current_node,
        state_manager.current_edges
    )
    def graph_plot():
        final_step = (state_manager.step_counter.get() == STEP_FINISH)
        plot_graph(
            state_manager.graph.get(),
            input.start_node(),
            input.target_node(),
            input.layout_seed(),
            state_manager.distances_df.get(),
            state_manager.current_node.get(),
            state_manager.current_edges.get(),
            final_step
        )

    @reactive.Effect
    @reactive.event(input.submit_solution)
    def check_user_solution():
        algorithm_handler.check_user_solution(input)

    @reactive.calc
    def parsed_edge_list():
        file: list[FileInfo] | None = input.edge_list_file()
        if file is None:
            return None
        return file[0]["datapath"]

    @reactive.Effect
    def use_parsed_edge_list():
        edge_list = parsed_edge_list()
        if edge_list is not None:
            try:
                with open(DEFAULT_EDGE_LIST_PATH, 'r') as file:
                    edge_list_str = file.read()
                result = generate_from_edge_list(edge_list_str)
                if isinstance(result, str):
                    state_manager.invalid_edge_list.set(True)
                    state_manager.step_explanation.set(TagList(result))
                else:
                    state_manager.invalid_edge_list.set(False)
                    state_manager.graph.set(result)
            except FileNotFoundError:
                state_manager.invalid_edge_list.set(True)
                state_manager.step_explanation.set(
                    TagList(f"Edge list file not found: {DEFAULT_EDGE_LIST_PATH}")
                )

    # Initialize tutorial modal server
    tutorial_modal_server(input, output, session)


def _update_graph_based_on_selection(input):
    """Update graph based on user selection."""
    if input.selectize_graph() == GraphType.RANDOM_GRAPH.value:
        if input.k_slider() > input.n_slider():
            state_manager.step_explanation.set(
                TagList("Please select make sure that k is not smaller than n")
            )
        else:
            graph = generate_random_graph(
                input.n_slider(), input.k_slider(), input.p_slider()
            )
            state_manager.graph.set(graph)
    elif input.selectize_graph() == GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value:
        state_manager.graph.set(generate_koot_example())
    elif input.selectize_graph() == GraphType.EDGE_LIST.value:
        edge_list_input = input.edge_list_input()
        if isinstance(edge_list_input, str):
            result = generate_from_edge_list(input.edge_list_input())
            if isinstance(result, str):
                state_manager.invalid_edge_list.set(True)
                state_manager.step_explanation.set(TagList(result))
            else:
                state_manager.invalid_edge_list.set(False)
                state_manager.graph.set(result)
        else:
            state_manager.graph.set(edge_list_input)