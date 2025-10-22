import random

import networkx as nx


def generate_random_graph(n, k, p):
    G = nx.connected_watts_strogatz_graph(n, k, p)

    # Add random integer weights to edges
    for (u, v) in G.edges():
        G[u][v]['weight'] = random.randint(1, 100)

    # Generate layout positions for Cytoscape visualization
    pos = nx.spring_layout(G, seed=42, scale=200)
    # Add positions as node attributes
    for node, (x, y) in pos.items():
        G.nodes[node]['x'] = x
        G.nodes[node]['y'] = y

    return G


def generate_koot_example():
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

    # Generate layout positions for Cytoscape visualization
    pos = nx.spring_layout(G, seed=42, scale=200)
    # Add positions as node attributes
    for node, (x, y) in pos.items():
        G.nodes[node]['x'] = x
        G.nodes[node]['y'] = y

    return G


def generate_from_real_edge_list(edgelist: str):
    edgelist_correct = "\n".join(
        [f"{u} {v} {{'weight':{w}}}" for u, v, w in (line.split() for line in edgelist.split('\n'))])

    edgelist_lines = edgelist_correct.split('\n')
    G = nx.parse_edgelist(edgelist_lines, nodetype=int)
    # print(edgelist_lines)



    if nx.is_connected(G):
        return G
    else:
        return "Graph is not connected"


def generate_from_edge_list(edgelist: str):
    try:
        edgelist_lines = [f"{u} {v} {{'weight':{w}}}" for u, v, w in (line.split() for line in edgelist.split('\n'))]
        G = nx.parse_edgelist(edgelist_lines, nodetype=int)
    except (ValueError, SyntaxError, TypeError):
        return "Edgelist invalid"

    for line in nx.generate_edgelist(G):
        print(line)

    if nx.is_connected(G):
        # Generate layout positions for Cytoscape visualization
        pos = nx.spring_layout(G, seed=42, scale=200)
        # Add positions as node attributes
        for node, (x, y) in pos.items():
            G.nodes[node]['x'] = x
            G.nodes[node]['y'] = y
        return G
    else:
        return "Graph is not connected"


def generate_from_csv(csv_content: str):
    """Generate graph from CSV format.

    Expected format:
    source,target,weight
    0,1,10
    1,2,15

    Args:
        csv_content: CSV string with header and edge data

    Returns:
        NetworkX Graph object or error string
    """
    try:
        lines = csv_content.strip().split('\n')

        # Skip header if present
        if lines and ('source' in lines[0].lower() or 'node' in lines[0].lower()):
            lines = lines[1:]

        if not lines:
            return "CSV file is empty"

        G = nx.Graph()

        for line in lines:
            if not line.strip():
                continue

            parts = line.strip().split(',')
            if len(parts) < 2:
                return "Invalid CSV format. Expected: source,target,weight"

            try:
                source = int(parts[0].strip())
                target = int(parts[1].strip())
                weight = int(parts[2].strip()) if len(parts) > 2 else 1

                G.add_edge(source, target, weight=weight)
            except ValueError:
                return f"Invalid node or weight value in line: {line}"

        if not nx.is_connected(G):
            return "Graph is not connected"

        # Generate layout positions for Cytoscape visualization
        pos = nx.spring_layout(G, seed=42, scale=200)
        # Add positions as node attributes
        for node, (x, y) in pos.items():
            G.nodes[node]['x'] = x
            G.nodes[node]['y'] = y

        return G

    except Exception as e:
        return f"Error parsing CSV: {str(e)}"
