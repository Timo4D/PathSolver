"""OSM-based graph visualization with Plotly and map background."""

import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import pandas as pd


def create_osm_plotly_figure(graph, start_node=None, target_node=None, current_node=None, 
                            current_edges=None, distances_df=None, 
                            center_lat=None, center_lon=None, zoom=None, preserve_view=False):
    """
    Create a Plotly figure with the OSM graph overlaid on a map.
    
    Args:
        graph: NetworkX graph with node coordinates (lat, lon)
        start_node: Start node for algorithm
        target_node: Target node for algorithm
        current_node: Currently selected node
        current_edges: Currently highlighted edges
        distances_df: DataFrame with distance information
    
    Returns:
        plotly.graph_objects.Figure: Interactive map with street network
    """
    if not graph or len(graph.nodes()) == 0:
        # Return empty map if no graph
        fig = go.Figure()
        fig.update_layout(
            title="No graph data available",
            xaxis_title="Longitude",
            yaxis_title="Latitude"
        )
        return fig
    
    # Extract node positions
    node_lats = []
    node_lons = []
    node_ids = []
    node_texts = []
    node_colors = []
    
    for node_id in graph.nodes():
        node_data = graph.nodes[node_id]
        lat = node_data.get('lat', node_data.get('y', 0))
        lon = node_data.get('lon', node_data.get('x', 0))
        
        node_lats.append(lat)
        node_lons.append(lon)
        node_ids.append(node_id)
        
        # Create hover text with distance info if available
        text = f"Node {node_id}"
        if distances_df is not None and not distances_df.empty:
            try:
                distance_info = distances_df[distances_df.index == node_id]
                if not distance_info.empty:
                    cost = distance_info['Cost'].iloc[0]
                    text += f"<br>Distance: {cost}"
            except (KeyError, IndexError):
                pass
        node_texts.append(text)
        
        # Color nodes based on their role
        if node_id == start_node:
            node_colors.append('green')
        elif node_id == target_node:
            node_colors.append('red')
        elif node_id == current_node:
            node_colors.append('orange')
        else:
            node_colors.append('lightblue')
    
    # Extract edge positions
    edge_lats = []
    edge_lons = []
    edge_weights = []
    edge_colors = []
    
    for u, v, data in graph.edges(data=True):
        u_data = graph.nodes[u]
        v_data = graph.nodes[v]
        
        u_lat = u_data.get('lat', u_data.get('y', 0))
        u_lon = u_data.get('lon', u_data.get('x', 0))
        v_lat = v_data.get('lat', v_data.get('y', 0))
        v_lon = v_data.get('lon', v_data.get('x', 0))
        
        edge_lats.extend([u_lat, v_lat, None])
        edge_lons.extend([u_lon, v_lon, None])
        
        weight = data.get('weight', 1)
        edge_weights.append(weight)
        
        # Color current edges differently
        if current_edges and ((u, v) in current_edges or (v, u) in current_edges):
            edge_colors.append('red')
        else:
            edge_colors.append('blue')
    
    # Create figure
    fig = go.Figure()
    
    # Add edges as lines
    fig.add_trace(go.Scattermapbox(
        lat=edge_lats,
        lon=edge_lons,
        mode='lines',
        line=dict(width=2, color='blue'),
        name='Roads',
        hoverinfo='skip'
    ))
    
    # Add highlighted current edges if any
    if current_edges:
        current_edge_lats = []
        current_edge_lons = []
        
        for u, v in current_edges:
            if graph.has_edge(u, v):
                u_data = graph.nodes[u]
                v_data = graph.nodes[v]
                
                u_lat = u_data.get('lat', u_data.get('y', 0))
                u_lon = u_data.get('lon', u_data.get('x', 0))
                v_lat = v_data.get('lat', v_data.get('y', 0))
                v_lon = v_data.get('lon', v_data.get('x', 0))
                
                current_edge_lats.extend([u_lat, v_lat, None])
                current_edge_lons.extend([u_lon, v_lon, None])
        
        if current_edge_lats:
            fig.add_trace(go.Scattermapbox(
                lat=current_edge_lats,
                lon=current_edge_lons,
                mode='lines',
                line=dict(width=4, color='red'),
                name='Current Edges',
                hoverinfo='skip'
            ))
    
    # Add nodes as markers
    fig.add_trace(go.Scattermapbox(
        lat=node_lats,
        lon=node_lons,
        mode='markers+text',
        marker=dict(
            size=12,
            color=node_colors,
            opacity=0.8
        ),
        text=[str(node_id) for node_id in node_ids],
        textposition='middle center',
        textfont=dict(color='white', size=10),
        hovertext=node_texts,
        hoverinfo='text',
        name='Intersections'
    ))
    
    # Calculate center and zoom for the map
    if preserve_view and center_lat is not None and center_lon is not None and zoom is not None:
        # Use the preserved viewport settings
        pass  # center_lat, center_lon, zoom are already set
    else:
        # Calculate defaults based on graph data
        if node_lats and node_lons:
            center_lat = sum(node_lats) / len(node_lats)
            center_lon = sum(node_lons) / len(node_lons)
            
            # Calculate appropriate zoom level based on data spread
            lat_range = max(node_lats) - min(node_lats)
            lon_range = max(node_lons) - min(node_lons)
            zoom = max(0, min(20, 15 - max(lat_range, lon_range) * 100))
        else:
            center_lat, center_lon, zoom = 0, 0, 1
    
    # Update layout with map
    layout_config = {
        'title': f"Street Network: {graph.graph.get('location', 'Unknown Location')}",
        'mapbox': dict(
            style='open-street-map',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom
        ),
        'margin': dict(l=0, r=0, t=30, b=0),
        'height': 600,
        'showlegend': True
    }
    
    # Add uirevision to preserve view when preserve_view is True
    if preserve_view:
        layout_config['uirevision'] = 'map-view'
    
    fig.update_layout(**layout_config)
    
    # Note: Plotly config will be applied when converting to HTML
    
    return fig