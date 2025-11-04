from shiny import App, ui

from modules.dijkstra_info import dijkstra_info
from modules.graph_ui import graph_ui, graph_ui_server
from modules.project_information import project_information
from modules.settings_ui import settings_ui, settings_ui_server
from modules.copyright_footer import copyright_footer
from modules.participant_id_modal import participant_id_modal_ui, participant_id_modal_server
from localization import _

example_page = ui.page_fluid(
    ui.panel_title("Dijkstra Shiny!"),
    ui.input_slider("n", "N", 0, 100, 20),
    ui.output_text_verbatim("txt"),
)

simple_plot = ui.page_fluid(ui.output_plot("plot"))

simple_graph = ui.page_fluid(ui.output_plot("graph"))

# Create the initial UI with reactive navigation and participant ID modal
app_ui = ui.page_fluid(
    ui.output_ui("dynamic_app_ui"),
    ui.output_ui("participant_modal"),
    ui.tags.script("""
        // Handle hiding the participant modal
        Shiny.addCustomMessageHandler('hideParticipantModal', function(message) {
            $('#participant_modal_overlay').fadeOut(300, function() {
                $(this).remove();
            });
            window.participantIdSet = true;
        });
    """)
)


def server(input, output, session):
    from shiny import render, reactive
    from modules.state_manager import state_manager
    from modules.project_information import get_project_information
    from modules.dijkstra_info import get_dijkstra_info
    from utils.user_logger import get_logger

    # Initialize logger for this session
    logger = get_logger()

    # Register session end handler
    def on_session_end():
        logger.log_session_end()

    session.on_ended(on_session_end)

    # Participant ID modal
    @output
    @render.ui
    def participant_modal():
        """Render participant ID modal initially."""
        if not state_manager.participant_id_set.get():
            return participant_id_modal_ui()
        return ui.div()

    # Dynamic main UI that updates with language changes
    @output
    @render.ui
    @reactive.event(state_manager.current_language)
    def dynamic_app_ui():
        return ui.page_navbar(
            ui.nav_panel(_("nav_start"), ui.div(graph_ui(), copyright_footer(), style="min-height: 100vh; display: flex; flex-direction: column;")),
            ui.nav_panel(_("nav_about"), ui.div(ui.output_ui("dynamic_project_info"), copyright_footer(), style="min-height: 100vh; display: flex; flex-direction: column;")),
            ui.nav_panel(_("nav_algorithm_info"), ui.div(ui.output_ui("dynamic_dijkstra_info"), copyright_footer(), style="min-height: 100vh; display: flex; flex-direction: column;")),
            ui.nav_panel(_("nav_settings"), ui.div(settings_ui(), copyright_footer(), style="min-height: 100vh; display: flex; flex-direction: column;")),
            title=_("app_title"),
        )

    # Dynamic content that updates with language changes
    @output
    @render.ui
    @reactive.event(state_manager.current_language)
    def dynamic_project_info():
        return get_project_information()

    @output
    @render.ui
    @reactive.event(state_manager.current_language)
    def dynamic_dijkstra_info():
        return get_dijkstra_info()

    # Initialize server modules
    participant_id_modal_server(input, output, session)
    graph_ui_server(input, output, session)
    settings_ui_server(input, output, session)


app = App(app_ui, server)
