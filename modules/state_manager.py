"""State management for PathSolver application."""

import json
import os
import hashlib
import secrets
import pandas as pd
import networkx as nx
from shiny import reactive
from htmltools import TagList

from constants import get_initial_explanation
from localization import I18n, set_language, get_current_language


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
        
        # UI state - use function call to get localized text
        self.step_explanation = reactive.Value(TagList(get_initial_explanation()))
        
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
        self.prediction_feedback_message = reactive.Value(None)  # Persistent feedback message
        
        # Settings state
        self.visualization_mode = reactive.Value(self.config["settings"]["visualization_mode"])
        self.force_game_mode = reactive.Value(self.config["settings"]["force_game_mode"])
        self.force_game_difficulty = reactive.Value(self.config["settings"]["force_game_difficulty"])
        self.graph_font_size = reactive.Value(self.config["settings"].get("graph_font_size", 16))  # Default 16px
        self.solution_quiz_enabled = reactive.Value(self.config["settings"].get("solution_quiz_enabled", True))
        self.force_solution_quiz = reactive.Value(self.config["settings"].get("force_solution_quiz", False))
        self.settings_unlocked = reactive.Value(not self.config["settings"]["password_protected"])
        self.admin_password_hash = self.config["settings"].get("admin_password_hash")
        self.admin_password_salt = self.config["settings"].get("admin_password_salt")
        
        # For backwards compatibility, if old plaintext password exists, convert it
        if "admin_password" in self.config["settings"] and not self.admin_password_hash:
            old_password = self.config["settings"]["admin_password"]
            self._set_password_hash(old_password)
            self._save_config()
        
        # Language state
        default_language = self.config["settings"].get("language", "en")
        self.current_language = reactive.Value(default_language)
        # Initialize i18n with the configured language immediately (non-reactively)
        set_language(default_language)
        self._language_initialized = True

        # Task mode state
        self.task_mode_enabled = reactive.Value(self.config["settings"].get("task_mode_enabled", False))
        self.current_task_index = reactive.Value(0)  # Index in tasks array
        self.completed_tasks = reactive.Value([])  # List of completed task numbers
        self.tasks = self.config.get("tasks", [])  # Pre-defined tasks list

        # Participant ID for evaluation studies
        self.participant_id = reactive.Value(None)
        self.participant_id_set = reactive.Value(False)
    
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
            self.step_explanation.set(TagList(get_initial_explanation()))
            
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
        self.prediction_feedback_message.set(None)
    
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
                    "admin_password_hash": None,
                    "admin_password_salt": None,
                    "language": "en",
                    "solution_quiz_enabled": True,
                    "force_solution_quiz": False
                }
            }
    
    def authenticate_settings(self, password):
        """Authenticate password for settings access."""
        if self._verify_password(password):
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
    
    def update_solution_quiz_setting(self, enabled):
        """Update solution quiz feature setting."""
        self.solution_quiz_enabled.set(enabled)
        if not enabled:
            # If disabling solution quiz, also disable force mode
            self.force_solution_quiz.set(False)
    
    def update_force_solution_quiz(self, enabled):
        """Update force solution quiz setting."""
        self.force_solution_quiz.set(enabled)
    
    def _ensure_language_initialized(self):
        """Ensure language is initialized in reactive context."""
        if not self._language_initialized:
            try:
                current_lang = self.current_language.get() if hasattr(self, 'current_language') else "en"
                set_language(current_lang)
                self._language_initialized = True
            except RuntimeError:
                # No reactive context available yet, set to default
                set_language("en")
                self._language_initialized = True

    def update_language(self, language_code):
        """Update the application language."""
        from localization import get_available_languages
        available_languages = get_available_languages()
        
        if language_code in available_languages:
            self.current_language.set(language_code)
            set_language(language_code)
            self._language_initialized = True
            
            # Update all static content that needs to be refreshed
            self._refresh_static_content()
            
            return True
        return False
    
    def _refresh_static_content(self):
        """Refresh static content that doesn't automatically update on language change."""
        try:
            # Update constants
            from constants import get_step_headings, get_initial_explanation
            import constants
            constants.STEP_HEADINGS = get_step_headings()
            constants.INITIAL_EXPLANATION = get_initial_explanation()
            
            # Update static UI content
            from modules.dijkstra_explanation import update_dijkstra_explanation
            from modules.project_information import update_project_information
            from modules.dijkstra_info import update_dijkstra_info
            
            update_dijkstra_explanation()
            update_project_information()
            update_dijkstra_info()
            
            # Update step explanation if it's currently showing the default text
            current_explanation = str(self.step_explanation.get())
            if "Here will be" in current_explanation or "Hier werden" in current_explanation:
                self.step_explanation.set(TagList(get_initial_explanation()))
            
        except Exception as e:
            print(f"Warning: Could not refresh static content: {e}")

    def set_participant_id(self, participant_id):
        """Set the participant ID for this session."""
        self.participant_id.set(participant_id)
        self.participant_id_set.set(True)

    def get_participant_id(self):
        """Get the current participant ID."""
        return self.participant_id.get()

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
    
    def _hash_password(self, password, salt=None):
        """Hash a password with salt using SHA-256."""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Combine password and salt
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        # Create hash
        hash_obj = hashlib.sha256(password_bytes + salt_bytes)
        password_hash = hash_obj.hexdigest()
        
        return password_hash, salt
    
    def _verify_password(self, password):
        """Verify a password against the stored hash."""
        if not self.admin_password_hash or not self.admin_password_salt:
            return False
        
        # Hash the input password with the stored salt
        password_hash, _ = self._hash_password(password, self.admin_password_salt)
        
        # Compare with stored hash
        return password_hash == self.admin_password_hash
    
    def _set_password_hash(self, password):
        """Set the password hash and salt."""
        password_hash, salt = self._hash_password(password)
        self.admin_password_hash = password_hash
        self.admin_password_salt = salt
        
        # Update config
        self.config["settings"]["admin_password_hash"] = password_hash
        self.config["settings"]["admin_password_salt"] = salt
        
        # Remove old plaintext password if it exists
        if "admin_password" in self.config["settings"]:
            del self.config["settings"]["admin_password"]
    
    def set_admin_password(self, new_password):
        """Set a new admin password."""
        try:
            self._set_password_hash(new_password)
            self._save_config()
            return True
        except Exception as e:
            print(f"Error setting password: {e}")
            return False
    
    def update_password_protection(self, enabled):
        """Update password protection setting."""
        self.config["settings"]["password_protected"] = enabled
        if not enabled:
            self.settings_unlocked.set(True)
        else:
            self.settings_unlocked.set(False)
        self._save_config()

    # Task mode methods
    def get_current_task(self):
        """Get the current task definition."""
        if not self.task_mode_enabled.get() or not self.tasks:
            return None

        idx = self.current_task_index.get()
        if idx < len(self.tasks):
            return self.tasks[idx]
        return None

    def get_start_node(self, input_obj):
        """Get start node - from task if in task mode, otherwise from input."""
        if self.is_task_mode_active():
            task = self.get_current_task()
            return task['start_node'] if task else 0
        else:
            try:
                value = input_obj.start_node() if hasattr(input_obj, 'start_node') else None
                return value if value is not None else 0
            except:
                return 0

    def get_target_node(self, input_obj):
        """Get target node - from task if in task mode, otherwise from input."""
        if self.is_task_mode_active():
            task = self.get_current_task()
            return task['target_node'] if task else 1
        else:
            try:
                value = input_obj.target_node() if hasattr(input_obj, 'target_node') else None
                return value if value is not None else 1
            except:
                return 1

    def advance_to_next_task(self):
        """Advance to the next task."""
        current_task = self.get_current_task()
        if current_task:
            # Mark current task as completed
            task_num = current_task["task_number"]
            completed = self.completed_tasks.get()
            if task_num not in completed:
                completed.append(task_num)
                self.completed_tasks.set(completed)

        # Move to next task
        next_idx = self.current_task_index.get() + 1
        if next_idx < len(self.tasks):
            self.current_task_index.set(next_idx)
            return True
        else:
            # All tasks completed - disable task mode
            self.task_mode_enabled.set(False)
            return False

    def is_task_mode_active(self):
        """Check if task mode is currently active."""
        return self.task_mode_enabled.get() and self.current_task_index.get() < len(self.tasks)

    def get_total_tasks(self):
        """Get total number of tasks."""
        return len(self.tasks)

    def reset_task_mode(self):
        """Reset task mode to start from first task."""
        self.current_task_index.set(0)
        self.completed_tasks.set([])
        self.task_mode_enabled.set(self.config["settings"].get("task_mode_enabled", False))

    def _save_config(self):
        """Save configuration to config.json."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False


# Global state manager instance
state_manager = StateManager()