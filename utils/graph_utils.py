import matplotlib.pyplot as plt
import networkx as nx
from networkx.classes import Graph



def dijkstra_solution(G: Graph, start: int, target: int, weight="weight"):
    return nx.dijkstra_path(G, start, target, weight=weight)


def plot_graph(G, start, target, seed, distances=None, current_node=None, current_edges=None, dark_mode=None,
               final_step=False):
    width: int = 3

    if current_edges is None:
        current_edges = []
    if not G:
        return None

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

    if current_edges:
        edge_color_map = []
        for edge in G.edges:
            if tuple(edge) in [tuple(e) for e in current_edges] or tuple(edge[::-1]) in [tuple(e) for e in
                                                                                         current_edges]:
                edge_color_map.append('tab:red')
            else:
                edge_color_map.append('black')

        nx.draw_networkx_edges(G, pos, edge_color=edge_color_map, width=width)
    else:
        nx.draw_networkx_edges(G, pos, edge_color=default_color, width=width)

    nx.draw_networkx_nodes(G, pos, node_color=node_color_map, node_size=400)

    # Draw labels
    if "label" in G.nodes[0]:
        nx.draw_networkx_labels(G, pos)
        labels = dict(sorted(nx.get_node_attributes(G, "label").items()))
        label_pos = {node: (coords[0], coords[1] - 0.13) for node, coords in pos.items()}
        nx.draw_networkx_labels(G, label_pos, labels, font_color=default_color)
    else:
        labels = {node: str(node) for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels)

    # Draw Distances
    if not distances["Cost"].empty:
        distance_labels = distances["Cost"].replace(float('inf'), '∞').apply(
            lambda x: int(x) if isinstance(x, float) else x)

        label_pos = {node: (coords[0], coords[1] + 0.13) for node, coords in pos.items()}
        nx.draw_networkx_labels(G, label_pos, distance_labels, font_color=default_color)

    if not final_step:
        # Draw weights
        edge_labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.axis('off')
