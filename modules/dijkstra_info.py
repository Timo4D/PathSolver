from htmltools import TagList, tags
from localization import _

def get_dijkstra_info():
    """Get localized Dijkstra information content."""
    return TagList(
        tags.p(_("dijkstra_sources_intro")),
        tags.ul(
            tags.li(_("original_paper"),
                    tags.a("https://doi.org/10.1007/BF01386390", href="https://doi.org/10.1007/BF01386390")),
            tags.li(_("wikipedia_link"), tags.a("https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm",
                                          href="https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm")),
            tags.li(_("w3schools_link"), tags.a("https://www.w3schools.com/dsa/dsa_algo_graphs_dijkstra.php",
                                          href="https://www.w3schools.com/dsa/dsa_algo_graphs_dijkstra.php")),
            tags.li(_("freecodecamp_link"),
                    tags.a("https://www.freecodecamp.org/news/dijkstras-shortest-path-algorithm-visual-introduction/",
                           href="https://www.freecodecamp.org/news/dijkstras-shortest-path-algorithm-visual-introduction/")),
            tags.li(_("german_video"),
                    tags.a("https://youtu.be/KiOso3VE-vI?si=57XbxgaRLpkY47Bz",
                           href="https://youtu.be/KiOso3VE-vI?si=57XbxgaRLpkY47Bz"))
        )
    )

# Create the Dijkstra information content - this will be updated when language changes
dijkstra_info = get_dijkstra_info()

def update_dijkstra_info():
    """Update the global dijkstra_info when language changes."""
    global dijkstra_info
    dijkstra_info = get_dijkstra_info()
