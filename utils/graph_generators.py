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


def generate_from_address(address: str, distance: int = 1000, network_type: str = "drive"):
    """
    Generate a graph from an address using OSMnx for map visualization.
    
    Args:
        address: Street address or place name
        distance: Distance in meters from the address center
        network_type: Type of network ('drive', 'walk', 'bike')
    
    Returns:
        NetworkX graph with additional metadata for map visualization or error message string
    """
    import time
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Map generation timed out")
    
    try:
        print(f"Starting map generation for: {address}")
        
        # Set a timeout for the OSMnx request (30 seconds)
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        # Get the graph from OSMnx
        start_time = time.time()
        G = ox.graph_from_address(address, dist=distance, network_type=network_type)
        load_time = time.time() - start_time
        print(f"OSMnx graph loaded in {load_time:.2f} seconds")
        
        # Cancel the timeout
        signal.alarm(0)
        
        if not G.nodes():
            return "No road network found for this address. Try a different location."
        
        # Convert to undirected graph for Dijkstra visualization
        if G.is_directed():
            G = ox.convert.to_undirected(G)
        
        # Convert MultiGraph to simple Graph to avoid key issues
        if isinstance(G, nx.MultiGraph):
            # Create a new simple graph
            simple_G = nx.Graph()
            for u, v, data in G.edges(data=True):
                if not simple_G.has_edge(u, v):
                    # Use the first edge's data
                    weight = int(data.get('length', 100))
                    simple_G.add_edge(u, v, weight=weight)
            
            # Copy node attributes including coordinates
            for node, data in G.nodes(data=True):
                simple_G.add_node(node, **data)
            
            G = simple_G
        else:
            # Ensure edge weights are based on length (distance)
            for u, v, data in G.edges(data=True):
                weight = int(data.get('length', 100))
                G[u][v]['weight'] = weight
        
        # Check if graph is connected
        if not nx.is_connected(G):
            # Get the largest connected component
            largest_cc = max(nx.connected_components(G), key=len)
            G = G.subgraph(largest_cc).copy()
            print(f"Using largest connected component with {len(G.nodes())} nodes")
        
        # Store original coordinates before relabeling
        original_coords = {}
        for node in G.nodes():
            if 'y' in G.nodes[node] and 'x' in G.nodes[node]:
                original_coords[node] = (G.nodes[node]['y'], G.nodes[node]['x'])  # lat, lon
        
        # Relabel nodes with simple incrementing integers for readability
        # Create mapping from original node IDs to integers
        original_nodes = list(G.nodes())
        node_mapping = {original_node: i for i, original_node in enumerate(original_nodes)}
        
        # Relabel the graph
        G = nx.relabel_nodes(G, node_mapping)
        
        # Add map center and bounds as graph attributes
        if original_coords:
            lats = [coord[0] for coord in original_coords.values()]
            lons = [coord[1] for coord in original_coords.values()]
            G.graph['map_center'] = (sum(lats) / len(lats), sum(lons) / len(lons))
            G.graph['map_bounds'] = ((min(lats), min(lons)), (max(lats), max(lons)))
        
        print(f"Map generation completed: {len(G.nodes())} intersections, {len(G.edges())} streets")
        return G
        
    except TimeoutError:
        signal.alarm(0)
        return "Map generation timed out. Please try a different address or smaller distance."
    except Exception as e:
        signal.alarm(0)
        error_msg = str(e)
        if "Found no graph nodes" in error_msg:
            return "No road network found for this address. Please try a more specific address or different location."
        elif "NetworkX graph" in error_msg:
            return "Unable to process the road network for this location. Please try a different address."
        else:
            return f"Error generating map: {error_msg}"
