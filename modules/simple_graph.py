import networkx as nx
import matplotlib.pyplot as plt


def create_graph():
    # Define the edges with distances
    edges = [
        (0, 6, 35), (0, 7, 224), (1, 2, 291), (1, 3, 128), (1, 4, 137),
        (2, 4, 292), (3, 5, 99), (3, 7, 112), (4, 6, 270), (5, 7, 151)
    ]

    # Create a graph
    G = nx.Graph()

    # Add edges to the graph
    for u, v, d in edges:
        G.add_edge(u, v, weight=d)

    # Get positions for the nodes in a circular layout
    pos = nx.spring_layout(G, seed=1)

    # Draw the nodes and edges
    plt.figure(figsize=(8, 8))
    nx.draw_networkx_nodes(G, pos, node_size=700)
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(data=True))
    nx.draw_networkx_labels(G, pos, font_size=14, font_family='sans-serif')

    # Add edge labels (distances)
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    # Show the plot
    plt.title("Cities Distance Network")
    plt.axis('off')  # Turn off the axis
    plt.show()
