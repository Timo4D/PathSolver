from shiny import reactive, ui

from modules.tutorial_modal import tutorial_modal


def graph_ui():
    return ui.page_sidebar(
        ui.sidebar(
            ui.input_action_button("show_tutorial", "Tutorial"),
            ui.input_select(
                "graph_select",
                "Select your Graph",
                {
                    "example_graph": "Example Graph",
                    "random_graph": "Random Graph",
                    "import_graph": "Import Graph",
                    "create_graph": "Create your own Graph",
                },
            ),
            bg="ffffff",
        ),
        "Main Content",
    )


def graph_ui_server(input, output, session):
    @reactive.effect
    @reactive.event(input.show_tutorial)
    def _():
        ui.modal_show(tutorial_modal())
