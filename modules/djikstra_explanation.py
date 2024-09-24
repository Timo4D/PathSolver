from htmltools import TagList, tags

djikstra_explanation = TagList(
    tags.h3("Djikstra"),
    tags.br(),
    tags.ol(
        tags.li("Algorithm is initialized with distance 0 for the start vertex and infinite for all other vertices"),
        tags.li("The current vertex is selected from the unvisited vertices by the shortest distance from the start"),
        tags.li("For the current vertex, provisional distances to all neighboring vertices are calculated / updated"),
        tags.li(
            "Repeat (from 2.) or stop, when the provisional distance to the destination vertex is less or equal the shortest distance to an unvisited vertex")
    )
)
