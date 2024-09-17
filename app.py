from shiny import App, render, ui

example_page =  ui.page_fluid(
    ui.panel_title("Djikstra Shiny!"),
    ui.input_slider("n", "N", 0, 100, 20),
    ui.output_text_verbatim("txt"),
)


app_ui = ui.page_navbar(
        ui.nav_panel("Startseite", example_page),
        ui.nav_panel("Über den Algorithmus", "Page Über den Algorithmus"),
        ui.nav_panel("Über das Projekt", "Page Über das Projekt"),
        title = "Djikstra",
        id = "navbar",
        )



def server(input, output, session):
    @render.text
    def txt():
        return f"n*2 is {input.n() * 2}"


app = App(app_ui, server)
