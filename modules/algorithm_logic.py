"""Algorithm logic for Dijkstra's algorithm steps."""

import networkx as nx
from htmltools import TagList
from shiny import ui

from constants import (
    STEP_INITIALIZE, STEP_VISIT_NODES, STEP_FIND_NEXT_NODE, STEP_FINISH, STEP_SHOW_SOLUTION,
    ERROR_EMPTY_SOLUTION, ERROR_INVALID_FORMAT, ERROR_INCORRECT_SOLUTION
)
from utils.graph_utils import dijkstra_solution


class DijkstraStepHandler:
    """Handles the step-by-step execution of Dijkstra's algorithm."""
    
    def __init__(self, state_manager):
        self.state = state_manager
    
    def handle_next_step(self, input):
        """Handle the next step in the algorithm."""
        step = self.state.step_counter.get()
        self.state.save_state()
        df = self.state.distances_df.get()
        G = self.state.graph.get()
        
        # Increment global step counter for each action
        self.state.global_step_counter.set(self.state.global_step_counter.get() + 1)
        
        # Clear any previous error states when starting algorithm
        if step == STEP_INITIALIZE:
            self.state.start_node_error.set(False)
            self.state.target_node_error.set(False)
        
        if step == STEP_INITIALIZE:
            self.initialize_step(input, df, G)
        elif step == STEP_VISIT_NODES:
            self.visit_neighbors(df, G)
        elif step == STEP_FIND_NEXT_NODE:
            self.set_new_current_node(df, G, input)
            if not self.state.solution.get():
                solution = dijkstra_solution(G, input.start_node(), input.target_node())
                self.state.solution.set(solution)
        elif step == STEP_SHOW_SOLUTION:
            self.show_solution(self.state.solution.get())
            self.state.step_explanation.set(TagList(""))
    
    def initialize_step(self, input, df, G):
        """Initialize the first step of the algorithm."""
        self.state.step_explanation.set(
            TagList("🚀 Starting Dijkstra's algorithm! First set distance to start node to 0 and every other node to infinity")
        )
        
        # Check if the graph is connected before proceeding
        if not nx.is_connected(G):
            self.state.step_explanation.set(
                TagList(
                    "❌ Cannot run Dijkstra algorithm: The graph is not fully connected!",
                    ui.br(), ui.br(),
                    "A connected graph is required for Dijkstra's algorithm to find paths between all nodes. ",
                    "This graph has isolated components that cannot reach each other.",
                    ui.br(), ui.br(),
                    "Please:",
                    ui.br(),
                    "• Generate a new random graph, or",
                    ui.br(), 
                    "• Add edges to connect all components, or",
                    ui.br(),
                    "• Choose a different graph that is fully connected"
                )
            )
            return
        
        if not df.empty:
            start_node_raw = input.start_node()
            target_node_raw = input.target_node()
            
            # Always clear errors first
            self.state.start_node_error.set(False)
            self.state.target_node_error.set(False)
            
            # Convert to appropriate type to match graph nodes
            start_node = start_node_raw
            target_node = target_node_raw
            
            # Try to match the type of nodes in the graph
            if G.nodes:
                sample_node = next(iter(G.nodes))
                if isinstance(sample_node, int):
                    try:
                        start_node = int(start_node_raw) if start_node_raw is not None else None
                        target_node = int(target_node_raw) if target_node_raw is not None else None
                    except (ValueError, TypeError):
                        pass
                elif isinstance(sample_node, str):
                    start_node = str(start_node_raw) if start_node_raw is not None else None
                    target_node = str(target_node_raw) if target_node_raw is not None else None
            
            # Validate start node
            if start_node is None:
                self.state.start_node_error.set(True)
                self.state.step_explanation.set(TagList("Please select a start node"))
                return
            
            if start_node not in G.nodes:
                self.state.start_node_error.set(True)
                self.state.step_explanation.set(TagList(f"Start node {start_node} does not exist in the graph. Available nodes: {list(G.nodes)}"))
                return
            
            # Validate target node
            if target_node is None:
                self.state.target_node_error.set(True)
                self.state.step_explanation.set(TagList("Please select a target node"))
                return
                
            if target_node not in G.nodes:
                self.state.target_node_error.set(True)
                self.state.step_explanation.set(TagList(f"Target node {target_node} does not exist in the graph. Available nodes: {list(G.nodes)}"))
                return
            
            # Both nodes are valid, proceed with algorithm
            # For labeled graphs, we need to look up by city name instead of node ID
            lookup_value = start_node
            if G.nodes and "label" in G.nodes[next(iter(G.nodes))]:
                # This is a labeled graph - use the city name for lookup
                lookup_value = nx.get_node_attributes(G, "label")[start_node]
            
            # Find the row index for the start_node (using appropriate lookup value)
            start_rows = df[df.iloc[:, 0] == lookup_value]
            if start_rows.empty:
                self.state.start_node_error.set(True)
                self.state.step_explanation.set(TagList(f"Start node {start_node} (lookup: {lookup_value}) not found in distance table"))
                return
            
            start_row_idx = start_rows.index[0]
            df.iloc[start_row_idx, 1] = 0
            if G.nodes and "label" in G.nodes[next(iter(G.nodes))]:
                df.iloc[start_row_idx, 2] = nx.get_node_attributes(G, "label")[start_node]
            else:
                df.iloc[start_row_idx, 2] = start_node
            
            # Success - update state
            self.state.distances_df.set(df)
            self.state.nodes_visited.set(self.state.nodes_visited.get() + [start_node])
            self.state.current_node.set(start_node)
            self.state.step_counter.set(STEP_VISIT_NODES)
            
            # Ensure error states are cleared
            self.state.start_node_error.set(False)
            self.state.target_node_error.set(False)
    
    def visit_neighbors(self, df, G):
        """Visit and update distances to neighbors."""
        # Find the row index for the current node
        current_node = self.state.current_node.get()
        lookup_value = current_node
        if G.nodes and "label" in G.nodes[next(iter(G.nodes))]:
            lookup_value = nx.get_node_attributes(G, "label")[current_node]
        
        current_rows = df[df.iloc[:, 0] == lookup_value]
        if current_rows.empty:
            return  # Cannot proceed if current node not found
        current_row_idx = current_rows.index[0]
        prev_cost = df.iloc[current_row_idx, 1]
        neighbors, edges = [], []
        
        for n in G.neighbors(self.state.current_node.get()):
            if n not in self.state.nodes_visited.get():
                new_weight = G[n][self.state.current_node.get()]['weight'] + prev_cost

                neighbors.append({
                    "node": n, 
                    "weight": (G[n][self.state.current_node.get()]['weight'] + prev_cost)
                })

                # Find the row index for node n
                n_lookup_value = n
                if G.nodes and "label" in G.nodes[next(iter(G.nodes))]:
                    n_lookup_value = nx.get_node_attributes(G, "label")[n]
                
                n_rows = df[df.iloc[:, 0] == n_lookup_value]
                if n_rows.empty:
                    continue  # Skip if node not found in DataFrame
                n_row_idx = n_rows.index[0]
                if new_weight < df.iloc[n_row_idx, 1]:
                    df.iloc[n_row_idx, 1] = new_weight
                    if G.nodes and "label" in G.nodes[next(iter(G.nodes))]:
                        df.iloc[n_row_idx, 2] = nx.get_node_attributes(G, "label")[self.state.current_node.get()]
                    else:
                        df.iloc[n_row_idx, 2] = self.state.current_node.get()

                edges.append(sorted((n, self.state.current_node.get())))

        self.state.distances_df.set(df.copy())
        self.state.current_edges.set(self.state.current_edges.get() + edges)
        
        nodes_visited_without_current = [
            int(node) for node in self.state.nodes_visited.get() 
            if node != self.state.current_node.get()
        ]

        nodes_visited_text = None
        if nodes_visited_without_current:
            nodes_visited_text = TagList(
                f"We will leave nodes {nodes_visited_without_current} out as we have already visited them", 
                ui.br()
            )

        current_node = self.state.current_node.get()
        nodes_visited_count = len(self.state.nodes_visited.get())
        self.state.step_explanation.set(
            TagList(
                f"🔍 Now examining neighbors of node {current_node} (visited {nodes_visited_count} nodes so far)", ui.br(),
                nodes_visited_text,
                "You need to calculate the cost of all unvisited neighbours. To do this add the distance to your current node + the weight of the edge.",
                ui.br(),
                "If the weight is lower than what's already calculated we need to update it, otherwise we won't change it",
                ui.br(),
            )
        )
        self.state.step_counter.set(STEP_FIND_NEXT_NODE)
    
    def set_new_current_node(self, df, G, input):
        """Set the next node to visit."""
        self.state.current_edges.set([])

        # Filter out visited nodes from the DataFrame
        visited_lookup_values = []
        for visited_node in self.state.nodes_visited.get():
            if G.nodes and "label" in G.nodes[next(iter(G.nodes))]:
                # For labeled graphs, convert node ID to city name
                visited_lookup_values.append(nx.get_node_attributes(G, "label")[visited_node])
            else:
                # For unlabeled graphs, use node ID directly
                visited_lookup_values.append(visited_node)
        
        unvisited_nodes = df[~df.iloc[:, 0].isin(visited_lookup_values)]
        min_cost_row_idx = unvisited_nodes["Cost"].idxmin()
        min_cost_lookup_value = df.iloc[min_cost_row_idx, 0]
        
        # Convert back to node ID if this is a labeled graph
        if G.nodes and "label" in G.nodes[next(iter(G.nodes))]:
            # Find the node ID that corresponds to this city name
            label_to_node = {v: k for k, v in nx.get_node_attributes(G, "label").items()}
            min_cost_node = label_to_node[min_cost_lookup_value]
        else:
            min_cost_node = min_cost_lookup_value
        
        # Check if prediction game is enabled (either forced or user enabled) and we should wait for user prediction
        game_active = (self.state.game_enabled.get() and self.state.force_game_mode.get()) or \
                     (self.state.game_enabled.get() and input.game_enabled() if input.game_enabled() is not None else False)
        
        if game_active and not self.state.waiting_for_prediction.get():
            # Get list of candidate nodes (unvisited nodes with finite costs)
            finite_cost_nodes = unvisited_nodes[unvisited_nodes["Cost"] != float('inf')]
            
            if len(finite_cost_nodes) > 1:  # Only ask for prediction if there are choices
                # Store the correct answer and candidates
                candidates = []
                for _, row in finite_cost_nodes.iterrows():
                    node_lookup = row.iloc[0]
                    if G.nodes and "label" in G.nodes[next(iter(G.nodes))]:
                        label_to_node = {v: k for k, v in nx.get_node_attributes(G, "label").items()}
                        node_id = label_to_node[node_lookup]
                    else:
                        node_id = node_lookup
                    candidates.append(node_id)
                
                self.state.prediction_candidates.set(candidates)
                self.state.waiting_for_prediction.set(True)
                
                # Don't proceed with algorithm until prediction is made
                self.state.step_explanation.set(
                    TagList(
                        "🎮 Prediction Game: Which node will Dijkstra visit next?",
                        ui.br(), ui.br(),
                        "Look at the unvisited nodes in the distance table and click on the one with the lowest cost in the graph above!",
                        ui.br(), ui.br(),
                        f"Unvisited nodes with finite distances: {candidates}"
                    )
                )
                return
        
        # Normal algorithm flow - set the current node
        self.state.current_node.set(min_cost_node)

        if self.state.current_node.get() == input.target_node():
            self.state.step_explanation.set(
                TagList(
                    "We have now arrived at our Target node, that means we are done and have found the shortest possible distance to it",
                    ui.br(),
                    "You now have to enter your solution of the fastest path in new Box below. If it is correct you will see the path on the graph.",
                    ui.br(),
                    "The weights of the edges are now hidden, so try to get the solution with help of the table below.",
                    ui.br(),
                    "The Dijkstra Algorithm would trace the way from the Target node via its previous node until it arrives at the start node",
                )
            )
            self.state.step_counter.set(self.state.step_counter.get() + 1)
        else:
            nodes_visited_count = len(self.state.nodes_visited.get())
            total_nodes = len(G.nodes())
            self.state.step_explanation.set(
                TagList(
                    f"✅ Selected node {min_cost_node} (lowest unvisited cost) as our new current node.", ui.br(),
                    f"🔄 Since {self.state.current_node.get()} is not our target node, we'll continue the algorithm by examining its neighbors next.",
                    ui.br(), ui.br(),
                    f"Progress: {nodes_visited_count}/{total_nodes} nodes visited. This is the core of Dijkstra's algorithm: repeatedly select the unvisited node with minimum distance and explore its neighbors.",
                    ui.br()
                )
            )
            self.state.step_counter.set(self.state.step_counter.get() - 1)
        
        self.state.nodes_visited.set(self.state.nodes_visited.get() + [self.state.current_node.get()])
    
    def handle_prediction(self, predicted_node, input):
        """Handle user prediction in game mode."""
        if not self.state.waiting_for_prediction.get():
            return False
        
        # Get the correct answer using the same logic as set_new_current_node
        df = self.state.distances_df.get()
        G = self.state.graph.get()
        
        # Filter out visited nodes from the DataFrame
        visited_lookup_values = []
        for visited_node in self.state.nodes_visited.get():
            if G.nodes and "label" in G.nodes[next(iter(G.nodes))]:
                visited_lookup_values.append(nx.get_node_attributes(G, "label")[visited_node])
            else:
                visited_lookup_values.append(visited_node)
        
        unvisited_nodes = df[~df.iloc[:, 0].isin(visited_lookup_values)]
        min_cost_row_idx = unvisited_nodes["Cost"].idxmin()
        min_cost_lookup_value = df.iloc[min_cost_row_idx, 0]
        
        # Convert to node ID
        if G.nodes and "label" in G.nodes[next(iter(G.nodes))]:
            label_to_node = {v: k for k, v in nx.get_node_attributes(G, "label").items()}
            correct_node = label_to_node[min_cost_lookup_value]
        else:
            correct_node = min_cost_lookup_value
        
        # Handle the prediction
        is_correct = self.state.handle_prediction(predicted_node, correct_node)
        
        # Clear prediction candidates to remove highlighting
        self.state.prediction_candidates.set([])
        
        # Continue with the algorithm
        self.state.current_node.set(correct_node)
        
        if correct_node == input.target_node():
            self.state.step_explanation.set(
                TagList(
                    f"{'✅ Correct prediction!' if is_correct else '❌ Incorrect prediction.'} The algorithm selected node {correct_node}.",
                    ui.br(), ui.br(),
                    "We have now arrived at our Target node, that means we are done and have found the shortest possible distance to it",
                    ui.br(),
                    "You now have to enter your solution of the fastest path in new Box below. If it is correct you will see the path on the graph.",
                    ui.br(),
                    "The weights of the edges are now hidden, so try to get the solution with help of the table below.",
                    ui.br(),
                    "The Dijkstra Algorithm would trace the way from the Target node via its previous node until it arrives at the start node",
                )
            )
            self.state.step_counter.set(self.state.step_counter.get() + 1)
        else:
            nodes_visited_count = len(self.state.nodes_visited.get())  
            total_nodes = len(G.nodes())
            self.state.step_explanation.set(
                TagList(
                    f"{'✅ Correct prediction!' if is_correct else '❌ Incorrect prediction.'} The algorithm selected node {correct_node}.",
                    ui.br(), ui.br(),
                    f"✅ Selected node {correct_node} (lowest unvisited cost) as our new current node.", ui.br(),
                    f"🔄 Since {correct_node} is not our target node, we'll continue the algorithm by examining its neighbors next.",
                    ui.br(), ui.br(),
                    f"Progress: {nodes_visited_count}/{total_nodes} nodes visited. This is the core of Dijkstra's algorithm: repeatedly select the unvisited node with minimum distance and explore its neighbors.",
                    ui.br()
                )
            )
            self.state.step_counter.set(self.state.step_counter.get() - 1)
        
        self.state.nodes_visited.set(self.state.nodes_visited.get() + [correct_node])
        
        return is_correct
    
    def show_solution(self, solution):
        """Show the final solution path."""
        edges = [list(edge) for edge in zip(solution, solution[1:])]
        self.state.current_edges.set(edges)
    
    def check_user_solution(self, input):
        """Check if the user's solution is correct."""
        user_input = input.user_solution().strip()
        
        # Validate input is not empty
        if not user_input:
            self.state.step_explanation.set(TagList(ERROR_EMPTY_SOLUTION))
            return
            
        try:
            # Split by comma and strip whitespace from each element
            user_solution = [int(node.strip()) for node in user_input.split(",")]
        except ValueError:
            self.state.step_explanation.set(TagList(ERROR_INVALID_FORMAT))
            return
        
        # Validate that all nodes exist in the graph
        G = self.state.graph.get()
        invalid_nodes = [node for node in user_solution if node not in G.nodes()]
        if invalid_nodes:
            self.state.step_explanation.set(
                TagList(f"Invalid nodes: {invalid_nodes}. Please only use nodes that exist in the graph.")
            )
            return
            
        # Validate that the path is connected
        for i in range(len(user_solution) - 1):
            if not G.has_edge(user_solution[i], user_solution[i + 1]):
                self.state.step_explanation.set(
                    TagList(f"No edge exists between nodes {user_solution[i]} and {user_solution[i + 1]}. Please check your path.")
                )
                return

        correct_solution = self.state.solution.get()

        if user_solution == correct_solution:
            self.state.step_counter.set(STEP_SHOW_SOLUTION)
            # Draw the solution
            self.handle_next_step(input)
        else:
            self.state.step_explanation.set(TagList(ERROR_INCORRECT_SOLUTION))