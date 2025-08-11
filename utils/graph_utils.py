import matplotlib.pyplot as plt
import networkx as nx
from networkx.classes import Graph
import math



def dijkstra_solution(G: Graph, start: int, target: int, weight="weight"):
    return nx.dijkstra_path(G, start, target, weight=weight)


def plot_graph(G, start, target, seed, distances=None, current_node=None, current_edges=None, dark_mode=False,
               final_step=False):
    width: int = 3
    if current_edges is None or not isinstance(current_edges, (list, tuple)):
        current_edges = []
    if not G:
        return None

    current_edges_set = {(u, v) for u, v in current_edges} | {(v, u) for u, v in current_edges}

    pos = nx.spring_layout(G, seed=seed)

    if dark_mode == "dark":
        plt.style.use('dark_background')
        default_color = 'white'
    else:
        plt.style.use('default')
        default_color = 'black'

    # Draw Node Color
    node_color_map = []
    for node in G:
        if node == start:
            node_color_map.append('tab:green')
        elif node == target:
            node_color_map.append('tab:red')
        elif node == current_node:
            node_color_map.append('tab:pink')
        else:
            node_color_map.append('tab:blue')

    nx.draw_networkx_nodes(G, pos, node_color=node_color_map, node_size=400)
    nx.draw_networkx_labels(G, pos)

    # Draw labels
    if G.nodes and "label" in G.nodes[next(iter(G.nodes))]:
        labels = dict(sorted(nx.get_node_attributes(G, "label").items()))
        label_pos = {node: (coords[0], coords[1] - 0.13) for node, coords in pos.items()}
        nx.draw_networkx_labels(G, label_pos, labels, font_color=default_color)

    # Verbesserte Edge-Verarbeitung
    if current_edges:
        edge_color_map = ['tab:red' if (u, v) in current_edges_set else default_color
                          for u, v in G.edges]
        nx.draw_networkx_edges(G, pos, edge_color=edge_color_map, width=width)
    else:
        nx.draw_networkx_edges(G, pos, edge_color=default_color, width=width)

    # Draw Distances
    if distances is not None and not distances["Cost"].empty:
        distance_labels = distances["Cost"].replace(float('inf'), 'ꝏ').apply(
            lambda x: int(x) if isinstance(x, float) else x)

        label_pos = {node: (coords[0], coords[1] + 0.13) for node, coords in pos.items()}
        # Ensure the node exists in pos before drawing the label
        distance_labels = {node: label for node, label in distance_labels.items() if node in pos}
        nx.draw_networkx_labels(G, label_pos, distance_labels, font_color=default_color)

    if not final_step:
        # Draw weights
        edge_labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.axis('off')


def convert_graph_to_cytoscape(graph, current_node=None, start_node=None, target_node=None, nodes_visited=None, current_edges=None, distances=None, prediction_candidates=None, game_difficulty="medium"):
    """Convert NetworkX graph to Cytoscape format."""
    if not graph or len(graph.nodes) == 0:
        return {"elements": [], "style": [], "layout": {"name": "circle"}}
    
    if nodes_visited is None:
        nodes_visited = set()
    if current_edges is None or not isinstance(current_edges, (list, tuple)):
        current_edges = []
    if prediction_candidates is None:
        prediction_candidates = []
    
    # Create bidirectional edge set like matplotlib does
    current_edges_set = {(u, v) for u, v in current_edges} | {(v, u) for u, v in current_edges}
    
    # Convert NetworkX graph to Cytoscape format
    elements = []
    
    # Add nodes
    for node in graph.nodes(data=True):
        node_id, node_attrs = node
        
        # Build compound label based on difficulty level
        label_parts = []
        
        # Show distances based on difficulty level
        if game_difficulty == "easy":
            # Easy: Show all distances
            if distances is not None and not distances.empty and "Cost" in distances.columns:
                if node_id in distances["Cost"]:
                    dist_value = distances["Cost"][node_id]
                    if dist_value == float('inf'):
                        label_parts.append("ꝏ")
                    else:
                        label_parts.append(str(int(dist_value) if isinstance(dist_value, float) else dist_value))
        elif game_difficulty == "medium":
            # Medium: Show distances only for visited nodes and current node
            if (distances is not None and not distances.empty and "Cost" in distances.columns and
                (node_id in nodes_visited or node_id == current_node)):
                if node_id in distances["Cost"]:
                    dist_value = distances["Cost"][node_id]
                    if dist_value == float('inf'):
                        label_parts.append("ꝏ")
                    else:
                        label_parts.append(str(int(dist_value) if isinstance(dist_value, float) else dist_value))
        # Hard: No distances shown at all (no else case needed)
        
        # Add main node ID (center)
        label_parts.append(str(node_id))
        
        # Add custom label below (like matplotlib y - 0.13) 
        if "label" in node_attrs:
            label_parts.append(str(node_attrs["label"]))
        
        # Join with newlines to create multi-line label
        compound_label = "\n".join(label_parts)
        
        node_data = {
            "data": {
                "id": str(node_id),
                "label": compound_label
            }
        }
        
        # Add position if stored in node attributes
        if "x" in node_attrs and "y" in node_attrs:
            node_data["position"] = {
                "x": node_attrs["x"],
                "y": node_attrs["y"]
            }
        
        # Style nodes based on current state (order matters for priority)
        classes = []
        
        # Mark example graph nodes (those with labels) for special styling
        if "label" in node_attrs:
            classes.append("example-graph")
        
        if node_id == current_node:
            classes.append("current")
        elif node_id == start_node:
            classes.append("start")
        elif node_id == target_node:
            classes.append("target")
        elif node_id in nodes_visited:
            classes.append("visited")
        
        # Add prediction candidate class if applicable
        if node_id in prediction_candidates:
            classes.append("prediction-candidate")
        
        if classes:
            node_data["classes"] = " ".join(classes)
        
        elements.append(node_data)
    
    # Add edges
    for edge in graph.edges(data=True):
        source, target, data = edge
        weight = data.get("weight", 1)
        
        # Control edge weight visibility based on difficulty
        edge_data = {
            "data": {
                "id": f"{source}-{target}",
                "source": str(source),
                "target": str(target),
                "weight": weight
            }
        }
        
        # Show weight labels based on difficulty
        if game_difficulty == "hard":
            # Hard: Hide edge weights completely
            edge_data["data"]["label"] = ""
        else:
            # Easy and Medium: Show edge weights
            edge_data["data"]["label"] = str(weight)
        
        # Highlight current edges using the bidirectional set
        if (source, target) in current_edges_set:
            edge_data["classes"] = "current"
        
        elements.append(edge_data)
    
    return elements


def get_cytoscape_styles(font_size=16):
    """Get Cytoscape styles for different node and edge states to match matplotlib colors."""
    return [
        {
            "selector": "node",
            "style": {
                "background-color": "#1f77b4",  # tab:blue
                "color": "#fff",
                "label": "data(label)",
                "width": 80,  # Back to original size
                "height": 80,  # Back to original size
                "text-valign": "center",
                "text-halign": "center",
                "font-size": f"{font_size}px",
                "font-weight": "bold",  # Make text bold for better readability
                "text-wrap": "wrap",  # Allow text wrapping
                "text-max-width": "140px"  # Original text width limit
            }
        },
        {
            "selector": "node.example-graph",
            "style": {
                "shape": "round-rectangle",  # Rounded rectangle for example graphs
                "width": 100,  # Slightly wider for city names
                "height": 80,
            }
        },
        {
            "selector": "node.edge-source",
            "style": {
                "background-color": "#FF9800",
                "border-width": 3,
                "border-color": "#FF5722"
            }
        },
        {
            "selector": "node.prediction-candidate",
            "style": {
                "border-width": 4,
                "border-color": "#007bff",
                "border-style": "dashed",
                "background-color": "#e7f3ff"
            }
        },
        {
            "selector": "node.start",
            "style": {
                "background-color": "#2ca02c",  # tab:green
            }
        },
        {
            "selector": "node.target", 
            "style": {
                "background-color": "#d62728",  # tab:red
            }
        },
        {
            "selector": "node.current",
            "style": {
                "background-color": "#ff1493",  # tab:pink
                "border-width": 3,
                "border-color": "#ff69b4"
            }
        },
        {
            "selector": "node.visited",
            "style": {
                "background-color": "#9C27B0",
            }
        },
        {
            "selector": "edge",
            "style": {
                "width": 2,
                "line-color": "#000000",  # Default black color like matplotlib
                "target-arrow-color": "#000000",
                "target-arrow-shape": "triangle",
                "label": "data(weight)",
                "font-size": f"{font_size}px",
                "font-weight": "bold",
                "color": "#000000",
                "text-background-color": "#ffffff",
                "text-background-opacity": 0.8,
                "text-background-padding": "3px",
                "text-border-width": 1,
                "text-border-color": "#cccccc",
                "text-border-opacity": 0.8
            }
        },
        {
            "selector": "edge.current",
            "style": {
                "width": 4,
                "line-color": "#d62728",  # tab:red to match matplotlib current edges
                "target-arrow-color": "#d62728"
            }
        }
    ]


def get_cytoscape_layout():
    """Get default Cytoscape layout."""
    return {
        "name": "cose"
    }
