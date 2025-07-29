"""Map utilities for fetching and processing road network data from OpenStreetMap."""

import osmnx as ox
import networkx as nx
import pandas as pd
from typing import Tuple, Optional, Dict, Any


def fetch_road_network(location: str, distance: int = 1000, network_type: str = "drive") -> nx.MultiDiGraph:
    """
    Fetch road network from OpenStreetMap for a given location.
    
    Args:
        location: Location name or address (e.g., "Manhattan, New York, USA")
        distance: Distance in meters from the location center
        network_type: Type of network ('drive', 'walk', 'bike', 'all', 'all_private')
    
    Returns:
        NetworkX MultiDiGraph representing the road network
    """
    try:
        # Configure OSMnx settings for better performance (newer API)
        ox.settings.use_cache = True
        ox.settings.log_console = False
        
        # Fetch the road network from OSM
        G = ox.graph_from_address(location, dist=distance, network_type=network_type)
        
        return G
    except Exception as e:
        raise ValueError(f"Failed to fetch road network for '{location}': {str(e)}")


def fetch_road_network_from_bbox(north: float, south: float, east: float, west: float, 
                                network_type: str = "drive") -> nx.MultiDiGraph:
    """
    Fetch road network from OpenStreetMap for a bounding box.
    
    Args:
        north, south, east, west: Bounding box coordinates
        network_type: Type of network ('drive', 'walk', 'bike', 'all', 'all_private')
    
    Returns:
        NetworkX MultiDiGraph representing the road network
    """
    try:
        ox.settings.use_cache = True
        ox.settings.log_console = False
        G = ox.graph_from_bbox(north, south, east, west, network_type=network_type)
        return G
    except Exception as e:
        raise ValueError(f"Failed to fetch road network for bounding box: {str(e)}")


def simplify_road_network(G: nx.MultiDiGraph, max_nodes: int = 50) -> nx.Graph:
    """
    Simplify and convert road network to undirected graph suitable for Dijkstra.
    
    Args:
        G: Original road network from OSM
        max_nodes: Maximum number of nodes in simplified graph
    
    Returns:
        Simplified undirected NetworkX Graph with weights
    """
    # Convert to undirected graph and try to simplify (handle already simplified graphs)
    G_undirected = G.to_undirected()
    try:
        G_simple = ox.simplify_graph(G_undirected)
    except Exception:
        # Graph is already simplified, use as-is
        G_simple = G_undirected
    
    # If graph is too large, extract a subgraph
    if len(G_simple.nodes) > max_nodes:
        # Get the largest connected component
        largest_cc = max(nx.connected_components(G_simple), key=len)
        G_simple = G_simple.subgraph(largest_cc).copy()
        
        # If still too large, sample nodes
        if len(G_simple.nodes) > max_nodes:
            center_node = get_most_central_node(G_simple)
            nodes_to_keep = get_k_hop_subgraph_nodes(G_simple, center_node, max_nodes)
            G_simple = G_simple.subgraph(nodes_to_keep).copy()
    
    # Ensure all edges have weights (use length if available, otherwise default)
    for u, v, data in G_simple.edges(data=True):
        if 'weight' not in data:
            if 'length' in data:
                data['weight'] = int(data['length'])
            else:
                data['weight'] = 1
    
    # Add node positions for visualization
    for node, data in G_simple.nodes(data=True):
        if 'y' in data and 'x' in data:
            data['lat'] = data['y']
            data['lon'] = data['x']
    
    return G_simple


def get_most_central_node(G: nx.Graph) -> Any:
    """Get the most centrally located node in the graph."""
    centrality = nx.betweenness_centrality(G)
    return max(centrality, key=centrality.get)


def get_k_hop_subgraph_nodes(G: nx.Graph, center_node: Any, max_nodes: int) -> set:
    """Get nodes within k-hops of center node up to max_nodes."""
    nodes = {center_node}
    current_frontier = {center_node}
    
    while len(nodes) < max_nodes and current_frontier:
        next_frontier = set()
        for node in current_frontier:
            neighbors = set(G.neighbors(node)) - nodes
            next_frontier.update(neighbors)
        
        # Add as many nodes as possible without exceeding max_nodes
        remaining_capacity = max_nodes - len(nodes)
        nodes_to_add = list(next_frontier)[:remaining_capacity]
        nodes.update(nodes_to_add)
        current_frontier = set(nodes_to_add)
    
    return nodes


def create_road_network_labels(G: nx.Graph) -> Dict[Any, str]:
    """
    Create human-readable labels for road network nodes.
    
    Args:
        G: Road network graph with coordinate data
    
    Returns:
        Dictionary mapping node IDs to labels
    """
    labels = {}
    for i, node in enumerate(G.nodes()):
        node_data = G.nodes[node]
        if 'lat' in node_data and 'lon' in node_data:
            lat = round(node_data['lat'], 4)
            lon = round(node_data['lon'], 4)
            labels[node] = f"N{i+1}\n({lat},{lon})"
        else:
            labels[node] = f"Node {i+1}"
    
    return labels


def get_graph_bounds(G: nx.Graph) -> Tuple[float, float, float, float]:
    """
    Get the geographic bounds of a road network graph.
    
    Returns:
        Tuple of (min_lat, max_lat, min_lon, max_lon)
    """
    lats = []
    lons = []
    
    for node, data in G.nodes(data=True):
        if 'lat' in data and 'lon' in data:
            lats.append(data['lat'])
            lons.append(data['lon'])
        elif 'y' in data and 'x' in data:
            lats.append(data['y'])
            lons.append(data['x'])
    
    if not lats or not lons:
        return 0, 0, 0, 0
    
    return min(lats), max(lats), min(lons), max(lons)


def add_map_mode_to_graph(G: nx.Graph, location_name: str = "Road Network") -> nx.Graph:
    """
    Add metadata to graph to indicate it's a map-based graph.
    
    Args:
        G: Road network graph
        location_name: Name of the location
    
    Returns:
        Graph with map metadata
    """
    G.graph['is_map_graph'] = True
    G.graph['location_name'] = location_name
    G.graph['bounds'] = get_graph_bounds(G)
    
    # Add node labels for better UX
    labels = create_road_network_labels(G)
    nx.set_node_attributes(G, labels, "label")
    
    return G