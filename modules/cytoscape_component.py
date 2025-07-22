"""Cytoscape.js component for Shiny for Python."""

from typing import Dict, List, Optional, Union, Any
from htmltools import HTMLDependency, Tag, TagList, tags
from shiny import ui
import json


def jquery_dependency() -> HTMLDependency:
    """Create HTML dependency for jQuery."""
    return HTMLDependency(
        name="jquery",
        version="3.6.0",
        source={"href": "https://code.jquery.com/"},
        script={"src": "jquery-3.6.0.min.js"}
    )

def cytoscape_dependency() -> HTMLDependency:
    """Create HTML dependency for Cytoscape.js library."""
    return HTMLDependency(
        name="cytoscape",
        version="3.26.0",
        source={"href": "https://unpkg.com/cytoscape@3.26.0/dist/"},
        script={"src": "cytoscape.min.js"}
    )


def cytoscape_component_dependency() -> HTMLDependency:
    """Create HTML dependency for custom Cytoscape component."""
    return HTMLDependency(
        name="cytoscape-component",
        version="1.0.0",
        source={"subdir": "www"},
        script={"src": "cytoscape_component.js"}
    )


def cytoscape_graph(
    graph_id: str,
    elements: Optional[List[Dict]] = None,
    height: str = "400px",
    width: str = "100%",
    style: Optional[List[Dict]] = None,
    layout: Optional[Dict] = None
) -> Tag:
    """
    Create a Cytoscape.js graph component.
    
    Args:
        graph_id: Unique identifier for the graph
        elements: List of nodes and edges in Cytoscape format
        height: Height of the graph container
        width: Width of the graph container  
        style: Custom Cytoscape styles
        layout: Layout options for the graph
        
    Returns:
        HTML tag for the graph component
    """
    return TagList(
        jquery_dependency(),
        cytoscape_dependency(),
        cytoscape_component_dependency(),
        tags.div(
            id=graph_id,
            class_="cytoscape-graph",
            style=f"width: {width}; height: {height}; border: 1px solid #ccc;"
        )
    )


def networkx_to_cytoscape(G, node_positions: Optional[Dict] = None) -> List[Dict]:
    """
    Convert a NetworkX graph to Cytoscape.js format.
    
    Args:
        G: NetworkX graph
        node_positions: Optional dictionary of node positions
        
    Returns:
        List of elements in Cytoscape format
    """
    elements = []
    
    # Add nodes
    for node in G.nodes():
        element = {
            'data': {
                'id': str(node),
                'label': str(node)
            }
        }
        
        # Add position if provided
        if node_positions and node in node_positions:
            pos = node_positions[node]
            element['position'] = {
                'x': float(pos[0]) * 100,  # Scale for better visibility
                'y': float(pos[1]) * 100
            }
            
        elements.append(element)
    
    # Add edges
    for edge in G.edges(data=True):
        source, target, data = edge
        element = {
            'data': {
                'id': f"{source}-{target}",
                'source': str(source),
                'target': str(target)
            }
        }
        
        # Add weight if present
        if 'weight' in data:
            element['data']['weight'] = data['weight']
            element['data']['label'] = str(data['weight'])
            
        elements.append(element)
    
    return elements


class CytoscapeRenderer:
    """Renderer class for Cytoscape graphs in Shiny."""
    
    def __init__(self, graph_id: str):
        self.graph_id = graph_id
        self.elements = []
        self.start_node = None
        self.target_node = None
        self.visited_nodes = []
        self.current_node = None
        self.current_edges = []
        self.shortest_path = []
        
    def update_graph(self, G, node_positions: Optional[Dict] = None):
        """Update the graph elements."""
        self.elements = networkx_to_cytoscape(G, node_positions)
        
    def set_start_node(self, node_id: str):
        """Set the start node."""
        self.start_node = str(node_id) if node_id is not None else None
        
    def set_target_node(self, node_id: str):
        """Set the target node."""
        self.target_node = str(node_id) if node_id is not None else None
        
    def set_visited_nodes(self, nodes: List):
        """Set the visited nodes."""
        self.visited_nodes = [str(node) for node in nodes] if nodes else []
        
    def set_current_node(self, node_id):
        """Set the current node."""
        self.current_node = str(node_id) if node_id is not None else None
        
    def set_current_edges(self, edges: List):
        """Set the current edges."""
        if edges:
            self.current_edges = [f"{edge[0]}-{edge[1]}" for edge in edges]
        else:
            self.current_edges = []
            
    def set_shortest_path(self, path: List):
        """Set the shortest path."""
        self.shortest_path = [str(node) for node in path] if path else []
        
    def render_data(self) -> Dict:
        """Generate render data for the Cytoscape component."""
        return {
            'elements': self.elements,
            'startNode': self.start_node,
            'targetNode': self.target_node,
            'visitedNodes': self.visited_nodes,
            'currentNode': self.current_node,
            'currentEdges': self.current_edges,
            'shortestPath': self.shortest_path,
            'fit': True
        }


def render_cytoscape_graph(
    output_id: str,
    renderer: CytoscapeRenderer
):
    """
    Render function for Cytoscape graphs.
    
    Args:
        output_id: Output ID for the graph
        renderer: CytoscapeRenderer instance
        
    Returns:
        Render data for Shiny
    """
    return renderer.render_data()


# Example usage functions
def create_dijkstra_cytoscape_ui(graph_id: str = "dijkstra_graph") -> Tag:
    """Create UI for Dijkstra visualization with Cytoscape."""
    return TagList(
        tags.div(
            cytoscape_graph(
                graph_id=graph_id,
                height="500px",
                width="100%"
            ),
            class_="graph-container"
        ),
        tags.style("""
            .graph-container {
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .cytoscape-graph {
                background-color: #fafafa;
            }
        """)
    )