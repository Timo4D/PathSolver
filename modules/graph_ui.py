"""Refactored graph UI module with improved organization."""

import networkx as nx
from htmltools import TagList
from shiny import ui, render, reactive
from shiny.types import FileInfo

from constants import DEFAULT_EDGE_LIST_PATH, STEP_FINISH
from constants import DEFAULT_START_NODE, DEFAULT_TARGET_NODE
from localization import _
from modules.state_manager import state_manager
from modules.ui_components import (
    main_ui, GraphType, create_progress_bar, create_explanation_ui,
    render_graph_generator_settings, render_error_tooltip, render_distances_table,
    create_prediction_game_ui
)
from modules.algorithm_logic import DijkstraStepHandler
from modules.cytoscape.graph_component import render_cytoscape
from modules.solution_quiz import render_solution_quiz
from modules.tutorial_modal import tutorial_modal_server
from utils.graph_generators import generate_random_graph, generate_koot_example, generate_from_edge_list, generate_from_osm_location
from utils.graph_utils import plot_graph, convert_graph_to_cytoscape, get_cytoscape_styles, get_cytoscape_layout
from utils.osm_visualization import create_osm_plotly_figure


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
            # Check if solution quiz should be shown
            # Quiz is shown if: admin enabled it AND (admin forced it OR user enabled it)
            quiz_should_show = state_manager.solution_quiz_enabled.get() and (
                state_manager.force_solution_quiz.get() or  # Admin forced it on
                (input.solution_quiz_enabled() if input.solution_quiz_enabled() is not None else True)  # User choice (default True)
            )
            
            if quiz_should_show:
                return render_solution_quiz()

    @output
    @render.ui
    @reactive.event(
        state_manager.waiting_for_prediction, state_manager.game_score,
        state_manager.consecutive_correct, state_manager.total_predictions,
        state_manager.correct_predictions, state_manager.last_prediction_correct,
        state_manager.game_enabled, state_manager.force_game_mode, state_manager.current_language
    )
    def prediction_game_ui():
        # Only show prediction game UI if game feature is enabled in settings
        if not state_manager.game_enabled():
            return ui.div()
        
        # Check if game should be active (forced or user enabled)
        game_active = state_manager.force_game_mode() or \
                     (input.game_enabled() if input.game_enabled() is not None else False)
        
        # Only show UI if game is actually active
        if not game_active:
            return ui.div()
        
        return create_prediction_game_ui(
            state_manager.waiting_for_prediction.get(),
            state_manager.game_score.get(),
            state_manager.consecutive_correct.get(),
            state_manager.total_predictions.get(),
            state_manager.correct_predictions.get(),
            state_manager.last_prediction_correct.get(),
            state_manager.get_effective_game_difficulty()
        )

    @output
    @render.ui
    @reactive.event(state_manager.step_counter, state_manager.current_language)
    def progress_bar():
        return create_progress_bar(state_manager.step_counter.get())

    @output
    @render.ui
    @reactive.event(state_manager.step_counter, state_manager.step_explanation, state_manager.global_step_counter)
    def explain():
        return create_explanation_ui(
            state_manager.step_counter.get(),
            state_manager.step_explanation.get(),
            state_manager.global_step_counter.get()
        )

    @output
    @render.ui
    @reactive.event(state_manager.nodes_visited)
    def visited_nodes():
        nodes = ", ".join(
            [str(int(node)) for node in state_manager.nodes_visited.get()]
        ) if state_manager.nodes_visited.get() else _("no_nodes_visited")
        return TagList(nodes)
    
    @output
    @render.ui
    @reactive.event(state_manager.current_language)
    def algorithm_explanation():
        """Render algorithm explanation that updates when language changes."""
        from modules.ui_components import algorithm_explanation_ui
        return algorithm_explanation_ui()
    
    @output
    @render.ui
    @reactive.event(state_manager.current_language)
    def dynamic_graph_selection():
        """Dynamic graph selection UI that updates with language."""
        from modules.ui_components import graph_selection_ui
        return graph_selection_ui()
    
    @output
    @render.ui
    @reactive.event(state_manager.current_language)
    def dynamic_start_node():
        """Dynamic start node input that updates with language."""
        return ui.input_numeric(
            "start_node",
            ui.span(_("start_node"), ui.output_ui("start_node_error_message")),
            value=DEFAULT_START_NODE,
            min=0,
        )
    
    @output
    @render.ui
    @reactive.event(state_manager.current_language)
    def dynamic_target_node():
        """Dynamic target node input that updates with language."""
        return ui.input_numeric(
            "target_node",
            ui.span(_("target_node"), ui.output_ui("target_node_error_message")),
            value=DEFAULT_TARGET_NODE,
            min=0,
        )
    
    @output
    @render.ui
    @reactive.event(state_manager.current_language)
    def dynamic_distances():
        """Dynamic distances table that updates with language."""
        from modules.ui_components import distances_ui
        return distances_ui()
    
    @output
    @render.ui
    @reactive.event(state_manager.current_language)
    def dynamic_visited_nodes():
        """Dynamic visited nodes card that updates with language."""
        from modules.ui_components import visited_nodes_ui
        return visited_nodes_ui()

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
        input.start_node, input.target_node, state_manager.game_difficulty,
        state_manager.force_game_difficulty, state_manager.nodes_visited, state_manager.current_node
    )
    def display_distances():
        from modules.ui_components import get_filtered_distances_for_difficulty
        
        # Apply difficulty-based filtering to distances table
        original_df = state_manager.distances_df.get()
        filtered_df = get_filtered_distances_for_difficulty(
            original_df,
            state_manager.get_effective_game_difficulty(),
            state_manager.nodes_visited.get(),
            state_manager.current_node.get()
        )
        
        return render_distances_table(
            filtered_df,
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
    @reactive.event(state_manager.game_enabled, state_manager.force_game_mode, state_manager.current_language)
    def dynamic_game_toggle():
        """Show/hide game toggle based on settings."""
        from modules.ui_components import prediction_game_toggle_ui
        return prediction_game_toggle_ui()

    @output
    @render.ui
    @reactive.event(state_manager.solution_quiz_enabled, state_manager.force_solution_quiz, state_manager.current_language)
    def dynamic_solution_quiz_toggle():
        """Show/hide solution quiz toggle based on settings."""
        from modules.ui_components import solution_quiz_toggle_ui
        return solution_quiz_toggle_ui()
    
    @output
    @render.ui
    @reactive.event(state_manager.game_enabled, state_manager.force_game_mode, state_manager.force_game_difficulty, input.game_enabled, state_manager.current_language)
    def game_difficulty_selector():
        """Show/hide difficulty selector based on settings and game state."""
        from modules.ui_components import game_difficulty_selector_ui
        
        # Only show if game feature is enabled in settings
        if not state_manager.game_enabled():
            return ui.div()
        
        # Check if game should be active (forced or user enabled)
        game_active = state_manager.force_game_mode() or \
                     (input.game_enabled() if input.game_enabled() is not None else False)
        
        # Only show difficulty selector if game is actually active
        if not game_active:
            return ui.div()
        
        return game_difficulty_selector_ui()

    @output
    @render.ui
    @reactive.event(state_manager.visualization_mode, state_manager.current_language)
    def layout_seed_control():
        """Show layout seed input only when matplotlib visualization is selected."""
        if state_manager.visualization_mode() == "matplotlib":
            return ui.input_numeric(
                "layout_seed",
                _("layout_seed"),
                value=42,
                min=0,
                max=999,
                step=1
            )
        else:
            return ui.div()  # Return empty div when cytoscape is selected

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
    @render.ui
    @reactive.event(state_manager.visualization_mode, state_manager.graph)
    def graph_display():
        """Conditionally render either cytoscape, matplotlib, or plotly map graph."""
        graph = state_manager.graph.get()
        
        # If it's an OSM graph, show Plotly map
        if graph and hasattr(graph, 'graph') and 'location' in graph.graph:
            return ui.div(
                ui.output_ui("osm_map_graph"),
                key="osm-map",
                style="height: 600px;"
            )
        
        # Otherwise use normal visualization modes
        mode = state_manager.visualization_mode()
        if mode == "cytoscape":
            from modules.cytoscape.graph_component import output_cytoscape_graph
            # Add a key to force recreation when switching modes
            return ui.div(
                output_cytoscape_graph("cytoscape_graph"),
                key=f"cytoscape-{mode}"
            )
        else:
            return ui.div(
                ui.output_plot("matplotlib_graph", height="600px"),
                key=f"matplotlib-{mode}"
            )

    @reactive.Effect
    @reactive.event(state_manager.visualization_mode)
    def handle_visualization_mode_change():
        """Handle visualization mode changes to ensure proper graph rendering."""
        mode = state_manager.visualization_mode()
        # Force a graph update when switching modes to prevent stale state
        graph = state_manager.graph.get()
        if graph:
            # Trigger a graph update by temporarily setting the same graph
            state_manager.graph.set(graph)
    
    @reactive.Effect
    @reactive.event(input.submit_solution)
    def check_user_solution():
        algorithm_handler.check_user_solution(input)
    
    @reactive.Effect
    @reactive.event(input.game_enabled)
    def toggle_game_mode():
        # Only allow toggle if game feature is enabled in settings
        if state_manager.game_enabled():
            if input.game_enabled():
                state_manager.reset_game_state()
    
    @reactive.Effect
    @reactive.event(input.solution_quiz_enabled)
    def toggle_solution_quiz():
        # This handler doesn't need to do anything special,
        # the quiz logic in render_solution_quiz_ui will handle the user's choice
        pass
    
    @reactive.Effect
    @reactive.event(input.game_difficulty)
    def update_difficulty():
        """Update game difficulty when user changes selection."""
        if (state_manager.game_enabled() and input.game_difficulty() and 
            not state_manager.force_game_difficulty.get()):
            # Only allow user to change difficulty if not forced by instructor
            state_manager.update_game_difficulty(input.game_difficulty())
    
    @reactive.Effect
    @reactive.event(input.cytoscape_graph_node_clicked)
    def handle_prediction_click():
        """Handle node clicks for prediction game."""
        # Only handle predictions if game feature is enabled and waiting for prediction
        if not state_manager.game_enabled() or not state_manager.waiting_for_prediction.get():
            return
        
        data = input.cytoscape_graph_node_clicked()
        if data and "id" in data:
            predicted_node = int(data["id"])
            # Handle the prediction through the algorithm handler
            algorithm_handler.handle_prediction(predicted_node, input)

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
        state_manager.current_node, state_manager.current_edges, state_manager.distances_df,
        state_manager.prediction_candidates, state_manager.visualization_mode, state_manager.game_difficulty,
        state_manager.force_game_difficulty, state_manager.graph_font_size
    )
    def cytoscape_graph():
        """Render the graph using Cytoscape.js."""
        # Only render if visualization mode is cytoscape
        if state_manager.visualization_mode() != "cytoscape":
            # Return empty structure instead of None to prevent payload issues
            return {
                "elements": [],
                "style": get_cytoscape_styles(state_manager.graph_font_size()),
                "layout": get_cytoscape_layout()
            }
            
        graph = state_manager.graph.get()
        if not graph:
            # Return empty structure if no graph
            return {
                "elements": [],
                "style": get_cytoscape_styles(state_manager.graph_font_size()),
                "layout": get_cytoscape_layout()
            }
            
        elements = convert_graph_to_cytoscape(
            graph,
            current_node=state_manager.current_node.get(),
            start_node=input.start_node(),
            target_node=input.target_node(),
            nodes_visited=state_manager.nodes_visited.get(),
            current_edges=state_manager.current_edges.get(),
            distances=state_manager.distances_df.get(),
            prediction_candidates=state_manager.prediction_candidates.get(),
            game_difficulty=state_manager.get_effective_game_difficulty()
        )
        
        return {
            "elements": elements,
            "style": get_cytoscape_styles(state_manager.graph_font_size()),
            "layout": get_cytoscape_layout()
        }

    @output
    @render.plot
    @reactive.event(
        state_manager.graph, input.start_node, input.target_node, 
        state_manager.current_node, state_manager.current_edges, state_manager.distances_df,
        state_manager.visualization_mode, input.layout_seed
    )
    def matplotlib_graph():
        """Render the graph using Matplotlib."""
        # Only render if visualization mode is matplotlib
        if state_manager.visualization_mode() != "matplotlib":
            return None
            
        graph = state_manager.graph.get()
        if not graph:
            return None
            
        start_node = None
        target_node = None
        
        # Parse start and target nodes
        if input.start_node():
            try:
                start_node = int(input.start_node())
            except (ValueError, TypeError):
                start_node = input.start_node()
        
        if input.target_node():
            try:
                target_node = int(input.target_node())
            except (ValueError, TypeError):
                target_node = input.target_node()
        
        # Get layout seed from input or use default
        seed = input.layout_seed() if input.layout_seed() is not None else 42
        
        # Create the plot
        return plot_graph(
            graph,
            start=start_node,
            target=target_node,
            seed=seed,
            distances=state_manager.distances_df.get(),
            current_node=state_manager.current_node.get(),
            current_edges=state_manager.current_edges.get(),
            dark_mode=False,
            final_step=False
        )

    @output
    @render.ui
    @reactive.event(
        state_manager.graph, input.start_node, input.target_node, 
        state_manager.current_node, state_manager.current_edges, state_manager.distances_df
    )
    def osm_map_graph():
        """Render OSM graph using Plotly with map background."""
        graph = state_manager.graph.get()
        if not graph or not (hasattr(graph, 'graph') and 'location' in graph.graph):
            return ui.div("No OSM graph data available")
            
        start_node = None
        target_node = None
        
        # Parse start and target nodes
        if input.start_node():
            try:
                start_node = int(input.start_node())
            except (ValueError, TypeError):
                start_node = input.start_node()
        
        if input.target_node():
            try:
                target_node = int(input.target_node())
            except (ValueError, TypeError):
                target_node = input.target_node()
        
        # Create the Plotly figure with map background
        fig = create_osm_plotly_figure(
            graph,
            start_node=start_node,
            target_node=target_node,
            current_node=state_manager.current_node.get(),
            current_edges=state_manager.current_edges.get(),
            distances_df=state_manager.distances_df.get()
        )
        
        # Return Plotly figure as HTML
        from htmltools import HTML
        return HTML(fig.to_html(include_plotlyjs=True, div_id="osm-map-plot"))

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
                        TagList(_("cannot_delete_min_nodes"))
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
                        TagList(_("cannot_delete_disconnect").format(source=source_id, target=target_id))
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
                    TagList(_("added_new_node").format(node_id=new_node_id, x=data['x'], y=data['y']))
                )
            else:
                print("Debug: No graph found in state manager")  # Debug output
        else:
            print("Debug: No valid position data received for add_node event")  # Debug output

    @reactive.Effect
    @reactive.event(input.cytoscape_graph_edge_creation_started)
    def handle_edge_creation_started():
        """Handle start of edge creation mode."""
        data = input.cytoscape_graph_edge_creation_started()
        if data and "source" in data:
            source_node = data["source"]
            state_manager.step_explanation.set(
                TagList(_("edge_creation_start").format(source=source_node))
            )

    @reactive.Effect
    @reactive.event(input.cytoscape_graph_edge_creation_ended)
    def handle_edge_creation_ended():
        """Handle end of edge creation mode."""
        state_manager.step_explanation.set(
            TagList(_("edge_creation_ended"))
        )

    @reactive.Effect
    @reactive.event(input.cytoscape_graph_create_edge)
    def handle_create_edge():
        """Handle creating a new edge between two nodes."""
        data = input.cytoscape_graph_create_edge()
        if data and "source" in data and "target" in data:
            source_id = int(data["source"])
            target_id = int(data["target"])
            graph = state_manager.graph.get()
            
            if graph and source_id in graph.nodes() and target_id in graph.nodes():
                # Check if edge already exists
                if graph.has_edge(source_id, target_id):
                    state_manager.step_explanation.set(
                        TagList(_("edge_already_exists").format(source=source_id, target=target_id))
                    )
                    return
                
                # Create a copy of the graph and add the new edge
                graph_copy = graph.copy()
                # Add edge with default weight of 1
                graph_copy.add_edge(source_id, target_id, weight=1)
                
                # Update the graph in state manager
                state_manager.graph.set(graph_copy)
                
                # Reset algorithm state since graph structure changed
                state_manager.reset_algorithm_state()
                
                state_manager.step_explanation.set(
                    TagList(_("created_edge").format(source=source_id, target=target_id))
                )
            else:
                state_manager.step_explanation.set(
                    TagList(_("cannot_create_invalid_nodes").format(source=source_id, target=target_id))
                )

    @reactive.Effect
    @reactive.event(input.cytoscape_graph_update_edge_weight)
    def handle_update_edge_weight():
        """Handle updating the weight of an edge."""
        data = input.cytoscape_graph_update_edge_weight()
        if data and "source" in data and "target" in data and "weight" in data:
            source_id = int(data["source"])
            target_id = int(data["target"])
            new_weight = float(data["weight"])
            graph = state_manager.graph.get()
            
            if graph and graph.has_edge(source_id, target_id):
                # Create a copy of the graph and update the edge weight
                graph_copy = graph.copy()
                graph_copy[source_id][target_id]['weight'] = new_weight
                
                # Update the graph in state manager
                state_manager.graph.set(graph_copy)
                
                # Reset algorithm state since edge weights changed
                state_manager.reset_algorithm_state()
                
                state_manager.step_explanation.set(
                    TagList(_("updated_edge_weight").format(source=source_id, target=target_id, weight=new_weight))
                )
            else:
                state_manager.step_explanation.set(
                    TagList(_("cannot_update_nonexistent").format(source=source_id, target=target_id))
                )

    # Initialize tutorial modal server and get tutorial object
    tutorial = tutorial_modal_server(input, output, session)
    
    # Add tutorial styles output
    @output
    @render.ui
    def tutorial_styles():
        if not tutorial.is_active():
            return ""
        
        current_step = tutorial.get_current_step()
        highlight_element = current_step.get("highlight_element")
        
        if not highlight_element:
            return ""
        
        # CSS to highlight the target element with enhanced visibility
        return ui.tags.style(f"""
            #{highlight_element} {{
                border: 4px solid #ff6b35 !important;
                border-radius: 8px !important;
                box-shadow: 0 0 20px rgba(255, 107, 53, 0.6) !important;
                position: relative !important;
                z-index: 1050 !important;
                background-color: rgba(255, 255, 255, 0.95) !important;
            }}
            
            #{highlight_element}::before {{
                content: "";
                position: absolute;
                top: -8px;
                left: -8px;
                right: -8px;
                bottom: -8px;
                border: 2px dashed #ff6b35;
                border-radius: 12px;
                z-index: -1;
            }}
            
            
            /* Special handling for different UI elements */
            #{highlight_element}.form-control,
            #{highlight_element}.form-select {{
                background-color: rgba(255, 255, 255, 1) !important;
            }}
            
            #{highlight_element} .card {{
                background-color: rgba(255, 255, 255, 0.98) !important;
            }}
        """)


def _update_graph_based_on_selection(input):
    """Update graph based on user selection."""
    if input.selectize_graph() == GraphType.RANDOM_GRAPH.value:
        if input.k_slider() > input.n_slider():
            state_manager.step_explanation.set(
                TagList(_("select_k_not_smaller_n"))
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
    elif input.selectize_graph() == GraphType.OSM_LOCATION.value:
        location = input.osm_location_input()
        distance = input.osm_distance_input()
        if location and location.strip():
            result = generate_from_osm_location(location.strip(), distance)
            if isinstance(result, str):
                state_manager.invalid_edge_list.set(True)
                state_manager.step_explanation.set(TagList(result))
            else:
                state_manager.invalid_edge_list.set(False)
                state_manager.graph.set(result)
        else:
            state_manager.step_explanation.set(TagList("Please enter a location"))