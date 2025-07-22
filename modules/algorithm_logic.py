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
            TagList("First set distance to start node to 0 and every other node to infinity")
        )
        
        if not df.empty:
            start_node = input.start_node()
            target_node = input.target_node()
            
            if start_node in G.nodes:
                self.state.start_node_error.set(False)
            else:
                self.state.start_node_error.set(True)
                return

            if target_node in G.nodes:
                df.iloc[start_node, 1] = 0
                if "label" in G.nodes[0]:
                    df.iloc[start_node, 2] = nx.get_node_attributes(G, "label")[start_node]
                else:
                    df.iloc[start_node, 2] = start_node
                self.state.distances_df.set(df)
                self.state.nodes_visited.set(self.state.nodes_visited.get() + [start_node])
                self.state.current_node.set(start_node)
                self.state.step_counter.set(STEP_VISIT_NODES)
                self.state.target_node_error.set(False)
            else:
                self.state.target_node_error.set(True)
    
    def visit_neighbors(self, df, G):
        """Visit and update distances to neighbors."""
        prev_cost = df.iloc[self.state.current_node.get(), 1]
        neighbors, edges = [], []
        
        for n in G.neighbors(self.state.current_node.get()):
            if n not in self.state.nodes_visited.get():
                new_weight = G[n][self.state.current_node.get()]['weight'] + prev_cost

                neighbors.append({
                    "node": n, 
                    "weight": (G[n][self.state.current_node.get()]['weight'] + prev_cost)
                })

                if new_weight < df.iloc[n, 1]:
                    df.iloc[n, 1] = new_weight
                    if "label" in G.nodes[0]:
                        df.iloc[n, 2] = nx.get_node_attributes(G, "label")[self.state.current_node.get()]
                    else:
                        df.iloc[n, 2] = self.state.current_node.get()

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

        self.state.step_explanation.set(
            TagList(
                "Now look at the possible unvisited neighbours", ui.br(),
                nodes_visited_text,
                "You need to calculate the cost of all unvisited neighbours. To do this add the distance to your current node + the weight of the edge.",
                ui.br(),
                "If the weight is lower that whats already calculated we need to update it, otherwise we won't change it",
                ui.br(),
            )
        )
        self.state.step_counter.set(STEP_FIND_NEXT_NODE)
    
    def set_new_current_node(self, df, G, input):
        """Set the next node to visit."""
        self.state.current_edges.set([])

        unvisited_nodes = df[~df.index.isin(self.state.nodes_visited.get())]
        min_cost_node = unvisited_nodes["Cost"].idxmin()
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
            self.state.step_explanation.set(
                TagList(
                    f"You can see that {min_cost_node} is the node with the lowest cost that we have not visited yet, so {self.state.current_node.get()} is our new Node. ",
                    ui.br(),
                    f"Also notice that {self.state.current_node.get()} is not our Target Node, so we need to continue and do the previous step again",
                    ui.br()
                )
            )
            self.state.step_counter.set(self.state.step_counter.get() - 1)
        
        self.state.nodes_visited.set(self.state.nodes_visited.get() + [self.state.current_node.get()])
    
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