"""Map utilities for fetching and processing road network data from OpenStreetMap."""

import osmnx as ox
import networkx as nx
import pandas as pd
import folium
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


def create_folium_map_with_graph(graph, current_node=None, start_node=None, target_node=None, 
                                nodes_visited=None, current_edges=None, distances=None):
    """
    Create a Folium map with the graph overlaid on the actual map.
    
    Args:
        graph: NetworkX graph with geographic coordinates
        current_node: Currently active node in algorithm
        start_node: Algorithm start node
        target_node: Algorithm target node
        nodes_visited: Set of visited nodes
        current_edges: List of currently active edges
        distances: DataFrame with distance information
    
    Returns:
        Folium map HTML as string
    """
    if not graph or len(graph.nodes) == 0:
        return "<p>No graph data available</p>"
    
    # Get graph bounds for map centering
    min_lat, max_lat, min_lon, max_lon = get_graph_bounds(graph)
    
    if min_lat == max_lat == min_lon == max_lon == 0:
        return "<p>No geographic coordinates available</p>"
    
    # Calculate center and zoom
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=15,
        tiles='OpenStreetMap'
    )
    
    # Fit bounds to show all nodes
    if min_lat != max_lat and min_lon != max_lon:
        m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
    
    # Set defaults
    if nodes_visited is None:
        nodes_visited = set()
    if current_edges is None:
        current_edges = []
    
    # Create bidirectional edge set for highlighting
    current_edges_set = {(u, v) for u, v in current_edges} | {(v, u) for u, v in current_edges}
    
    # Add edges first (so they appear under nodes)
    for edge in graph.edges(data=True):
        source, target, data = edge
        source_data = graph.nodes[source]
        target_data = graph.nodes[target]
        
        if 'lat' in source_data and 'lon' in source_data and 'lat' in target_data and 'lon' in target_data:
            # Determine edge visualization based on algorithm state
            edge_weight = data.get('weight', 1)
            
            if (source, target) in current_edges_set:
                # Current edges: Bright red, thick, prominent
                color = '#FF0000'
                weight = 6
                opacity = 1.0
                dash_array = None
                popup_text = f"🔍 EXPLORING: {source}→{target}<br>Distance: {edge_weight}m<br>Status: Currently being examined by algorithm"
            else:
                # Regular edges: Blue, thinner, more subtle
                color = '#2E86AB'
                weight = 3
                opacity = 0.7
                dash_array = '5, 5'  # Dashed line for non-active edges
                popup_text = f"Edge: {source}→{target}<br>Distance: {edge_weight}m<br>Status: Available path"
            
            # Create the edge polyline
            folium.PolyLine(
                locations=[
                    [source_data['lat'], source_data['lon']],
                    [target_data['lat'], target_data['lon']]
                ],
                color=color,
                weight=weight,
                opacity=opacity,
                dash_array=dash_array,
                popup=folium.Popup(popup_text, max_width=250)
            ).add_to(m)
            
            # Add weight label at the middle of the edge for current edges
            if (source, target) in current_edges_set:
                mid_lat = (source_data['lat'] + target_data['lat']) / 2
                mid_lon = (source_data['lon'] + target_data['lon']) / 2
                
                folium.Marker(
                    location=[mid_lat, mid_lon],
                    icon=folium.DivIcon(
                        html=f'<div style="background-color: white; border: 2px solid #FF0000; border-radius: 4px; padding: 2px 4px; font-weight: bold; font-size: 12px; color: #FF0000;">{edge_weight}m</div>',
                        icon_size=(50, 20),
                        icon_anchor=(25, 10)
                    )
                ).add_to(m)
    
    # Add nodes
    for node_id, node_data in graph.nodes(data=True):
        if 'lat' not in node_data or 'lon' not in node_data:
            continue
            
        lat, lon = node_data['lat'], node_data['lon']
        
        # Determine node color and style based on algorithm state
        if node_id == current_node:
            # Current node: Large, bright blue with pulsing effect
            color = 'blue'
            icon_color = 'white'
            icon = 'cog'
            prefix = 'fa'
            radius = 12
        elif node_id == start_node:
            # Start node: Green with start icon
            color = 'green'
            icon_color = 'white'
            icon = 'play'
            prefix = 'fa'
            radius = 10
        elif node_id == target_node:
            # Target node: Red with target icon
            color = 'red'
            icon_color = 'white'
            icon = 'flag-checkered'
            prefix = 'fa'
            radius = 10
        elif node_id in nodes_visited:
            # Visited nodes: Orange with checkmark
            color = 'orange'
            icon_color = 'white'
            icon = 'check'
            prefix = 'fa'
            radius = 8
        else:
            # Unvisited nodes: Gray and smaller
            color = 'gray'
            icon_color = 'white'
            icon = 'circle'
            prefix = 'fa'
            radius = 6
        
        # Create popup text with node information
        popup_text = f"<b>Node {node_id}</b><br>"
        
        # Add distance information if available
        if distances is not None and not distances.empty and "Cost" in distances.columns:
            if node_id in distances.index or node_id in distances.get("Node", []):
                try:
                    if "Node" in distances.columns:
                        mask = distances["Node"] == node_id
                        if mask.any():
                            dist_value = distances.loc[mask, "Cost"].iloc[0]
                        else:
                            dist_value = float('inf')
                    else:
                        dist_value = distances.loc[node_id, "Cost"]
                    
                    if dist_value == float('inf'):
                        popup_text += "Cost: ∞<br>"
                    else:
                        popup_text += f"Cost: {int(dist_value) if isinstance(dist_value, float) else dist_value}<br>"
                except (KeyError, IndexError):
                    pass
        
        # Add coordinates
        popup_text += f"Lat: {lat:.4f}<br>Lon: {lon:.4f}"
        
        # Add custom label if available
        if "label" in node_data:
            popup_text += f"<br>{node_data['label']}"
        
        # Use CircleMarker for variable sizing and better algorithm visualization
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            popup=folium.Popup(popup_text, max_width=200),
            color='white',  # Border color
            weight=2,
            fillColor=color,
            fillOpacity=0.8,
            opacity=1.0
        ).add_to(m)
        
        # Add an icon marker on top for better identification
        folium.Marker(
            location=[lat, lon],
            icon=folium.Icon(
                color=color,
                icon=icon,
                prefix=prefix,
                icon_color=icon_color
            ),
            popup=folium.Popup(popup_text, max_width=200)
        ).add_to(m)
    
    # Add enhanced map information panel
    if hasattr(graph, 'graph') and 'location_name' in graph.graph:
        location_name = graph.graph['location_name']
        
        # Determine algorithm status
        algorithm_status = ""
        if current_node is not None:
            algorithm_status = f"🔍 Exploring from Node {current_node}"
        elif nodes_visited:
            algorithm_status = f"✅ Visited {len(nodes_visited)} nodes"
        else:
            algorithm_status = "🚀 Ready to start algorithm"
            
        # Create current edges status
        edges_status = ""
        if current_edges:
            edges_status = f"📈 Examining {len(current_edges)} edges"
        
        # Create a more constrained info panel that stays within the map bounds
        info_html = f'''
        <div style="position: absolute; 
                    top: 10px; right: 10px; width: 280px; max-height: 120px;
                    background-color: rgba(255, 255, 255, 0.95); 
                    border: 2px solid #2196F3; border-radius: 8px; z-index:1000; 
                    font-size: 12px; padding: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.15);
                    pointer-events: none; overflow: hidden;">
            <div style="margin-bottom: 4px; font-weight: bold; color: #2196F3; font-size: 13px;">
                📍 {location_name}
            </div>
            <div style="margin-bottom: 2px; color: #333; font-size: 11px;">
                {algorithm_status}
            </div>
            {f'<div style="margin-bottom: 2px; color: #666; font-size: 10px;">{edges_status}</div>' if edges_status else ''}
            <div style="font-size: 10px; color: #888; margin-top: 6px;">
                🟢 Start  🔴 Target  🔵 Current  🟠 Visited  ⚪ Unvisited
            </div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(info_html))
    
    # Return HTML string
    return m._repr_html_()


def convert_graph_to_folium_data(graph, current_node=None, start_node=None, target_node=None,
                                nodes_visited=None, current_edges=None, distances=None):
    """
    Convert graph data to format suitable for Folium rendering.
    
    Returns:
        Dictionary with processed graph data for Folium
    """
    return {
        'graph': graph,
        'current_node': current_node,
        'start_node': start_node,
        'target_node': target_node,
        'nodes_visited': nodes_visited or set(),
        'current_edges': current_edges or [],
        'distances': distances
    }