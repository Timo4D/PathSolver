"""UI components for PathSolver application."""

from enum import Enum
from operator import contains

import pandas as pd
from htmltools import TagList
from shiny import render, ui
from shiny.types import FileInfo

from constants import (COLOR_ACTIVE, COLOR_INACTIVE, COLOR_START_NODE,
                       COLOR_TARGET_NODE,
                       DEFAULT_NEIGHBORS, DEFAULT_NODES, DEFAULT_REWIRE_PROB,
                       DEFAULT_START_NODE, DEFAULT_TARGET_NODE,
                       ERROR_INVALID_DATA, ERROR_NODE_NOT_IN_GRAPH,
                       MAX_NEIGHBORS, MAX_NODES, MAX_REWIRE_PROB,
                       MIN_NEIGHBORS, MIN_NODES, MIN_REWIRE_PROB,
                       STEP_HEADINGS)
from modules.cytoscape.graph_component import output_cytoscape_graph
from modules.dijkstra_explanation import dijkstra_explanation
from modules.tutorial_modal import tutorial_modal
from utils.icons import warning as warning_icon


class GraphType(Enum):
    RANDOM_GRAPH = "random_graph"
    KOOT_EXAMPLE_DEUTSCHLAND = "koot_example_deutschland"
    EDGE_LIST = "edge_list"
    CSV_FILE = "csv_file"


def main_ui():
    """Main application UI layout."""
    return ui.page_fluid(
        ui.output_ui("tutorial_styles"),  # Add tutorial styles
        ui.layout_sidebar(
            ui.sidebar(
                tutorial_modal(),
                ui.output_ui("dynamic_game_toggle"),
                ui.output_ui("game_difficulty_selector"),
                graph_selection_ui(),
                ui.output_ui("graph_generator_settings"),
                ui.input_numeric(
                    "start_node",
                    ui.span("Start Node", ui.output_ui("start_node_error_message")),
                    value=DEFAULT_START_NODE,
                    min=0,
                ),
                ui.input_numeric(
                    "target_node",
                    ui.span("Target Node", ui.output_ui("target_node_error_message")),
                    value=DEFAULT_TARGET_NODE,
                    min=0,
                ),
                ui.output_ui("layout_seed_control"),
            ),
            ui.output_ui("graph_display"),
            ui.output_ui("progress_bar"),
            ui.output_ui("prediction_game_ui"),
            ui.output_ui("explain"),
            ui.row(
                ui.column(6, ui.output_ui("render_solution_quiz_ui"), distances_ui()),
                ui.column(6, visited_nodes_ui(), algorithm_explanation_ui()),
            ),
        ),
    )


def graph_selection_ui():
    """Graph selection dropdown UI."""
    return ui.input_selectize(
        "selectize_graph",
        "Select a Graph",
        {
            GraphType.RANDOM_GRAPH.value: "Random Graph",
            GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value: "Germany Example",
            GraphType.EDGE_LIST.value: "Import from Edgelist",
            GraphType.CSV_FILE.value: "Upload a CSV file",
        },
        selected=GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value,
    )


def distances_ui():
    """Distances table UI component."""
    return ui.card(
        ui.card_header("Distances between nodes"),
        ui.card_body(
            ui.output_data_frame("display_distances"),
        ),
    )


def get_filtered_distances_for_difficulty(df, difficulty, nodes_visited, current_node):
    """Filter distances table based on game difficulty."""
    if difficulty == "easy":
        # Easy: Show all distances
        return df
    elif difficulty == "medium":
        # Medium: Show distances only for visited nodes and current node
        if df.empty or "Cost" not in df.columns:
            return df
        
        filtered_df = df.copy()
        # Convert Cost column to object type to allow mixed types
        filtered_df["Cost"] = filtered_df["Cost"].astype(object)
        
        # Get nodes that should NOT show distances (unvisited and not current)
        for index, row in filtered_df.iterrows():
            node_id = None
            if "Node" in row:
                try:
                    node_id = int(row["Node"])
                except (ValueError, TypeError):
                    node_id = row["Node"]
            else:
                node_id = index
            
            # Hide distance if node is not visited and not current
            if node_id not in nodes_visited and node_id != current_node:
                filtered_df.at[index, "Cost"] = "?"
        
        return filtered_df
    elif difficulty == "hard":
        # Hard: Hide all distances
        if df.empty or "Cost" not in df.columns:
            return df
        
        filtered_df = df.copy()
        # Convert Cost column to object type to allow mixed types
        filtered_df["Cost"] = filtered_df["Cost"].astype(object)
        filtered_df["Cost"] = "?"
        return filtered_df
    
    return df


def visited_nodes_ui():
    """Visited nodes display UI component."""
    return ui.card(
        ui.card_header("Visited Nodes"), ui.card_body(ui.output_ui("visited_nodes"))
    )


def algorithm_explanation_ui():
    """Algorithm explanation UI component."""
    return ui.card(
        ui.card_header("Explanation of the Algorithm"),
        ui.card_body(dijkstra_explanation),
    )


def game_difficulty_selector_ui():
    """Difficulty selector for prediction game mode."""
    from modules.state_manager import state_manager
    
    # Only show if game feature is enabled in settings
    if not state_manager.game_enabled():
        return ui.div()
    
    # Check if difficulty is forced by instructor
    forced_difficulty = state_manager.force_game_difficulty.get()
    
    if forced_difficulty:
        # Show read-only forced difficulty
        difficulty_labels = {
            "easy": "🟢 Easy - Full hints and distances shown",
            "medium": "🟡 Medium - Some visual aids hidden", 
            "hard": "🔴 Hard - Minimal visual information"
        }
        
        return ui.div(
            ui.div(
                ui.strong(f"🎯 Game Difficulty (Forced by Instructor)"),
                style="margin-bottom: 5px;"
            ),
            ui.div(
                difficulty_labels.get(forced_difficulty, forced_difficulty.title()),
                style="padding: 8px; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;"
            ),
            ui.p(
                "The difficulty level has been set by your instructor and cannot be changed.",
                style="font-size: 0.8em; color: #6c757d; margin: 5px 0 0 0;"
            ),
            style="margin-bottom: 10px;"
        )
    else:
        # Show normal selector
        return ui.div(
            ui.input_selectize(
                "game_difficulty",
                "🎯 Game Difficulty",
                choices={
                    "easy": "🟢 Easy",
                    "medium": "🟡 Medium", 
                    "hard": "🔴 Hard"
                },
                selected="medium",
            ),
            style="margin-bottom: 10px;"
        )


def prediction_game_toggle_ui():
    """Toggle for enabling prediction game mode - only shown if enabled in settings."""
    from modules.state_manager import state_manager
    
    if not state_manager.game_enabled():
        return ui.div()  # Return empty div if game is disabled in settings
    
    # If force game mode is enabled, show a read-only toggle that's always on
    if state_manager.force_game_mode():
        return ui.div(
            ui.div(
                ui.strong("🎮 Prediction Game Mode (Forced On)"),
                style="margin-bottom: 5px;"
            ),
            ui.p(
                "Game mode is forced on by administrator settings.",
                style="font-size: 0.8em; color: #6c757d; margin: 0;"
            )
        )
    
    return ui.input_switch(
        "game_enabled",
        "🎮 Prediction Game Mode",
        value=False,
    )


def create_prediction_game_ui(
    waiting_for_prediction, game_score, consecutive_correct, 
    total_predictions, correct_predictions, last_prediction_correct, game_difficulty=None
):
    """Create prediction game UI when waiting for user prediction."""
    if not waiting_for_prediction:
        return None
    
    # Calculate accuracy percentage
    accuracy = 0
    if total_predictions > 0:
        accuracy = round((correct_predictions / total_predictions) * 100, 1)
    
    # Feedback message for last prediction
    feedback_message = ""
    feedback_style = ""
    if last_prediction_correct is not None:
        if last_prediction_correct:
            feedback_message = f"✅ Correct! +{10 + min(consecutive_correct * 2, 20)} points"
            feedback_style = "color: #28a745; font-weight: bold;"
        else:
            feedback_message = "❌ Incorrect. The algorithm chose a different node."
            feedback_style = "color: #dc3545; font-weight: bold;"
    
    return ui.card(
        ui.card_header(
            ui.div(
                "🎯 Prediction Challenge",
                style="display: inline-block; margin-right: 20px; font-size: 1.1em; font-weight: bold;"
            ),
            ui.div(
                ui.span(
                    f"🏆 {game_score}",
                    style="display: inline-block; margin-right: 15px; font-size: 1.3em; font-weight: bold; color: #28a745; background-color: #d4edda; padding: 4px 8px; border-radius: 6px; border: 2px solid #c3e6cb;"
                ),
                ui.span(
                    f"🔥 {consecutive_correct}",
                    style="display: inline-block; margin-right: 15px; font-size: 1.1em; font-weight: bold; color: #fd7e14;"
                ),
                ui.span(
                    f"📊 {accuracy}%",
                    style="display: inline-block; font-size: 1.1em; font-weight: bold; color: #007bff; background-color: #cce5ff; padding: 4px 8px; border-radius: 6px; border: 2px solid #99d6ff;"
                ),
                style="display: inline-block;"
            ),
            style="display: flex; justify-content: space-between; align-items: center;"
        ),
        ui.card_body(
            ui.div(feedback_message, style=feedback_style) if feedback_message else None,
            ui.h4("Which node will Dijkstra visit next?", style="color: #007bff; margin-top: 10px;"),
            ui.p(
                "Look at the distances table and click on the unvisited node with the lowest cost!",
                style="margin-bottom: 15px;"
            ),
            ui.div(
                _get_difficulty_hint(game_difficulty),
                style="background-color: #e7f3ff; padding: 10px; border-radius: 5px; font-style: italic;"
            )
        ),
        style="border: 2px solid #007bff; box-shadow: 0 4px 8px rgba(0,123,255,0.2);"
    )


def create_progress_bar(step_counter):
    """Create progress bar UI."""
    return TagList(
        ui.layout_columns(
            ui.input_action_button("prev_step", "Previous Step"),
            *[
                ui.div(
                    style=f"background-color: {COLOR_ACTIVE if step_counter >= i else COLOR_INACTIVE}; height: 30px; width: 100%; margin: auto; display: flex; align-items: center; justify-content: center;"
                )
                for i in range(4)
            ],
            ui.input_action_button("next_step", "Next Step"),
        )
    )


def create_explanation_ui(step_counter, step_explanation, global_step_counter=None):
    """Create step explanation UI."""
    # Create the main heading
    heading = STEP_HEADINGS.get(step_counter)
    
    # Add global step counter if provided
    if global_step_counter is not None and global_step_counter > 0:
        heading = f"Overall Progress: Step {global_step_counter} | {heading}"
    
    return TagList(
        ui.h1(heading, style="margin-bottom: 0;"),
        ui.p(step_explanation, style="margin-top: 0;"),
    )


def render_graph_generator_settings(graph_type):
    """Render settings UI based on selected graph type."""
    if graph_type == GraphType.RANDOM_GRAPH.value:
        return ui.TagList(
            ui.input_slider(
                "n_slider", "Number of Nodes", MIN_NODES, MAX_NODES, DEFAULT_NODES
            ),
            ui.input_slider(
                "k_slider",
                "Neighbors in a ring topology",
                MIN_NEIGHBORS,
                MAX_NEIGHBORS,
                DEFAULT_NEIGHBORS,
            ),
            ui.input_slider(
                "p_slider",
                "Probability of rewiring each edge",
                MIN_REWIRE_PROB,
                MAX_REWIRE_PROB,
                DEFAULT_REWIRE_PROB,
            ),
        )
    elif graph_type == GraphType.EDGE_LIST.value:
        return ui.TagList(
            ui.input_text_area(
                "edge_list_input",
                ui.span("Edge List", ui.output_ui("edge_list_error_message")),
                "0 1 10\n1 2 10\n2 0 20",
                rows=10,
                autoresize=True,
            )
        )
    elif graph_type == GraphType.CSV_FILE.value:
        return ui.TagList(
            ui.input_file(
                "edge_list_file",
                ui.span("Upload an edge list", ui.output_ui("edge_list_error_message")),
            )
        )


def render_error_tooltip(has_error):
    """Render error tooltip if there's an error."""
    return ui.tooltip(warning_icon, "Your input is invalid") if has_error else None


def render_distances_table(df, start_node, target_node):
    """Render the distances data frame with styling."""
    if contains(df.columns, "Node"):
        try:
            index_start = int(
                df.index[df["Node"].astype(int) == int(start_node)].item()
            )
            index_target = int(
                df.index[df["Node"].astype(int) == int(target_node)].item()
            )
        except ValueError:
            df = pd.DataFrame({"Error": [ERROR_NODE_NOT_IN_GRAPH]})
            return render.DataTable(df, width="100%")

        try:
            styles = [
                {"rows": index_start, "style": {"background-color": COLOR_START_NODE}},
                {
                    "rows": index_target,
                    "style": {"background-color": COLOR_TARGET_NODE},
                },
            ]
            return render.DataTable(df, width="100%", styles=styles)
        except TypeError:
            df = pd.DataFrame({"Error": [ERROR_INVALID_DATA]})
            return render.DataTable(df, width="100%")
    else:
        try:
            styles = [
                {
                    "rows": [int(start_node)],
                    "style": {"background-color": COLOR_START_NODE},
                },
                {
                    "rows": [int(target_node)],
                    "style": {"background-color": COLOR_TARGET_NODE},
                },
            ]
            return render.DataTable(df, width="100%", styles=styles)
        except TypeError:
            df = pd.DataFrame({"Error": [ERROR_INVALID_DATA]})
            return render.DataTable(df, width="100%")


def _get_difficulty_hint(difficulty):
    """Get hint text based on game difficulty level."""
    if difficulty == "easy":
        return "💡 Easy Mode: The algorithm always selects the unvisited node with the minimum distance. Look at the distances table for guidance\!"
    elif difficulty == "medium":
        return "💡 Medium Mode: The algorithm selects the unvisited node with the lowest cost. Some visual aids are reduced."
    elif difficulty == "hard":
        return "💡 Hard Mode: Think carefully about which unvisited node has the shortest path from the start. Visual information is minimal\!"
    else:
        return "💡 The algorithm always selects the unvisited node with the minimum distance."
