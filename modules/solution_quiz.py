from shiny import ui
from localization import _

from utils.icons import question_circle_fill


def render_solution_quiz():
    return ui.card(
        ui.card_header(_("find_fastest_route")),
        ui.card_body(
            ui.input_text("user_solution", ui.tooltip(
                ui.span(_("your_solution"), question_circle_fill),
                _("solution_format_help"),
            ), width="100%", placeholder=_("solution_placeholder"))),
        ui.input_action_button("submit_solution", _("submit_solution"), class_="btn-danger"),
        class_="card border-danger border-3"
    )
