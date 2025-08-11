"""State management for PathSolver application."""

import json
import os
import pandas as pd
import networkx as nx
from shiny import reactive
from htmltools import TagList

from constants import INITIAL_EXPLANATION


class StateManager:
    """Manages all reactive state for the PathSolver application."""
    
    def __init__(self):
        # Load configuration
        self.config = self._load_config()
        
        # Graph and algorithm state
        self.distances_df = reactive.Value(pd.DataFrame())
        self.graph = reactive.Value(nx.Graph())
        self.solution = reactive.Value()
        
        # Algorithm progress state
        self.step_counter = reactive.Value(0)
        self.global_step_counter = reactive.Value(0)  # Always increasing step counter
        self.current_node = reactive.Value(None)
        self.current_edges = reactive.Value([])
        self.distance = reactive.Value(0)
        self.nodes_visited = reactive.Value([])
        
        # UI state
        self.step_explanation = reactive.Value(TagList(INITIAL_EXPLANATION))
        
        # Error state
        self.invalid_edge_list = reactive.Value(False)
        self.start_node_error = reactive.Value(False)
        self.target_node_error = reactive.Value(False)
        
        # History for undo functionality
        self.state_history = reactive.Value([])
        
        # Prediction game state
        self.game_enabled = reactive.Value(self.config["settings"]["game_feature_enabled"])
        self.game_difficulty = reactive.Value("easy")  # easy, medium, hard
        self.game_score = reactive.Value(0)
        self.consecutive_correct = reactive.Value(0)
        self.waiting_for_prediction = reactive.Value(False)
        self.prediction_candidates = reactive.Value([])
        self.last_prediction_correct = reactive.Value(None)
        self.total_predictions = reactive.Value(0)
        self.correct_predictions = reactive.Value(0)
        
        # Settings state
        self.visualization_mode = reactive.Value(self.config["settings"]["visualization_mode"])
        self.force_game_mode = reactive.Value(self.config["settings"]["force_game_mode"])
        self.force_game_difficulty = reactive.Value(self.config["settings"]["force_game_difficulty"])
        self.graph_font_size = reactive.Value(self.config["settings"].get("graph_font_size", 16))  # Default 16px
        self.settings_unlocked = reactive.Value(not self.config["settings"]["password_protected"])
        self.admin_password = self.config["settings"]["admin_password"]
    
    def save_state(self):
        """Save current state for undo functionality."""
        state = {
            "distances_df": self.distances_df.get().copy(),
            "step_counter": self.step_counter.get(),
            "global_step_counter": self.global_step_counter.get(),
            "nodes_visited": self.nodes_visited.get().copy(),
            "current_edges": self.current_edges.get().copy(),
            "current_node": self.current_node.get(),
            "step_explanation": self.step_explanation.get()
        }
        self.state_history.get().append(state)
    
    def restore_state(self):
        """Restore previous state for undo functionality."""
        if self.state_history.get():
            state = self.state_history.get().pop()
            self.distances_df.set(state["distances_df"])
            self.step_counter.set(state["step_counter"])
            self.global_step_counter.set(state["global_step_counter"])
            self.nodes_visited.set(state["nodes_visited"])
            self.current_edges.set(state["current_edges"])
            self.current_node.set(state["current_node"])
            self.step_explanation.set(state["step_explanation"])
    
    def reset_algorithm_state(self):
        """Reset algorithm state to initial conditions."""
        G = self.graph.get()
        if G:
            nodes, index_name = self._get_graph_nodes_and_index_name(G)
            distance_matrix = pd.DataFrame(index=nodes, columns=["Cost", "Previous"])
            distance_matrix["Cost"] = float('inf')
            
            distance_matrix.index.name = index_name
            distance_matrix.reset_index(inplace=True)
            self.distances_df.set(distance_matrix)
            self.step_counter.set(0)
            self.global_step_counter.set(0)
            self.nodes_visited.set([])
            self.current_edges.set([])
            self.current_node.set(None)
            self.solution.set(None)
            self.step_explanation.set(TagList(INITIAL_EXPLANATION))
            
            # Reset error states when algorithm is reset
            self.start_node_error.set(False)
            self.target_node_error.set(False)
            
            # Reset prediction game state when algorithm is reset
            self.reset_game_state()
    
    def reset_game_state(self):
        """Reset prediction game state."""
        self.game_score.set(0)
        self.consecutive_correct.set(0)
        self.waiting_for_prediction.set(False)
        self.prediction_candidates.set([])
        self.last_prediction_correct.set(None)
        self.total_predictions.set(0)
        self.correct_predictions.set(0)
    
    def handle_prediction(self, predicted_node, correct_node):
        """Handle a prediction made by the user."""
        is_correct = predicted_node == correct_node
        
        # Update statistics
        self.total_predictions.set(self.total_predictions.get() + 1)
        if is_correct:
            self.correct_predictions.set(self.correct_predictions.get() + 1)
            self.consecutive_correct.set(self.consecutive_correct.get() + 1)
            
            # Calculate score with bonus for consecutive correct answers
            base_points = 10
            bonus_points = min(self.consecutive_correct.get() * 2, 20)  # Max 20 bonus points
            points_earned = base_points + bonus_points
            self.game_score.set(self.game_score.get() + points_earned)
        else:
            self.consecutive_correct.set(0)
        
        self.last_prediction_correct.set(is_correct)
        self.waiting_for_prediction.set(False)
        
        return is_correct
    
    def _load_config(self):
        """Load configuration from config.json."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return default config if file doesn't exist or is invalid
            return {
                "settings": {
                    "game_feature_enabled": True,
                    "force_game_mode": False,
                    "force_game_difficulty": None,
                    "visualization_mode": "cytoscape",
                    "graph_font_size": 16,
                    "password_protected": False,
                    "admin_password": "admin123"
                }
            }
    
    def authenticate_settings(self, password):
        """Authenticate password for settings access."""
        if password == self.admin_password:
            self.settings_unlocked.set(True)
            return True
        return False
    
    def lock_settings(self):
        """Lock settings access."""
        if self.config["settings"]["password_protected"]:
            self.settings_unlocked.set(False)
    
    def update_game_setting(self, enabled):
        """Update game feature setting."""
        self.game_enabled.set(enabled)
        if not enabled:
            self.reset_game_state()
    
    def update_visualization_mode(self, mode):
        """Update visualization mode setting."""
        if mode in ["cytoscape", "matplotlib"]:
            self.visualization_mode.set(mode)
    
    def update_force_game_mode(self, enabled):
        """Update force game mode setting."""
        self.force_game_mode.set(enabled)
    
    def update_game_difficulty(self, difficulty):
        """Update game difficulty setting."""
        if difficulty in ["easy", "medium", "hard"]:
            self.game_difficulty.set(difficulty)
    
    def update_force_game_difficulty(self, difficulty):
        """Update forced game difficulty setting."""
        if difficulty is None or difficulty in ["easy", "medium", "hard"]:
            self.force_game_difficulty.set(difficulty)
    
    def update_graph_font_size(self, size):
        """Update graph font size setting."""
        if isinstance(size, (int, float)) and 8 <= size <= 36:
            self.graph_font_size.set(size)
    
    def get_effective_game_difficulty(self):
        """Get the effective game difficulty (forced or user-selected)."""
        forced_difficulty = self.force_game_difficulty.get()
        if forced_difficulty is not None:
            return forced_difficulty
        return self.game_difficulty.get()
    
    def _get_graph_nodes_and_index_name(self, G):
        """Get nodes and index name based on graph structure."""
        # Check if any node has a label attribute (safely handle any graph structure)
        has_labels = False
        if G.nodes:
            first_node = next(iter(G.nodes))
            has_labels = "label" in G.nodes[first_node]
        
        if has_labels:
            nodes = dict(sorted(nx.get_node_attributes(G, "label").items())).values()
            index_name = "Cities"
        else:
            # Keep the original node types instead of converting to string
            nodes = list(G.nodes)
            index_name = "Node"
        return nodes, index_name


# Global state manager instance
state_manager = StateManager()