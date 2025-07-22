"""Constants and configuration values for PathSolver application."""

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
DEFAULT_LAYOUT_SEED = 1

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

# UI text
STEP_HEADINGS = {
    STEP_INITIALIZE: "Step 0: Initialize",
    STEP_VISIT_NODES: "Step 1: Visit Nodes", 
    STEP_FIND_NEXT_NODE: "Step 2: Look For Next Node",
    STEP_FINISH: "Step 3: Finish",
    STEP_SHOW_SOLUTION: "Congratulations! Your solution is correct."
}

INITIAL_EXPLANATION = "Here will be the explanations of every step"

# Error messages
ERROR_INVALID_INPUT = "Your input is invalid"
ERROR_NODE_NOT_IN_GRAPH = "Selected Node not on Graph"
ERROR_INVALID_DATA = "Invalid data"
ERROR_EMPTY_SOLUTION = "Please enter a solution before submitting."
ERROR_INVALID_FORMAT = "Invalid input format. Please enter node numbers separated by commas (e.g., 0, 1, 2)."
ERROR_INCORRECT_SOLUTION = "Sorry, your solution is incorrect. Please try again."

# File paths (should be made configurable)
DEFAULT_EDGE_LIST_PATH = '/home/timo/shiny/dijkstra/edgelist.txt'