from htmltools import TagList, tags

djikstra_explanation = TagList(
    tags.p("0. Algorithm is initialized with distance 0 for the start node and ∞ (infinite) for all other nodes"),
    tags.p("1.The current node is selected from the unvisited vertices by the shortest distance from the start "),
    tags.p("2. For the current node, provisional distances to all neighboring vertices are calculated / updated "),
    tags.p(
        "3. Repeat (from 1.) or stop, when the provisional distance to the destination node is less or equal the shortest distance to an unvisited node."),
)
