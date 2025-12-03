"""
User Action Logger for PathSolver Evaluation

This module provides comprehensive logging of all user actions for research
and evaluation purposes. All events are logged with timestamps, session IDs,
and relevant contextual information.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
import requests
import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """Custom encoder for NumPy data types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super(NumpyEncoder, self).default(obj)


class UserActionLogger:
    """Singleton logger for tracking user actions throughout the application."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserActionLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.log_dir = Path("evaluation_logs")
        self.log_dir.mkdir(exist_ok=True)

        # Create session ID
        self.session_id = str(uuid.uuid4())[:8]
        self.session_start_time = datetime.now()

        # Create log file with session ID and timestamp
        timestamp = self.session_start_time.strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"user_actions_{timestamp}_{self.session_id}.jsonl"

        # Remote logging configuration
        self.remote_logging_url = os.getenv("REMOTE_LOGGING_URL", "http://157.180.50.44:5000/api/log")
        self.remote_logging_enabled = os.getenv("ENABLE_REMOTE_LOGGING", "true").lower() == "true"

        # Thread pool for async HTTP requests (don't block the main app)
        self.http_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="log_http")

        # Initialize log file
        self._log_event("session_start", {
            "session_id": self.session_id,
            "start_time": self.session_start_time.isoformat()
        })

        self._initialized = True

    def _send_http_log(self, event: Dict[str, Any]) -> None:
        """
        Send log event to remote logging server via HTTP.
        This runs in a background thread to avoid blocking the main app.

        Args:
            event: The complete event dictionary to send
        """
        if not self.remote_logging_enabled:
            return

        try:
            response = requests.post(
                self.remote_logging_url,
                data=json.dumps(event, cls=NumpyEncoder),
                headers={'Content-Type': 'application/json'},
                timeout=2  # Short timeout to avoid blocking
            )
            response.raise_for_status()
        except Exception as e:
            # Silently fail - we don't want remote logging issues to crash the app
            # Could optionally log this to a separate error log
            pass

    def _ensure_executor_available(self) -> None:
        """
        Ensure the HTTP executor is available and not shut down.
        Recreates the executor if it has been shut down.
        """
        if not hasattr(self, 'http_executor') or self.http_executor._shutdown:
            self.http_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="log_http")

    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Log a single event to the log file.

        Args:
            event_type: Type of event (e.g., "algorithm_step", "prediction_made")
            data: Dictionary containing event-specific data
        """
        # Get participant ID and task info from state manager if available
        participant_id = None
        task_mode_active = False
        current_task_number = None
        current_task_description = None

        try:
            from modules.state_manager import state_manager
            participant_id = state_manager.get_participant_id()

            # Get current task information if in task mode
            if state_manager.is_task_mode_active():
                task_mode_active = True
                current_task = state_manager.get_current_task()
                if current_task:
                    current_task_number = current_task.get('task_number')
                    current_task_description = current_task.get('description')
        except Exception:
            pass  # If state manager not available, proceed without extra info

        event = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "participant_id": participant_id,
            "task_mode_active": task_mode_active,
            "current_task_number": current_task_number,
            "current_task_description": current_task_description,
            "event_type": event_type,
            "data": data
        }

        # Write to JSONL format (one JSON object per line)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, cls=NumpyEncoder) + "\n")

        # Send to remote logging server in background thread
        if self.remote_logging_enabled:
            self._ensure_executor_available()
            self.http_executor.submit(self._send_http_log, event)

    # ==================== Algorithm Events ====================

    def log_algorithm_start(self, start_node: str, target_node: str, graph_type: str) -> None:
        """Log when user starts the Dijkstra algorithm."""
        self._log_event("algorithm_start", {
            "start_node": start_node,
            "target_node": target_node,
            "graph_type": graph_type
        })

    def log_algorithm_step(self, step_number: int, step_name: str,
                          current_node: Optional[str] = None,
                          nodes_visited: Optional[list] = None) -> None:
        """Log each algorithm step advancement."""
        self._log_event("algorithm_step", {
            "step_number": step_number,
            "step_name": step_name,
            "current_node": current_node,
            "nodes_visited": nodes_visited or []
        })

    def log_algorithm_back_step(self, from_step: int, to_step: int) -> None:
        """Log when user goes back a step."""
        self._log_event("algorithm_back_step", {
            "from_step": from_step,
            "to_step": to_step
        })

    def log_algorithm_reset(self) -> None:
        """Log when algorithm is reset."""
        self._log_event("algorithm_reset", {})

    def log_algorithm_complete(self, target_reached: bool,
                               total_steps: int,
                               final_distance: Optional[float] = None) -> None:
        """Log when algorithm completes."""
        self._log_event("algorithm_complete", {
            "target_reached": target_reached,
            "total_steps": total_steps,
            "final_distance": final_distance
        })

    # ==================== Graph Interaction Events ====================

    def log_graph_selected(self, graph_type: str, graph_params: Optional[Dict] = None) -> None:
        """Log when user selects a graph."""
        self._log_event("graph_selected", {
            "graph_type": graph_type,
            "parameters": graph_params or {}
        })

    def log_graph_uploaded(self, filename: str, num_nodes: int, num_edges: int) -> None:
        """Log when user uploads a custom graph."""
        self._log_event("graph_uploaded", {
            "filename": filename,
            "num_nodes": num_nodes,
            "num_edges": num_edges
        })

    def log_node_added(self, node_id: str, position: Optional[Dict] = None) -> None:
        """Log when user adds a node."""
        self._log_event("node_added", {
            "node_id": node_id,
            "position": position
        })

    def log_node_deleted(self, node_id: str) -> None:
        """Log when user deletes a node."""
        self._log_event("node_deleted", {
            "node_id": node_id
        })

    def log_edge_added(self, source: str, target: str, weight: float) -> None:
        """Log when user adds an edge."""
        self._log_event("edge_added", {
            "source": source,
            "target": target,
            "weight": weight
        })

    def log_edge_deleted(self, source: str, target: str) -> None:
        """Log when user deletes an edge."""
        self._log_event("edge_deleted", {
            "source": source,
            "target": target
        })

    def log_edge_weight_updated(self, source: str, target: str,
                                old_weight: float, new_weight: float) -> None:
        """Log when user updates edge weight."""
        self._log_event("edge_weight_updated", {
            "source": source,
            "target": target,
            "old_weight": old_weight,
            "new_weight": new_weight
        })

    def log_start_node_set(self, node_id: str, method: str = "context_menu") -> None:
        """Log when user sets start node."""
        self._log_event("start_node_set", {
            "node_id": node_id,
            "method": method  # "context_menu", "dropdown", etc.
        })

    def log_target_node_set(self, node_id: str, method: str = "context_menu") -> None:
        """Log when user sets target node."""
        self._log_event("target_node_set", {
            "node_id": node_id,
            "method": method
        })

    # ==================== Game/Prediction Events ====================

    def log_game_toggled(self, enabled: bool) -> None:
        """Log when game mode is toggled on/off."""
        self._log_event("game_toggled", {
            "enabled": enabled
        })

    def log_difficulty_changed(self, old_difficulty: str, new_difficulty: str) -> None:
        """Log when game difficulty is changed."""
        self._log_event("difficulty_changed", {
            "old_difficulty": old_difficulty,
            "new_difficulty": new_difficulty
        })

    def log_prediction_made(self, predicted_node: str, correct_node: str,
                           is_correct: bool, current_score: int,
                           consecutive_correct: int) -> None:
        """Log when user makes a prediction in game mode."""
        self._log_event("prediction_made", {
            "predicted_node": predicted_node,
            "correct_node": correct_node,
            "is_correct": is_correct,
            "score": current_score,
            "consecutive_correct": consecutive_correct
        })

    def log_game_stats(self, total_predictions: int, correct_predictions: int,
                      accuracy: float, max_streak: int) -> None:
        """Log game statistics."""
        self._log_event("game_stats", {
            "total_predictions": total_predictions,
            "correct_predictions": correct_predictions,
            "accuracy": accuracy,
            "max_streak": max_streak
        })

    # ==================== Quiz Events ====================

    def log_solution_quiz_toggled(self, enabled: bool) -> None:
        """Log when solution quiz is toggled."""
        self._log_event("solution_quiz_toggled", {
            "enabled": enabled
        })

    def log_quiz_submission(self, submitted_path: str, correct_path: str,
                           is_correct: bool, attempt_number: int = 1) -> None:
        """Log when user submits quiz answer."""
        self._log_event("quiz_submitted", {
            "submitted_path": submitted_path,
            "correct_path": correct_path,
            "is_correct": is_correct,
            "attempt_number": attempt_number
        })

    # ==================== Task Mode Events ====================

    def log_task_mode_toggled(self, enabled: bool) -> None:
        """Log when task mode is enabled/disabled."""
        self._log_event("task_mode_toggled", {
            "enabled": enabled
        })

    def log_task_started(self, task_index: int, task_description: str,
                        graph_type: str) -> None:
        """Log when user starts a task."""
        self._log_event("task_started", {
            "task_index": task_index,
            "task_description": task_description,
            "graph_type": graph_type
        })

    def log_task_completed(self, task_index: int, success: bool,
                          time_taken_seconds: Optional[float] = None) -> None:
        """Log when user completes a task."""
        self._log_event("task_completed", {
            "task_index": task_index,
            "success": success,
            "time_taken_seconds": time_taken_seconds
        })

    # ==================== Settings Events ====================

    def log_language_changed(self, old_language: str, new_language: str) -> None:
        """Log when user changes language."""
        self._log_event("language_changed", {
            "old_language": old_language,
            "new_language": new_language
        })

    def log_visualization_mode_changed(self, old_mode: str, new_mode: str) -> None:
        """Log when visualization mode is changed."""
        self._log_event("visualization_mode_changed", {
            "old_mode": old_mode,
            "new_mode": new_mode
        })

    def log_font_size_changed(self, old_size: int, new_size: int) -> None:
        """Log when font size is changed."""
        self._log_event("font_size_changed", {
            "old_size": old_size,
            "new_size": new_size
        })

    def log_settings_unlocked(self, password_correct: bool) -> None:
        """Log admin settings unlock attempts."""
        self._log_event("settings_unlocked", {
            "password_correct": password_correct
        })

    # ==================== Tutorial Events ====================

    def log_tutorial_started(self) -> None:
        """Log when user starts tutorial."""
        self._log_event("tutorial_started", {})

    def log_tutorial_step(self, step_number: int, step_description: str) -> None:
        """Log tutorial step progression."""
        self._log_event("tutorial_step", {
            "step_number": step_number,
            "step_description": step_description
        })

    def log_tutorial_completed(self) -> None:
        """Log when user completes tutorial."""
        self._log_event("tutorial_completed", {})

    def log_tutorial_skipped(self, at_step: int) -> None:
        """Log when user skips tutorial."""
        self._log_event("tutorial_skipped", {
            "at_step": at_step
        })

    # ==================== Error/Validation Events ====================

    def log_error(self, error_type: str, error_message: str,
                 context: Optional[Dict] = None) -> None:
        """Log errors and validation failures."""
        self._log_event("error_occurred", {
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        })

    def log_validation_failure(self, validation_type: str, reason: str) -> None:
        """Log validation failures (e.g., invalid path, disconnected graph)."""
        self._log_event("validation_failure", {
            "validation_type": validation_type,
            "reason": reason
        })

    # ==================== Export Events ====================

    def log_graph_exported(self, export_format: str) -> None:
        """Log when user exports graph."""
        self._log_event("graph_exported", {
            "format": export_format
        })

    # ==================== Session Management ====================

    def log_session_end(self) -> None:
        """Log session end and duration."""
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        self._log_event("session_end", {
            "session_id": self.session_id,
            "duration_seconds": session_duration
        })

        # Wait for pending HTTP requests to complete (with timeout)
        if hasattr(self, 'http_executor'):
            self.http_executor.shutdown(wait=True, cancel_futures=False)

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session."""
        session_duration = (datetime.now() - self.session_start_time).total_seconds()

        # Count events by type
        event_counts = {}
        if self.log_file.exists():
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        event_type = event.get("event_type", "unknown")
                        event_counts[event_type] = event_counts.get(event_type, 0) + 1
                    except json.JSONDecodeError:
                        continue

        return {
            "session_id": self.session_id,
            "start_time": self.session_start_time.isoformat(),
            "duration_seconds": session_duration,
            "total_events": sum(event_counts.values()),
            "event_counts": event_counts,
            "log_file": str(self.log_file)
        }


# Global logger instance
_logger = None


def get_logger() -> UserActionLogger:
    """Get or create the global logger instance."""
    global _logger
    if _logger is None:
        _logger = UserActionLogger()
    return _logger
