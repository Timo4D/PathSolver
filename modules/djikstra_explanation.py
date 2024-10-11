from htmltools import TagList, tags

djikstra_explanation = TagList(
    tags.p("a.Algorithm is initialized with distance 0 for the start vertex and ∞ (infinite) <br /> for all other vertices "),
    tags.p("b.The current vertex is selected from the unvisited vertices by the shortest distance from the start "),
    tags.p("c.For the current vertex, provisional distances to all neighboring vertices are calculated / updated "),
    tags.p(
        "d.Repeat (from b.) or stop, when the provisional distance to the destination vertex is less or equal the shortest distance to an unvisited vertex."),
    tags.p(
        "d.Repeat (from b.) or stop, when the provisional distance to the destination vertex is less or equal the shortest distance to an unvisited vertex."),
    tags.p("from Prof. Dr. Christian Koot"),
)
