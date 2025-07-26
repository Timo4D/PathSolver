"""Refactored graph UI module with improved organization."""

import networkx as nx
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
from utils.graph_utils import plot_graph, convert_graph_to_cytoscape, get_cytoscape_styles, get_cytoscape_layout


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
        elements = convert_graph_to_cytoscape(
            graph,
            current_node=state_manager.current_node.get(),
            start_node=input.start_node(),
            target_node=input.target_node(),
            nodes_visited=state_manager.nodes_visited.get(),
            current_edges=state_manager.current_edges.get()
        )
        
        return {
            "elements": elements,
            "style": get_cytoscape_styles(),
            "layout": get_cytoscape_layout()
        }

    @reactive.Effect
    @reactive.event(input.cytoscape_graph_set_start_node)
    def handle_set_start_node():
        """Handle setting start node from context menu."""
        data = input.cytoscape_graph_set_start_node()
        if data and "id" in data:
            node_id = int(data["id"])
            graph = state_manager.graph.get()
            if graph and node_id in graph.nodes():
                # Update the start node input programmatically
                ui.update_selectize("start_node", selected=str(node_id))
                # Reset algorithm state when start node changes
                state_manager.reset_algorithm_state()

    @reactive.Effect  
    @reactive.event(input.cytoscape_graph_set_target_node)
    def handle_set_target_node():
        """Handle setting target node from context menu."""
        data = input.cytoscape_graph_set_target_node()
        if data and "id" in data:
            node_id = int(data["id"])
            graph = state_manager.graph.get()
            if graph and node_id in graph.nodes():
                # Update the target node input programmatically
                ui.update_selectize("target_node", selected=str(node_id))
                # Reset algorithm state when target node changes
                state_manager.reset_algorithm_state()

    @reactive.Effect
    @reactive.event(input.cytoscape_graph_delete_node)
    def handle_delete_node():
        """Handle deleting a node from context menu."""
        data = input.cytoscape_graph_delete_node()
        if data and "id" in data:
            node_id = int(data["id"])
            graph = state_manager.graph.get()
            if graph and node_id in graph.nodes():
                # Check if deleting this node would disconnect the graph
                if len(graph.nodes()) <= 2:
                    state_manager.step_explanation.set(
                        TagList("Cannot delete node: Graph must have at least 2 nodes")
                    )
                    return
                
                # Remove the node and all its edges from the NetworkX graph
                graph_copy = graph.copy()
                graph_copy.remove_node(node_id)
                
                # Update the graph in state manager
                state_manager.graph.set(graph_copy)
                
                # Clear start/target if they were the deleted node
                current_start = input.start_node()
                current_target = input.target_node()
                
                if current_start and int(current_start) == node_id:
                    ui.update_selectize("start_node", selected="")
                if current_target and int(current_target) == node_id:
                    ui.update_selectize("target_node", selected="")
                
                # Reset algorithm state
                state_manager.reset_algorithm_state()

    @reactive.Effect
    @reactive.event(input.cytoscape_graph_delete_edge)
    def handle_delete_edge():
        """Handle deleting an edge from context menu."""
        data = input.cytoscape_graph_delete_edge()
        if data and "source" in data and "target" in data:
            source_id = int(data["source"])
            target_id = int(data["target"])
            graph = state_manager.graph.get()
            
            if graph and graph.has_edge(source_id, target_id):
                # Create a copy of the graph and remove the edge
                graph_copy = graph.copy()
                graph_copy.remove_edge(source_id, target_id)
                
                # Check if removing this edge would disconnect the graph
                if not nx.is_connected(graph_copy):
                    state_manager.step_explanation.set(
                        TagList(f"Cannot delete edge {source_id}-{target_id}: This would disconnect the graph")
                    )
                    return
                
                # Update the graph in state manager
                state_manager.graph.set(graph_copy)
                
                # Reset algorithm state since graph structure changed
                state_manager.reset_algorithm_state()

    @reactive.Effect
    @reactive.event(input.cytoscape_graph_add_node)
    def handle_add_node():
        """Handle adding a new node from context menu."""
        data = input.cytoscape_graph_add_node()
        print(f"Debug: Received add_node data: {data}")  # Debug output
        
        if data and "x" in data and "y" in data:
            graph = state_manager.graph.get()
            if graph:
                # Find the next available node ID
                existing_nodes = list(graph.nodes())
                if existing_nodes:
                    # For integer node IDs, find the maximum and add 1
                    if all(isinstance(node, int) for node in existing_nodes):
                        new_node_id = max(existing_nodes) + 1
                    else:
                        # For mixed or string node IDs, find a unique ID
                        new_node_id = len(existing_nodes)
                        while new_node_id in existing_nodes:
                            new_node_id += 1
                else:
                    new_node_id = 0
                
                print(f"Debug: Creating new node with ID: {new_node_id} at position ({data['x']}, {data['y']})")  # Debug output
                
                # Create a copy of the graph and add the new node with position
                graph_copy = graph.copy()
                graph_copy.add_node(new_node_id, x=data["x"], y=data["y"])
                
                # Update the graph in state manager
                state_manager.graph.set(graph_copy)
                
                # Reset algorithm state since graph structure changed
                state_manager.reset_algorithm_state()
                
                state_manager.step_explanation.set(
                    TagList(f"Added new node {new_node_id} to the graph at position ({data['x']:.0f}, {data['y']:.0f})")
                )
            else:
                print("Debug: No graph found in state manager")  # Debug output
        else:
            print("Debug: No valid position data received for add_node event")  # Debug output

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