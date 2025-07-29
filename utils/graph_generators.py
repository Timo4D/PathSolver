import random

import networkx as nx
from .map_utils import fetch_road_network, simplify_road_network, add_map_mode_to_graph


def generate_random_graph(n, k, p):
    G = nx.connected_watts_strogatz_graph(n, k, p)

    # Add random integer weights to edges
    for (u, v) in G.edges():
        G[u][v]['weight'] = random.randint(1, 100)

    return G


def generate_koot_example():
    edges = [
        (0, 6, 35), (0, 7, 224), (1, 2, 291), (1, 3, 128), (1, 4, 137),
        (2, 4, 292), (3, 5, 99), (3, 7, 112), (4, 6, 270), (5, 7, 151)
    ]

    node_labels = {
        0: "Berlin", 1: "Bremen", 2: "Düsseldorf", 3: "Hamburg",
        4: "Hannover", 5: "Kiel", 6: "Potsdam", 7: "Schwerin"
    }

    G = nx.Graph()
    for u, v, d in edges:
        G.add_edge(u, v, weight=d)

    nx.set_node_attributes(G, node_labels, "label")
    return G


def generate_from_real_edge_list(edgelist: str):
    edgelist_correct = "\n".join(
        [f"{u} {v} {{'weight':{w}}}" for u, v, w in (line.split() for line in edgelist.split('\n'))])

    edgelist_lines = edgelist_correct.split('\n')
    G = nx.parse_edgelist(edgelist_lines, nodetype=int)
    # print(edgelist_lines)



    if nx.is_connected(G):
        return G
    else:
        return "Graph is not connected"


def generate_from_edge_list(edgelist: str):
    try:
        edgelist_lines = [f"{u} {v} {{'weight':{w}}}" for u, v, w in (line.split() for line in edgelist.split('\n'))]
        G = nx.parse_edgelist(edgelist_lines, nodetype=int)
    except (ValueError, SyntaxError, TypeError):
        return "Edgelist invalid"

    for line in nx.generate_edgelist(G):
        print(line)

    if nx.is_connected(G):
        return G
    else:
        return "Graph is not connected"


def generate_from_map_location(location: str, distance: int = 1000, max_nodes: int = 30):
    """
    Generate a graph from a real map location using OpenStreetMap data.
    
    Args:
        location: Location name or address (e.g., "Times Square, New York, USA")
        distance: Distance in meters from the location center
        max_nodes: Maximum number of nodes in the simplified graph
    
    Returns:
        NetworkX Graph representing the road network, or error string
    """
    try:
        # Fetch the road network
        osm_graph = fetch_road_network(location, distance=distance)
        
        # Simplify for visualization and algorithm performance
        simplified_graph = simplify_road_network(osm_graph, max_nodes=max_nodes)
        
        # Add map metadata and labels
        map_graph = add_map_mode_to_graph(simplified_graph, location)
        
        if not nx.is_connected(map_graph):
            return "Road network is not connected - try a different location or larger distance"
        
        return map_graph
        
    except Exception as e:
        return f"Failed to generate map graph: {str(e)}"
