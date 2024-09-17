from shiny import App, render, ui
import matplotlib.pyplot as plt
import numpy as np

example_page =  ui.page_fluid(
    ui.panel_title("Djikstra Shiny!"),
    ui.input_slider("n", "N", 0, 100, 20),
    ui.output_text_verbatim("txt"),
)

simple_plot = ui.page_fluid(
        ui.output_plot("plot")
        )

app_ui = ui.page_navbar(
        ui.nav_panel("Startseite", example_page),
        ui.nav_panel("Über den Algorithmus", ui.output_plot("plot")),
        ui.nav_panel("Über das Projekt", "Page Über das Projekt"),
        title = "Djikstra",
        id = "navbar",
        )



def server(input, output, session):

    @render.plot
    def plot():
        
        plt.style.use('_mpl-gallery')

# make data
        np.random.seed(1)
        x = 4 + np.random.normal(0, 1.5, 200)

# plot:
        fig, ax = plt.subplots()

        ax.hist(x, bins=8, linewidth=0.5, edgecolor="white")

        ax.set(xlim=(0, 8), xticks=np.arange(1, 8),
               ylim=(0, 56), yticks=np.linspace(0, 56, 9))
        plt.show()

    @render.text
    def txt():
        return f"n*2 is {input.n() * 2}"


app = App(app_ui, server)
