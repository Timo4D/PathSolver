import os

from shiny import *
import networkx as nx
from pyvis.network import Network

# set up a static_assets folder for holding the Network()'s html file
DIR = os.path.dirname(os.path.abspath(__file__))
WWW = os.path.join(DIR, "www")

PYVIS_OUTPUT_ID = "pyvis"

ui_app = ui.page_fluid(
    ui.output_ui(PYVIS_OUTPUT_ID),
)


def server(input: Inputs, output: Outputs, session: Session):
    @output(id=PYVIS_OUTPUT_ID)
    @render.ui
    def _():
        edges = [
            (0, 6, 35), (0, 7, 224), (1, 2, 291), (1, 3, 128), (1, 4, 137),
            (2, 4, 292), (3, 5, 99), (3, 7, 112), (4, 6, 270), (5, 7, 151)
        ]

        # Create a graph
        G = nx.Graph()
        for u, v, d in edges:
            G.add_edge(u, v, weight=d)

        net = Network()
        net.from_nx(G)
        net.toggle_drag_nodes(False)

        net.generate_html(local=False)
        f = os.path.join(WWW, PYVIS_OUTPUT_ID + ".html")
        with open(f, "w") as f:
            f.write(net.html)

        return ui.tags.iframe(
            src=PYVIS_OUTPUT_ID + ".html",
            style="height:600px;width:100%;",
            scrolling="no",
            seamless="seamless",
            frameBorder="0",
        )


app = App(ui=ui_app, server=server, static_assets=WWW)
