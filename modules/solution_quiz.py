from shiny import ui

from utils.icons import question_circle_fill


def render_solution_quiz():
    return ui.card(
        ui.card_header("Find the fastest Route"),
        ui.card_body(
            ui.input_text("user_solution", ui.tooltip(
            ui.span("Your Solution: ", question_circle_fill),
            "Input the solution in form if the number from the nodes starting from the start node to the target node. For example: 0, 4, 3",
        ), width="100%", placeholder="1, 4, 5, 3")),
        ui.input_action_button("submit_solution", "Submit", class_="btn-danger"),
        class_="card border-danger border-3"
    )

