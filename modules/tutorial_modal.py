from shiny import reactive, ui, render
from shiny.types import ImgData
from pathlib import Path

directory = Path("./images").resolve()


def tutorial_modal():
    return ui.input_action_button("tutorial", "Tutorial"),


def tutorial_modal_server(input, output, session):
    @reactive.effect
    @reactive.event(input.tutorial)
    def show_important_message():
        m = ui.modal(

            ui.h4("Step 1"),
            ui.output_image("select_grap_image"),

            "You start by choosing a graph from the following options:", ui.br(),

            ui.accordion(
                ui.accordion_panel("Deutschland Beispiel", "A simple example with some german cities."),
                ui.accordion_panel("Random Graph",
                                   "This works by generating a connected Watts–Strogatz small-world graph.", ui.br(),
                                   "You can tweak the parameters using the sliders."
                                   ),
                ui.accordion_panel("Import from Edgelist",
                                   "This lets you create you own graph by defining a edge list.", ui.br(),
                                   ui.p(),
                                   "An edge is the connection between nodes. You can create edges by defining a tuple with three integers for example:",
                                   ui.br(),
                                   "(0, 1, 10)", ui.br(),
                                   "This will create a connection between nodes 0 and 1 with a distance of 10.", ui.br(),
                                   ui.p(),
                                   "Create multiple edges by separating each tuple with a ','.", ui.br(),
                                   "Make sure that all of the network is connected and there are no loose nodes or multiple unconnected graphs!",
                                   ui.br(),
                                   "Nodes that do not exist yet will be automatically created."
                                   )
            ),

            ui.hr(),
            ui.h4("Step 2"),
            ui.output_image("start_targe_seed_image"),
            "After choosing a graph you can select the start and the target node.", ui.br(),
            "The Dijkstra's algorithm will then try to find the fastest path from the start node to the target node.",
            ui.br(),
            "If you want to change the layout of you graph you simply need to change the layout seed until you find a good looking layout.",
            ui.hr(),
            ui.h4("Step 3"),
            ui.output_image("prev_next_image", height="100%", width="100%"),
            "To see each the algorithm do its work press the next step button. Each step will also be explained on the card below.",
            ui.br(),
            "If you like to look at a previous step, simply press the previous step button.", ui.br(),
            "During this time you can follow what the algorithm already figured out by looking at the distances between nodes table or the visited nodes card.",
            ui.hr(),
            ui.h4("Step 4"),
            "After the algorithm is done it will highlight the fastest way possible for you on the graph and you.",
            ui.br(),
            "At that point you can either go back with the previous step button and review the steps again or start over with a new graph.",
            title="The Dijkstra Algorithm",
            easy_close=True,
            footer=None,
            size='l'
        )
        ui.modal_show(m)

    @render.image
    def select_grap_image():
        img: ImgData = {"src": str(directory / "select_graph.png"), "width": "80%"}
        return img

    @render.image
    def start_targe_seed_image():
        img: ImgData = {"src": str(directory / "start_target_seed.png"), "width": "40%"}
        return img

    @render.image
    def prev_next_image():
        img: ImgData = {"src": str(directory / "prev_next.png"), "width": "100%"}
        return img
