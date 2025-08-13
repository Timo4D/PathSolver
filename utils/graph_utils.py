import matplotlib.pyplot as plt
import networkx as nx
from networkx.classes import Graph
import math
try:
    import contextily as ctx
    import geopandas as gpd
    from shapely.geometry import Point
    CONTEXTILY_AVAILABLE = True
except ImportError:
    CONTEXTILY_AVAILABLE = False

try:
    from ipyleaflet import Map, Marker, Polyline, Icon, DivIcon
    from ipywidgets import HTML
    IPYLEAFLET_AVAILABLE = True
except ImportError:
    IPYLEAFLET_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False



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


def plot_map_graph(G, start, target, distances=None, current_node=None, current_edges=None, dark_mode=False, final_step=False):
    """Plot graph with geographic coordinates and map background."""
    width: int = 3
    if current_edges is None or not isinstance(current_edges, (list, tuple)):
        current_edges = []
    if not G:
        return None

    current_edges_set = {(u, v) for u, v in current_edges} | {(v, u) for u, v in current_edges}

    # Check if nodes have geographic coordinates
    has_geo_coords = all('x' in G.nodes[node] and 'y' in G.nodes[node] for node in G.nodes())
    
    if not has_geo_coords or not CONTEXTILY_AVAILABLE:
        # Fallback to regular spring layout if no geo coordinates or contextily unavailable
        return plot_graph(G, start, target, seed=42, distances=distances, 
                         current_node=current_node, current_edges=current_edges, 
                         dark_mode=dark_mode, final_step=final_step)
    
    # Use geographic coordinates
    pos = {node: (G.nodes[node]['x'], G.nodes[node]['y']) for node in G.nodes()}
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 8))
    
    if dark_mode == "dark":
        plt.style.use('dark_background')
        default_color = 'white'
        map_style = ctx.providers.CartoDB.DarkMatter
    else:
        plt.style.use('default')
        default_color = 'black'
        map_style = ctx.providers.OpenStreetMap.Mapnik

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

    # Draw edges first (so they appear behind nodes)
    if current_edges:
        edge_color_map = ['tab:red' if (u, v) in current_edges_set else default_color
                          for u, v in G.edges]
        nx.draw_networkx_edges(G, pos, edge_color=edge_color_map, width=width, ax=ax)
    else:
        nx.draw_networkx_edges(G, pos, edge_color=default_color, width=width, ax=ax)

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color=node_color_map, node_size=400, ax=ax)
    nx.draw_networkx_labels(G, pos, ax=ax)

    # Draw custom labels if available
    if G.nodes and "label" in G.nodes[next(iter(G.nodes))]:
        labels = dict(sorted(nx.get_node_attributes(G, "label").items()))
        # Offset labels below nodes (adjust y coordinate)
        label_pos = {node: (coords[0], coords[1] - 0.0001) for node, coords in pos.items()}
        nx.draw_networkx_labels(G, label_pos, labels, font_color=default_color, ax=ax)

    # Draw Distances
    if distances is not None and not distances["Cost"].empty:
        distance_labels = distances["Cost"].replace(float('inf'), 'ꝏ').apply(
            lambda x: int(x) if isinstance(x, float) else x)

        # Offset labels above nodes (adjust y coordinate)
        label_pos = {node: (coords[0], coords[1] + 0.0001) for node, coords in pos.items()}
        distance_labels = {node: label for node, label in distance_labels.items() if node in pos}
        nx.draw_networkx_labels(G, label_pos, distance_labels, font_color=default_color, ax=ax)

    if not final_step:
        # Draw weights
        edge_labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax)

    # Add map background
    try:
        # Get bounds of the graph
        x_coords = [pos[node][0] for node in pos]
        y_coords = [pos[node][1] for node in pos]
        
        # Add some padding
        x_margin = (max(x_coords) - min(x_coords)) * 0.1
        y_margin = (max(y_coords) - min(y_coords)) * 0.1
        
        ax.set_xlim(min(x_coords) - x_margin, max(x_coords) + x_margin)
        ax.set_ylim(min(y_coords) - y_margin, max(y_coords) + y_margin)
        
        # Add basemap
        ctx.add_basemap(ax, crs='EPSG:4326', source=map_style, alpha=0.7)
        
    except Exception as e:
        print(f"Warning: Could not add basemap: {e}")
    
    ax.set_aspect('equal')
    plt.axis('off')


def create_ipyleaflet_map(G, start=None, target=None, distances=None, current_node=None, current_edges=None):
    """Create an interactive ipyleaflet map for graph visualization."""
    if not IPYLEAFLET_AVAILABLE or not G:
        return None
    
    # Check if nodes have geographic coordinates
    has_geo_coords = all('x' in G.nodes[node] and 'y' in G.nodes[node] for node in G.nodes())
    if not has_geo_coords:
        return None
    
    # Get map center and bounds from graph attributes
    center = G.graph.get('map_center', (40.7589, -73.9851))  # Default to NYC
    bounds = G.graph.get('map_bounds', None)
    
    # Create the map
    m = Map(center=center, zoom=15, layout={'width': '100%', 'height': '600px'})
    
    if current_edges is None:
        current_edges = []
    
    current_edges_set = {(u, v) for u, v in current_edges} | {(v, u) for u, v in current_edges}
    
    # Add edges as polylines with distance labels
    for u, v, edge_data in G.edges(data=True):
        if 'x' in G.nodes[u] and 'y' in G.nodes[u] and 'x' in G.nodes[v] and 'y' in G.nodes[v]:
            start_coord = [G.nodes[u]['y'], G.nodes[u]['x']]  # lat, lon
            end_coord = [G.nodes[v]['y'], G.nodes[v]['x']]    # lat, lon
            
            # Style based on whether edge is currently active
            if (u, v) in current_edges_set:
                color = 'red'
                weight = 6
                opacity = 0.8
                label_bg_color = '#dc3545'
            else:
                color = 'blue'
                weight = 3
                opacity = 0.6
                label_bg_color = '#007bff'
            
            polyline = Polyline(
                locations=[start_coord, end_coord],
                color=color,
                weight=weight,
                opacity=opacity
            )
            m.add_layer(polyline)
            
            # Add distance label at the midpoint of the edge
            edge_weight = edge_data.get('weight', 1)  # Get weight from edge data
            mid_lat = (start_coord[0] + end_coord[0]) / 2
            mid_lon = (start_coord[1] + end_coord[1]) / 2
            
            # Create edge label
            edge_label_icon = DivIcon(
                html=f'<div style="background: {label_bg_color}; color: white; padding: 1px 4px; border-radius: 2px; font-size: 10px; font-weight: bold; border: 1px solid white; box-shadow: 1px 1px 1px rgba(0,0,0,0.2);">{edge_weight}</div>',
                icon_size=[20, 14],
                icon_anchor=[10, 7]
            )
            
            edge_label_marker = Marker(
                location=[mid_lat, mid_lon],
                icon=edge_label_icon,
                draggable=False
            )
            m.add_layer(edge_label_marker)
    
    # Add nodes as markers with labels
    for node in G.nodes():
        if 'x' in G.nodes[node] and 'y' in G.nodes[node]:
            lat, lon = G.nodes[node]['y'], G.nodes[node]['x']
            
            # Create label with distances if available
            label_parts = [f"<strong>{node}</strong>"]
            if distances is not None and not distances.empty and "Cost" in distances.columns:
                if node in distances["Cost"]:
                    dist_value = distances["Cost"][node]
                    if dist_value == float('inf'):
                        label_parts.append("<br>d: ∞")
                    else:
                        label_parts.append(f"<br>d: {int(dist_value)}")
            
            title = " | ".join([str(node), f"d:{distances['Cost'][node] if distances is not None and not distances.empty and node in distances['Cost'] else 'N/A'}"])
            
            # Determine marker color and background based on node type
            if node == start:
                icon_url = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png'
                bg_color = '#28a745'
                text_color = 'white'
            elif node == target:
                icon_url = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png'
                bg_color = '#dc3545'
                text_color = 'white'
            elif node == current_node:
                icon_url = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png'
                bg_color = '#6f42c1'
                text_color = 'white'
            else:
                icon_url = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png'
                bg_color = '#007bff'
                text_color = 'white'
            
            # Create Icon object
            icon = Icon(
                icon_url=icon_url,
                shadow_url='https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                icon_size=[25, 41],
                icon_anchor=[12, 41],
                shadow_size=[41, 41]
            )
            
            marker = Marker(
                location=[lat, lon],
                title=title,
                alt=f"Node {node}",
                draggable=False,
                icon=icon
            )
            m.add_layer(marker)
            
            # Add a text label next to the marker
            label_html = "".join(label_parts)
            label_icon = DivIcon(
                html=f'<div style="background: {bg_color}; color: {text_color}; padding: 2px 6px; border-radius: 3px; font-size: 12px; font-weight: bold; border: 1px solid white; box-shadow: 1px 1px 2px rgba(0,0,0,0.3);">{label_html}</div>',
                icon_size=[40, 20],
                icon_anchor=[20, 30]  # Position slightly below and right of marker
            )
            
            # Offset label position slightly from marker
            label_lat = lat - 0.0002  # Slightly south of marker
            label_lon = lon + 0.0002  # Slightly east of marker
            
            label_marker = Marker(
                location=[label_lat, label_lon],
                icon=label_icon,
                draggable=False
            )
            m.add_layer(label_marker)
    
    # Fit bounds if available
    if bounds:
        (min_lat, min_lon), (max_lat, max_lon) = bounds
        m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
    
    return m


def create_plotly_map(G, start=None, target=None, distances=None, current_node=None, current_edges=None):
    """Create a clean interactive Plotly map for graph visualization."""
    if not PLOTLY_AVAILABLE or not G:
        return None
    
    # Check if nodes have geographic coordinates
    has_geo_coords = all('x' in G.nodes[node] and 'y' in G.nodes[node] for node in G.nodes())
    if not has_geo_coords:
        return None
    
    if current_edges is None:
        current_edges = []
    
    current_edges_set = {(u, v) for u, v in current_edges} | {(v, u) for u, v in current_edges}
    
    # Create figure
    fig = go.Figure()
    
    # Add edges as lines
    edge_lats = []
    edge_lons = []
    edge_colors = []
    edge_widths = []
    
    for u, v, edge_data in G.edges(data=True):
        if 'x' in G.nodes[u] and 'y' in G.nodes[u] and 'x' in G.nodes[v] and 'y' in G.nodes[v]:
            # Add line coordinates
            edge_lats.extend([G.nodes[u]['y'], G.nodes[v]['y'], None])
            edge_lons.extend([G.nodes[u]['x'], G.nodes[v]['x'], None])
            
            # Style based on whether edge is currently active
            if (u, v) in current_edges_set:
                color = 'red'
                width = 4
            else:
                color = 'blue'
                width = 2
            
            edge_colors.extend([color, color, color])
            edge_widths.extend([width, width, width])
    
    # Add edges to figure using Scattermapbox for map tiles
    fig.add_trace(go.Scattermapbox(
        lat=edge_lats,
        lon=edge_lons,
        mode='lines',
        line=dict(width=2, color='blue'),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Add current edges (highlighted)
    if current_edges:
        current_edge_lats = []
        current_edge_lons = []
        
        for u, v in current_edges:
            if (u in G.nodes() and v in G.nodes() and 
                'x' in G.nodes[u] and 'y' in G.nodes[u] and 
                'x' in G.nodes[v] and 'y' in G.nodes[v]):
                current_edge_lats.extend([G.nodes[u]['y'], G.nodes[v]['y'], None])
                current_edge_lons.extend([G.nodes[u]['x'], G.nodes[v]['x'], None])
        
        if current_edge_lats:
            fig.add_trace(go.Scattermapbox(
                lat=current_edge_lats,
                lon=current_edge_lons,
                mode='lines',
                line=dict(width=4, color='red'),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Prepare node data
    node_lats = []
    node_lons = []
    node_texts = []
    node_colors = []
    node_sizes = []
    hover_texts = []
    
    for node in G.nodes():
        if 'x' in G.nodes[node] and 'y' in G.nodes[node]:
            lat, lon = G.nodes[node]['y'], G.nodes[node]['x']
            node_lats.append(lat)
            node_lons.append(lon)
            
            # Create clean text label
            node_texts.append(str(node))
            
            # Create detailed hover text
            hover_parts = [f"Node: {node}"]
            
            # Add distance if available
            if distances is not None and not distances.empty and "Cost" in distances.columns:
                if node in distances["Cost"]:
                    dist_value = distances["Cost"][node]
                    if dist_value == float('inf'):
                        hover_parts.append("Distance: ∞")
                    else:
                        hover_parts.append(f"Distance: {int(dist_value)}")
            
            # Add adjacent edges info
            adjacent_edges = list(G.edges(node, data=True))
            if adjacent_edges:
                edge_info = []
                for _, neighbor, data in adjacent_edges[:3]:  # Show max 3 edges
                    weight = data.get('weight', 1)
                    edge_info.append(f"→{neighbor}: {weight}")
                if len(adjacent_edges) > 3:
                    edge_info.append(f"...+{len(adjacent_edges)-3} more")
                hover_parts.append("Edges: " + ", ".join(edge_info))
            
            hover_texts.append("<br>".join(hover_parts))
            
            # Determine color and size based on node type
            if node == start:
                node_colors.append('green')
                node_sizes.append(20)
            elif node == target:
                node_colors.append('red')
                node_sizes.append(20)
            elif node == current_node:
                node_colors.append('purple')
                node_sizes.append(18)
            else:
                node_colors.append('blue')
                node_sizes.append(12)
    
    # Add nodes to figure using Scattermapbox
    fig.add_trace(go.Scattermapbox(
        lat=node_lats,
        lon=node_lons,
        mode='markers+text',
        marker=dict(
            size=node_sizes,
            color=node_colors,
            sizemode='diameter'
        ),
        text=node_texts,
        textposition='middle center',
        textfont=dict(color='white', size=10, family="Arial Black"),
        hovertext=hover_texts,
        hoverinfo='text',
        showlegend=False
    ))
    
    # Get map bounds from graph attributes
    bounds = G.graph.get('map_bounds', None)
    center = G.graph.get('map_center', None)
    
    # Configure the layout with mapbox for street-level map tiles
    fig.update_layout(
        title=dict(
            text="Interactive Graph on Street Map",
            x=0.5,
            font=dict(size=16)
        ),
        mapbox=dict(
            style="open-street-map",  # Free OpenStreetMap tiles
            center=dict(lat=center[0] if center else 40.7589, lon=center[1] if center else -73.9851),
            zoom=15  # Good zoom level for street-level detail
        ),
        height=600,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    # Adjust zoom based on bounds if available
    if center and bounds:
        (min_lat, min_lon), (max_lat, max_lon) = bounds
        # Calculate appropriate zoom level based on bounds
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        max_range = max(lat_range, lon_range)
        
        # Zoom calculation: smaller range = higher zoom
        if max_range < 0.001:
            zoom = 18
        elif max_range < 0.003:
            zoom = 16
        elif max_range < 0.01:
            zoom = 14
        else:
            zoom = 12
        
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=center[0], lon=center[1]),
                zoom=zoom
            )
        )
    
    return fig


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
                "width": 4,
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
                "width": 6,
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
