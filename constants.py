"""Constants and configuration values for PathSolver application."""

from localization import _

# Step numbers
STEP_INITIALIZE = 0
STEP_VISIT_NODES = 1
STEP_FIND_NEXT_NODE = 2
STEP_FINISH = 3
STEP_SHOW_SOLUTION = 4

# Colors for UI
COLOR_ACTIVE = "red"
COLOR_INACTIVE = "#d9d9d9"
COLOR_START_NODE = "green"
COLOR_TARGET_NODE = "red"

# Default values
DEFAULT_START_NODE = 0
DEFAULT_TARGET_NODE = 1

# Graph generation limits
MIN_NODES = 2
MAX_NODES = 30
DEFAULT_NODES = 8

MIN_NEIGHBORS = 2
MAX_NEIGHBORS = 5
DEFAULT_NEIGHBORS = 3

MIN_REWIRE_PROB = 0
MAX_REWIRE_PROB = 1
DEFAULT_REWIRE_PROB = 0.5

# UI text functions (these return localized text)
def get_step_headings():
    """Get localized step headings."""
    return {
        STEP_INITIALIZE: _("step_0_title"),
        STEP_VISIT_NODES: _("step_1_title"), 
        STEP_FIND_NEXT_NODE: _("step_2_title"),
        STEP_FINISH: _("step_3_title"),
        STEP_SHOW_SOLUTION: _("congratulations_message")
    }

def get_initial_explanation():
    """Get localized initial explanation."""
    return _("explanation_placeholder")

# Error message functions (these return localized text)
def get_error_messages():
    """Get localized error messages."""
    return {
        'invalid_input': _("error_invalid_input"),
        'node_not_in_graph': _("error_node_not_in_graph"),
        'invalid_data': _("error_invalid_data"),
        'empty_solution': _("error_no_solution"),
        'invalid_format': _("error_invalid_format"),
        'incorrect_solution': _("error_incorrect_solution")
    }

# Legacy constants for backward compatibility
STEP_HEADINGS = get_step_headings()
INITIAL_EXPLANATION = get_initial_explanation()
ERROR_INVALID_INPUT = _("error_invalid_input")
ERROR_NODE_NOT_IN_GRAPH = _("error_node_not_in_graph") 
ERROR_INVALID_DATA = _("error_invalid_data")
ERROR_EMPTY_SOLUTION = _("error_no_solution")
ERROR_INVALID_FORMAT = _("error_invalid_format")
ERROR_INCORRECT_SOLUTION = _("error_incorrect_solution")

# File paths (should be made configurable)
DEFAULT_EDGE_LIST_PATH = '/home/timo/shiny/dijkstra/edgelist.txt'