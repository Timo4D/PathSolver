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
        distance_labels = distances["Cost"].replace(float('inf'), '∞').apply(
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


def convert_graph_to_cytoscape(graph, current_node=None, start_node=None, target_node=None, nodes_visited=None, current_edges=None):
    """Convert NetworkX graph to Cytoscape format."""
    if not graph or len(graph.nodes) == 0:
        return {"elements": [], "style": [], "layout": {"name": "circle"}}
    
    if nodes_visited is None:
        nodes_visited = set()
    if current_edges is None:
        current_edges = []
    
    # Convert NetworkX graph to Cytoscape format
    elements = []
    
    # Add nodes
    for node in graph.nodes(data=True):
        node_id, node_attrs = node
        node_data = {
            "data": {
                "id": str(node_id),
                "label": str(node_id)
            }
        }
        
        # Add position if stored in node attributes
        if "x" in node_attrs and "y" in node_attrs:
            node_data["position"] = {
                "x": node_attrs["x"],
                "y": node_attrs["y"]
            }
        
        # Style nodes based on current state
        if node_id == current_node:
            node_data["classes"] = "current"
        elif node_id == start_node:
            node_data["classes"] = "start"
        elif node_id == target_node:
            node_data["classes"] = "target"
        elif node_id in nodes_visited:
            node_data["classes"] = "visited"
        
        elements.append(node_data)
    
    # Add edges
    for edge in graph.edges(data=True):
        source, target, data = edge
        edge_data = {
            "data": {
                "id": f"{source}-{target}",
                "source": str(source),
                "target": str(target),
                "weight": data.get("weight", 1)
            }
        }
        
        # Highlight current edges
        if (source, target) in current_edges or (target, source) in current_edges:
            edge_data["classes"] = "current"
        
        elements.append(edge_data)
    
    return elements


def get_cytoscape_styles():
    """Get Cytoscape styles for different node and edge states."""
    return [
        {
            "selector": "node",
            "style": {
                "background-color": "#4CAF50",
                "color": "#fff",
                "label": "data(label)",
                "width": 40,
                "height": 40,
                "text-valign": "center",
                "text-halign": "center",
                "font-size": "12px"
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
            "selector": "node.start",
            "style": {
                "background-color": "#2196F3",
            }
        },
        {
            "selector": "node.target", 
            "style": {
                "background-color": "#FF5722",
            }
        },
        {
            "selector": "node.current",
            "style": {
                "background-color": "#FFC107",
                "border-width": 3,
                "border-color": "#FF9800"
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
                "line-color": "#666",
                "target-arrow-color": "#666",
                "target-arrow-shape": "triangle",
                "label": "data(weight)",
                "font-size": "10px"
            }
        },
        {
            "selector": "edge.current",
            "style": {
                "width": 4,
                "line-color": "#FFC107",
                "target-arrow-color": "#FFC107"
            }
        }
    ]


def get_cytoscape_layout():
    """Get default Cytoscape layout."""
    return {
        "name": "cose"
    }
