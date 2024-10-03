import ast
import random

import networkx as nx


def generate_random_graph(n, k, p):
    print("random")

    G = nx.connected_watts_strogatz_graph(n, k, p)

    # Add random integer weights to edges
    for (u, v) in G.edges():
        G[u][v]['weight'] = random.randint(1, 100)

    return G


def generate_koot_example():
    print("koot")
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
    print(nx.to_edgelist(G))
    return G


def generate_from_edge_list(edgelist: str):
    try:
        edges = ast.literal_eval(f'[{edgelist}]')
    except (SyntaxError, ValueError) as e:
        print(f"Error parsing edge list: {e}")
        return "Invalid Edge List"

    converted_edges = []
    for edge in edges:
        if len(edge) == 3:
            u, v, w = edge
            converted_edges.append((u, v, {'weight': w}))
        elif len(edge) == 2:
            u, v = edge
            converted_edges.append((u, v))

    print(converted_edges)
    # try:
    G = nx.from_edgelist(converted_edges)
    # except

    if nx.is_connected(G):
        return G
    else:
        return "Graph is not connected"
