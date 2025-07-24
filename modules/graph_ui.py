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
from modules.cytoscape.graph_component import render_cytoscape
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

    @output
    @render_cytoscape
    @reactive.event(
        state_manager.graph, input.start_node, input.target_node, 
        state_manager.current_node, state_manager.current_edges
    )
    def cytoscape_graph():
        """Render the graph using Cytoscape.js."""
        graph = state_manager.graph.get()
        if not graph or len(graph.nodes) == 0:
            return {"elements": [], "style": [], "layout": {"name": "circle"}}
        
        # Convert NetworkX graph to Cytoscape format
        elements = []
        
        # Add nodes
        for node in graph.nodes():
            node_data = {
                "data": {
                    "id": str(node),
                    "label": str(node)
                }
            }
            
            # Style nodes based on current state
            current_node = state_manager.current_node.get()
            start_node = input.start_node()
            target_node = input.target_node()
            
            if node == current_node:
                node_data["classes"] = "current"
            elif node == start_node:
                node_data["classes"] = "start"
            elif node == target_node:
                node_data["classes"] = "target"
            elif node in state_manager.nodes_visited.get():
                node_data["classes"] = "visited"
            
            elements.append(node_data)
        
        # Add edges
        for edge in graph.edges(data=True):
            source, target, data = edge
            edge_data = {
                "data": {
                    "id": f"{source}-{target}",
                    "source": str(source),
                    "target": str(target),
                    "weight": data.get("weight", 1)
                }
            }
            
            # Highlight current edges
            current_edges = state_manager.current_edges.get()
            if (source, target) in current_edges or (target, source) in current_edges:
                edge_data["classes"] = "current"
            
            elements.append(edge_data)
        
        # Define styles for different node and edge states
        style = [
            {
                "selector": "node",
                "style": {
                    "background-color": "#4CAF50",
                    "color": "#fff",
                    "label": "data(label)",
                    "width": 40,
                    "height": 40,
                    "text-valign": "center",
                    "text-halign": "center",
                    "font-size": "12px"
                }
            },
            {
                "selector": "node.start",
                "style": {
                    "background-color": "#2196F3",
                }
            },
            {
                "selector": "node.target", 
                "style": {
                    "background-color": "#FF5722",
                }
            },
            {
                "selector": "node.current",
                "style": {
                    "background-color": "#FFC107",
                    "border-width": 3,
                    "border-color": "#FF9800"
                }
            },
            {
                "selector": "node.visited",
                "style": {
                    "background-color": "#9C27B0",
                }
            },
            {
                "selector": "edge",
                "style": {
                    "width": 2,
                    "line-color": "#666",
                    "target-arrow-color": "#666",
                    "target-arrow-shape": "triangle",
                    "label": "data(weight)",
                    "font-size": "10px"
                }
            },
            {
                "selector": "edge.current",
                "style": {
                    "width": 4,
                    "line-color": "#FFC107",
                    "target-arrow-color": "#FFC107"
                }
            }
        ]
        
        layout = {
            "name": "circle",
            "radius": 150
        }
        
        return {
            "elements": elements,
            "style": style,
            "layout": layout
        }

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