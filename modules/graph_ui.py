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
    create_prediction_game_ui, create_prediction_feedback_ui
)
from modules.algorithm_logic import DijkstraStepHandler
from modules.cytoscape.graph_component import render_cytoscape
from modules.solution_quiz import render_solution_quiz
from modules.tutorial_modal import tutorial_modal_server
from utils.graph_generators import (
    generate_random_graph, generate_koot_example, generate_from_edge_list, generate_from_csv,
    generate_simple_path, generate_grid_graph, generate_european_cities
)
from utils.graph_utils import plot_graph, convert_graph_to_cytoscape, get_cytoscape_styles, get_cytoscape_layout, convert_graph_to_edgelist, convert_graph_to_csv
from utils.user_logger import get_logger


def graph_ui():
    """Main graph UI function."""
    return main_ui()


def graph_ui_server(input, output, session):
    """Main server logic for the graph UI."""
    # Initialize algorithm handler
    algorithm_handler = DijkstraStepHandler(state_manager)

    # Load task graph on initialization if in task mode
    @reactive.Effect
    @reactive.event(state_manager.current_task_index, state_manager.task_mode_enabled)
    def load_task_graph():
        """Load graph based on current task when in task mode, or default graph in free mode."""
        if state_manager.is_task_mode_active():
            task = state_manager.get_current_task()
            if task:
                # Log task start (when task changes or task mode is enabled)
                logger = get_logger()
                logger.log_task_started(
                    task_index=task.get('task_number'),
                    task_description=task.get('description'),
                    graph_type=task.get('graph_type')
                )

                # Generate graph based on task configuration
                if task["graph_type"] == "koot_example":
                    graph = generate_koot_example()
                elif task["graph_type"] == "simple_path":
                    graph = generate_simple_path()
                elif task["graph_type"] == "grid_graph":
                    graph = generate_grid_graph()
                elif task["graph_type"] == "european_cities":
                    graph = generate_european_cities()
                elif task["graph_type"] == "random":
                    params = task.get("params", {"n": 10, "k": 4, "p": 0.3})
                    graph = generate_random_graph(params["n"], params["k"], params["p"])
                else:
                    # Default fallback
                    graph = generate_koot_example()

                state_manager.graph.set(graph)
        else:
            # In free mode, ensure we have a graph loaded (use Germany example as default)
            if state_manager.graph.get() is None or not state_manager.graph.get().nodes():
                graph = generate_koot_example()
                state_manager.graph.set(graph)

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
    @reactive.event(
        state_manager.prediction_feedback_message,
        state_manager.last_prediction_correct,
        state_manager.game_score,
        state_manager.consecutive_correct,
        state_manager.total_predictions,
        state_manager.correct_predictions,
        state_manager.game_enabled,
        state_manager.force_game_mode
    )
    def prediction_feedback_ui():
        """Display persistent prediction feedback."""
        # Only show feedback if game feature is enabled in settings
        if not state_manager.game_enabled():
            return ui.div()

        # Check if game should be active (forced or user enabled)
        game_active = state_manager.force_game_mode() or \
                     (input.game_enabled() if input.game_enabled() is not None else False)

        # Only show feedback if game is actually active
        if not game_active:
            return ui.div()

        return create_prediction_feedback_ui(
            state_manager.prediction_feedback_message.get(),
            state_manager.last_prediction_correct.get(),
            state_manager.game_score.get(),
            state_manager.consecutive_correct.get(),
            state_manager.total_predictions.get(),
            state_manager.correct_predictions.get()
        )

    @output
    @render.ui
    @reactive.event(state_manager.step_counter, state_manager.current_language, state_manager.waiting_for_prediction)
    def progress_bar():
        return create_progress_bar(
            state_manager.step_counter.get(), 
            state_manager.waiting_for_prediction.get()
        )

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
    @reactive.event(state_manager.task_mode_enabled, state_manager.current_task_index)
    def dynamic_tutorial_button():
        """Dynamic tutorial button - hidden in task mode."""
        if state_manager.is_task_mode_active():
            return ui.div()  # Hide tutorial button in task mode
        else:
            from modules.tutorial_modal import tutorial_modal
            return tutorial_modal()

    @output
    @render.ui
    @reactive.event(state_manager.current_language, state_manager.task_mode_enabled, state_manager.current_task_index)
    def dynamic_graph_selection():
        """Dynamic graph selection UI that updates with language or task mode."""
        # If in task mode, show task progress instead of graph selector
        if state_manager.is_task_mode_active():
            task = state_manager.get_current_task()
            total_tasks = state_manager.get_total_tasks()
            current_num = state_manager.current_task_index.get() + 1

            return ui.div(
                ui.h4(f"Task {current_num} of {total_tasks}", style="margin-bottom: 10px;"),
                ui.p(task['description'], style="font-size: 14px; color: #666;"),
                style="padding: 15px; background-color: #f0f8ff; border-radius: 5px; border-left: 4px solid #2196F3;"
            )
        else:
            from modules.ui_components import graph_selection_ui
            return graph_selection_ui()
    
    @output
    @render.ui
    @reactive.event(state_manager.current_language, state_manager.task_mode_enabled, state_manager.current_task_index)
    def dynamic_start_node():
        """Dynamic start node input that updates with language or task mode."""
        if state_manager.is_task_mode_active():
            task = state_manager.get_current_task()
            return ui.div(
                ui.strong(_("start_node")),
                ui.p(str(task['start_node']), style="font-size: 18px; margin: 5px 0; color: #2196F3;"),
                style="padding: 10px; background-color: #f5f5f5; border-radius: 5px;"
            )
        else:
            return ui.input_numeric(
                "start_node",
                ui.span(_("start_node"), ui.output_ui("start_node_error_message")),
                value=DEFAULT_START_NODE,
                min=0,
            )

    @output
    @render.ui
    @reactive.event(state_manager.current_language, state_manager.task_mode_enabled, state_manager.current_task_index)
    def dynamic_target_node():
        """Dynamic target node input that updates with language or task mode."""
        if state_manager.is_task_mode_active():
            task = state_manager.get_current_task()
            return ui.div(
                ui.strong(_("target_node")),
                ui.p(str(task['target_node']), style="font-size: 18px; margin: 5px 0; color: #2196F3;"),
                style="padding: 10px; background-color: #f5f5f5; border-radius: 5px;"
            )
        else:
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
        # Block next step if waiting for prediction
        if state_manager.waiting_for_prediction.get():
            return
        algorithm_handler.handle_next_step(input)

    @reactive.Effect
    def update_graph():
        _update_graph_based_on_selection(input)

    @output
    @render.data_frame
    @reactive.event(
        state_manager.distances_df, state_manager.step_counter,
        state_manager.game_difficulty,
        state_manager.force_game_difficulty, state_manager.nodes_visited, state_manager.current_node,
        state_manager.task_mode_enabled, state_manager.current_task_index
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
            state_manager.get_start_node(input),
            state_manager.get_target_node(input)
        )

    @reactive.Effect
    @reactive.event(state_manager.current_task_index)
    def reset_dijkstra_on_task_change():
        """Reset algorithm state when task changes."""
        if state_manager.is_task_mode_active():
            state_manager.reset_algorithm_state()

    @reactive.Effect
    def reset_dijkstra_on_node_change():
        """Reset algorithm when start/target nodes change in free mode."""
        # Only listen to input changes in free mode
        if not state_manager.is_task_mode_active():
            try:
                # Access the inputs to create reactive dependency
                if hasattr(input, 'start_node'):
                    _ = input.start_node()
                if hasattr(input, 'target_node'):
                    _ = input.target_node()
                # Reset the algorithm
                state_manager.reset_algorithm_state()
            except:
                pass

    @reactive.Effect
    def initialize_distances():
        state_manager.reset_algorithm_state()

    @output
    @render.ui
    @reactive.event(state_manager.task_mode_enabled, state_manager.current_task_index)
    def graph_generator_settings():
        """Render graph generator settings - hidden in task mode."""
        if state_manager.is_task_mode_active():
            return ui.div()  # Hide settings in task mode

        # Get graph type, default to KOOT_EXAMPLE if None (when transitioning from task mode)
        graph_type = input.selectize_graph() if input.selectize_graph() is not None else GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value
        return render_graph_generator_settings(graph_type)

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
    @reactive.event(state_manager.visualization_mode)
    def graph_display():
        """Conditionally render either cytoscape or matplotlib graph."""
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
            logger = get_logger()
            logger.log_game_toggled(enabled=input.game_enabled())

            if input.game_enabled():
                # Enabling game mode - reset game state
                state_manager.reset_game_state()
            else:
                # Disabling game mode - reset game state and algorithm if in progress
                state_manager.reset_game_state()
                # Check if algorithm is in progress (step counter > 0) and reset it
                if state_manager.step_counter.get() > 0:
                    state_manager.reset_algorithm_state()
    
    @reactive.Effect
    @reactive.event(input.solution_quiz_enabled)
    def toggle_solution_quiz():
        # Log solution quiz toggle
        logger = get_logger()
        logger.log_solution_quiz_toggled(enabled=input.solution_quiz_enabled())

    @reactive.Effect
    @reactive.event(input.game_difficulty)
    def update_difficulty():
        """Update game difficulty when user changes selection."""
        if (state_manager.game_enabled() and input.game_difficulty() and
            not state_manager.force_game_difficulty.get()):
            # Log difficulty change
            old_difficulty = state_manager.game_difficulty.get()
            new_difficulty = input.game_difficulty()
            if old_difficulty != new_difficulty:
                logger = get_logger()
                logger.log_difficulty_changed(old_difficulty, new_difficulty)

            # Only allow user to change difficulty if not forced by instructor
            state_manager.update_game_difficulty(new_difficulty)
    
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
                with open(edge_list, 'r') as file:
                    file_content = file.read()

                # Detect if file is CSV format (contains commas) or edge list format (spaces)
                if ',' in file_content:
                    # CSV format
                    result = generate_from_csv(file_content)
                else:
                    # Edge list format
                    result = generate_from_edge_list(file_content)

                if isinstance(result, str):
                    state_manager.invalid_edge_list.set(True)
                    state_manager.step_explanation.set(TagList(result))
                else:
                    state_manager.invalid_edge_list.set(False)
                    state_manager.graph.set(result)
            except FileNotFoundError:
                state_manager.invalid_edge_list.set(True)
                state_manager.step_explanation.set(
                    TagList(f"File not found: {edge_list}")
                )

    @output
    @render_cytoscape
    @reactive.event(
        state_manager.graph,
        state_manager.current_node, state_manager.current_edges, state_manager.distances_df,
        state_manager.prediction_candidates, state_manager.visualization_mode, state_manager.game_difficulty,
        state_manager.force_game_difficulty, state_manager.graph_font_size,
        state_manager.task_mode_enabled, state_manager.current_task_index
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
            start_node=state_manager.get_start_node(input),
            target_node=state_manager.get_target_node(input),
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
        state_manager.graph,
        state_manager.current_node, state_manager.current_edges, state_manager.distances_df,
        state_manager.visualization_mode, input.layout_seed,
        state_manager.task_mode_enabled, state_manager.current_task_index
    )
    def matplotlib_graph():
        """Render the graph using Matplotlib."""
        # Only render if visualization mode is matplotlib
        if state_manager.visualization_mode() != "matplotlib":
            return None

        graph = state_manager.graph.get()
        if not graph:
            return None

        # Get start and target nodes using helper functions
        start_node = state_manager.get_start_node(input)
        target_node = state_manager.get_target_node(input)

        # Ensure they're integers if possible
        try:
            start_node = int(start_node) if start_node is not None else None
            target_node = int(target_node) if target_node is not None else None
        except (ValueError, TypeError):
            pass
        
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

    @reactive.Effect
    @reactive.event(input.cytoscape_graph_set_start_node)
    def handle_set_start_node():
        """Handle setting start node from context menu."""
        # Disable context menu in task mode
        if state_manager.is_task_mode_active():
            return

        data = input.cytoscape_graph_set_start_node()
        if data and "id" in data:
            node_id = int(data["id"])
            graph = state_manager.graph.get()
            if graph and node_id in graph.nodes():
                # Log the action
                logger = get_logger()
                logger.log_start_node_set(str(node_id), method="context_menu")

                # Update the start node input programmatically
                ui.update_selectize("start_node", selected=str(node_id))
                # Reset algorithm state when start node changes
                state_manager.reset_algorithm_state()

    @reactive.Effect
    @reactive.event(input.cytoscape_graph_set_target_node)
    def handle_set_target_node():
        """Handle setting target node from context menu."""
        # Disable context menu in task mode
        if state_manager.is_task_mode_active():
            return

        data = input.cytoscape_graph_set_target_node()
        if data and "id" in data:
            node_id = int(data["id"])
            graph = state_manager.graph.get()
            if graph and node_id in graph.nodes():
                # Log the action
                logger = get_logger()
                logger.log_target_node_set(str(node_id), method="context_menu")

                # Update the target node input programmatically
                ui.update_selectize("target_node", selected=str(node_id))
                # Reset algorithm state when target node changes
                state_manager.reset_algorithm_state()

    @reactive.Effect
    @reactive.event(input.cytoscape_graph_delete_node)
    def handle_delete_node():
        """Handle deleting a node from context menu."""
        # Disable context menu in task mode
        if state_manager.is_task_mode_active():
            return

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
                
                # Log the action
                logger = get_logger()
                logger.log_node_deleted(str(node_id))

                # Remove the node and all its edges from the NetworkX graph
                graph_copy = graph.copy()
                graph_copy.remove_node(node_id)

                # Update the graph in state manager
                state_manager.graph.set(graph_copy)

                # Clear start/target if they were the deleted node (only in free mode)
                if not state_manager.is_task_mode_active():
                    current_start = state_manager.get_start_node(input)
                    current_target = state_manager.get_target_node(input)

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
        # Disable context menu in task mode
        if state_manager.is_task_mode_active():
            return

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

                # Log the action
                logger = get_logger()
                logger.log_edge_deleted(str(source_id), str(target_id))

                # Update the graph in state manager
                state_manager.graph.set(graph_copy)

                # Reset algorithm state since graph structure changed
                state_manager.reset_algorithm_state()

    @reactive.Effect
    @reactive.event(input.cytoscape_graph_add_node)
    def handle_add_node():
        """Handle adding a new node from context menu."""
        # Disable context menu in task mode
        if state_manager.is_task_mode_active():
            return

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

                # Log the action
                logger = get_logger()
                logger.log_node_added(str(new_node_id), position={"x": data["x"], "y": data["y"]})

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
                
                # Log the action
                logger = get_logger()
                logger.log_edge_added(str(source_id), str(target_id), weight=1)

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
                # Get old weight for logging
                old_weight = graph[source_id][target_id]['weight']

                # Log the action
                logger = get_logger()
                logger.log_edge_weight_updated(str(source_id), str(target_id), old_weight, new_weight)

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

    @reactive.Effect
    @reactive.event(state_manager.graph)
    def update_edge_list_from_graph():
        """Update edge list input when graph changes via Cytoscape."""
        # Only update if user is in edge list mode
        if input.selectize_graph() == GraphType.EDGE_LIST.value:
            graph = state_manager.graph.get()
            if graph and len(graph.edges) > 0:
                # Convert graph to edge list format
                edge_list_str = convert_graph_to_edgelist(graph)
                # Update the text area input
                ui.update_text_area("edge_list_input", value=edge_list_str)

    @render.download(filename="graph_edgelist.csv")
    def download_edgelist():
        """Download current graph as CSV file."""
        graph = state_manager.graph.get()
        if graph:
            csv_content = convert_graph_to_csv(graph)
            yield csv_content
        else:
            yield "source,target,weight\n"

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
    # Skip if in task mode - graph is controlled by tasks
    if state_manager.is_task_mode_active():
        return

    logger = get_logger()

    if input.selectize_graph() == GraphType.RANDOM_GRAPH.value:
        n = input.n_slider()
        k = input.k_slider()

        # Validate ring topology constraints
        if k >= n:
            state_manager.step_explanation.set(
                TagList(_("select_k_not_smaller_n"))
            )
        else:
            graph = generate_random_graph(n, k, input.p_slider())
            state_manager.graph.set(graph)
            logger.log_graph_selected("random", {"n": n, "k": k, "p": input.p_slider()})
    elif input.selectize_graph() == GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value:
        state_manager.graph.set(generate_koot_example())
        logger.log_graph_selected("koot_example")
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
                logger.log_graph_selected("edge_list")
        else:
            state_manager.graph.set(edge_list_input)
            logger.log_graph_selected("edge_list")