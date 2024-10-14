import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.font_manager import font_scalings


def plot_graph(G, start, target, seed, current_node=None, current_edges=None, dark_mode=None):
    width: int = 3

    if current_edges is None:
        current_edges = []
    if not G:
        return None

    pos = nx.spring_layout(G, seed=seed)

    if dark_mode == "dark":
        plt.style.use('dark_background')
    else:
        plt.style.use('default')

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

    if current_edges:
        edge_color_map = []
        for edge in G.edges:
            if sorted(edge) in current_edges:
                edge_color_map.append('tab:red')
            else:
                edge_color_map.append('black')

        nx.draw_networkx_edges(G, pos, edge_color=edge_color_map, width=width)
    else:
        nx.draw_networkx_edges(G, pos, width=width)

    nx.draw_networkx_nodes(G, pos, node_color=node_color_map, node_size=500)

    # Draw labels
    if "label" in G.nodes[0]:
        nx.draw_networkx_labels(G, pos)
        labels = dict(sorted(nx.get_node_attributes(G, "label").items()))
        label_pos = {node: (coords[0], coords[1] - 0.12) for node, coords in pos.items()}
        nx.draw_networkx_labels(G, label_pos, labels)
    else:
        labels = {node: str(node) for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels)

    # Draw weights
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.axis('off')
