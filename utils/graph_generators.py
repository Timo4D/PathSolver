import random

import networkx as nx
import osmnx as ox


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


def generate_from_osm_location(location: str, distance: int):
    """
    Generate a graph from OpenStreetMap data for a given location and distance radius.
    
    Args:
        location (str): Location name or address
        distance (int): Distance radius in meters (100-500)
    
    Returns:
        networkx.Graph: Connected graph with edge weights as road lengths, or error string
    """
    try:
        # Validate distance parameter
        if not (100 <= distance <= 500):
            return "Distance must be between 100 and 500 meters"
        
        # Download street network from OSM
        G = ox.graph_from_address(location, dist=distance, network_type='drive')
        
        # Convert to undirected graph for Dijkstra algorithm compatibility
        G_undirected = G.to_undirected()
        
        # Ensure we have a connected component
        if not nx.is_connected(G_undirected):
            # Get the largest connected component
            largest_cc = max(nx.connected_components(G_undirected), key=len)
            G_undirected = G_undirected.subgraph(largest_cc).copy()
        
        # Create simplified graph with integer node IDs and length-based weights
        G_simple = nx.Graph()
        
        # Map original node IDs to simple integer IDs
        node_mapping = {node: i for i, node in enumerate(G_undirected.nodes())}
        
        # Add nodes with coordinates
        for original_id, simple_id in node_mapping.items():
            node_data = G_undirected.nodes[original_id]
            G_simple.add_node(simple_id, 
                             x=node_data.get('x', 0), 
                             y=node_data.get('y', 0),
                             lat=node_data.get('y', 0),
                             lon=node_data.get('x', 0))
        
        # Add edges with length as weight
        for u, v, data in G_undirected.edges(data=True):
            weight = data.get('length', 100)  # Use length as weight, default 100
            # Round weight to integer for better visualization
            weight = max(1, int(round(weight)))  
            G_simple.add_edge(node_mapping[u], node_mapping[v], weight=weight)
        
        # Store the original location and distance for potential map visualization
        G_simple.graph['location'] = location
        G_simple.graph['distance'] = distance
        
        return G_simple
        
    except Exception as e:
        return f"Error fetching location data: {str(e)}"
