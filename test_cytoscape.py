"""Simple test for Cytoscape.js component."""

import networkx as nx
from modules.cytoscape_component import networkx_to_cytoscape, CytoscapeRenderer

def test_networkx_conversion():
    """Test NetworkX to Cytoscape conversion."""
    # Create a simple graph
    G = nx.Graph()
    G.add_edge(1, 2, weight=5)
    G.add_edge(2, 3, weight=3)
    G.add_edge(1, 3, weight=7)
    
    # Convert to Cytoscape format
    elements = networkx_to_cytoscape(G)
    
    print("Cytoscape Elements:")
    for element in elements:
        print(f"  {element}")
    
    # Test renderer
    renderer = CytoscapeRenderer("test_graph")
    renderer.update_graph(G)
    renderer.set_start_node("1")
    renderer.set_target_node("3")
    renderer.set_visited_nodes(["1", "2"])
    renderer.set_current_node("2")
    
    render_data = renderer.render_data()
    print("\nRender Data:")
    print(f"  Start Node: {render_data['startNode']}")
    print(f"  Target Node: {render_data['targetNode']}")
    print(f"  Visited Nodes: {render_data['visitedNodes']}")
    print(f"  Current Node: {render_data['currentNode']}")
    print(f"  Elements: {len(render_data['elements'])} items")

if __name__ == "__main__":
    test_networkx_conversion()