from htmltools import TagList, tags

dijkstra_info = TagList(
    tags.p(
        "I don not own any of this content but these sources can provide you with more Information's about the Dijkstra Algorithm"),
    tags.ul(
        tags.li("Original Dijkstra paper: ",
                tags.a("https://doi.org/10.1007/BF01386390", href="https://doi.org/10.1007/BF01386390")),
        tags.li("Wikipedia: ", tags.a("https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm",
                                      href="https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm")),
        tags.li("w3schools: ", tags.a("https://www.w3schools.com/dsa/dsa_algo_graphs_dijkstra.php",
                                      href="https://www.w3schools.com/dsa/dsa_algo_graphs_dijkstra.php")),
        tags.li("freeCodeCamp: ",
                tags.a("https://www.freecodecamp.org/news/dijkstras-shortest-path-algorithm-visual-introduction/",
                       href="https://www.freecodecamp.org/news/dijkstras-shortest-path-algorithm-visual-introduction/")),
        tags.li("German YouTube Video from Florian Dalwigk: ",
                tags.a("https://youtu.be/KiOso3VE-vI?si=57XbxgaRLpkY47Bz",
                       href="https://youtu.be/KiOso3VE-vI?si=57XbxgaRLpkY47Bz"))
    )
)
