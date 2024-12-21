from htmltools import TagList, tags

project_information = TagList(
    tags.p("This application was developed as part of a bachelor's thesis at Aalen University."),
    tags.p(
        "The goal of the project was to provide a user-friendly and interactive visualization of the Dijkstra algorithm, specifically suitable for didactic use in lectures and exercises."),
    tags.p(
        "The application allows users to understand the functionality of the Dijkstra algorithm through step-by-step explanations and color highlights directly in the graph."),
    tags.p(
        "Learners and teachers can use both predefined and self-created graphs to explore and apply the algorithm."),
    tags.p(
        "The project is based on the Python library Shiny for Python, combined with NetworkX for graph representation and analysis."),
    tags.p(
        "The development of the application was guided by best practices from research on algorithm visualization."),
    tags.p(
        "The project exemplifies the connection between computer science and pedagogy and offers an innovative solution for conveying complex algorithmic concepts."),
    tags.p("You can find the sourcecode for this App on https://github.com/Timo4D/Dijkstra")
)
