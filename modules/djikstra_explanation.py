from htmltools import TagList, tags


def djikstra_explanation(step: int):
    active_style = "border-radius: 10px;box-shadow: 0 0 0 5px red;padding: 5px;"
    print("step",step)

    return TagList(
        tags.p(
            "a.Algorithm is initialized with distance 0 for the start vertex and ∞ (infinite) for all other vertices ",
            style = active_style if step==1 else ""
        ),
        tags.p(
            "b.The current vertex is selected from the unvisited vertices by the shortest distance from the start ",
            style = active_style if step == (2 or 3) else ""
        ),
        tags.p(
            "c.For the current vertex, provisional distances to all neighboring vertices are calculated / updated "
        ),
        tags.p(
            "d.Repeat (from b.) or stop, when the provisional distance to the destination vertex is less or equal the shortest distance to an unvisited vertex."),
        tags.p(
            "d.Repeat (from b.) or stop, when the provisional distance to the destination vertex is less or equal the shortest distance to an unvisited vertex."),
        tags.p("from Prof. Dr. Christian Koot"),
    )
