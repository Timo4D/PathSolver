import uuid
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
    # Hidden input to receive persistent session ID from JavaScript
    ui.input_text("persistent_session_id", "", value=""),
    ui.output_ui("dynamic_app_ui"),
    ui.output_ui("participant_modal"),
    ui.tags.script("""
        // Session persistence - Cookie management
        (function() {
            const COOKIE_NAME = 'pathsolver_session_id';
            const COOKIE_DAYS = 365;  // Session cookie expires in 1 year
            
            function getCookie(name) {
                const value = `; ${document.cookie}`;
                const parts = value.split(`; ${name}=`);
                if (parts.length === 2) return parts.pop().split(';').shift();
                return null;
            }
            
            function setCookie(name, value, days) {
                const date = new Date();
                date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
                document.cookie = `${name}=${value};expires=${date.toUTCString()};path=/;SameSite=Lax`;
            }
            
            function generateSessionId() {
                return 'sess_' + Math.random().toString(36).substr(2, 9) + 
                       '_' + Date.now().toString(36);
            }
            
            // Get or create persistent session ID
            let sessionId = getCookie(COOKIE_NAME);
            if (!sessionId) {
                sessionId = generateSessionId();
                setCookie(COOKIE_NAME, sessionId, COOKIE_DAYS);
                console.log('[Session] Created new persistent session:', sessionId);
            } else {
                console.log('[Session] Restored persistent session:', sessionId);
            }
            
            // Wait for Shiny to be ready, then send session ID to server
            $(document).on('shiny:connected', function() {
                // Update the hidden input with the session ID
                Shiny.setInputValue('persistent_session_id', sessionId);
            });
        })();
        
        // Handle hiding the participant modal
        Shiny.addCustomMessageHandler('hideParticipantModal', function(message) {
            $('#participant_modal_overlay').fadeOut(300, function() {
                $(this).remove();
            });
            window.participantIdSet = true;
        });
        
        // Handle session restored notification
        Shiny.addCustomMessageHandler('sessionRestored', function(message) {
            console.log('[Session] State restored from server');
            // Optionally show a quick toast notification
            if (message.show_notification) {
                // Could add a visual notification here if desired
            }
        });
    """),
    # Hide the session ID input
    ui.tags.style("#persistent_session_id { display: none; }")
)

def server(input, output, session):
    from shiny import render, reactive
    from modules.state_manager import get_session_state_manager
    from modules.project_information import get_project_information
    from modules.dijkstra_info import get_dijkstra_info
    from utils.user_logger import get_session_logger
    from utils.session_persistence import get_persistence

    # Get session-scoped state manager (each user gets their own isolated state)
    state_manager = get_session_state_manager(session)

    # Initialize session-scoped logger (each user gets their own logger instance)
    logger = get_session_logger(session, state_manager)
    
    # Session persistence instance
    persistence = get_persistence()
    
    # Track when session is ready for persistence operations
    persistent_id = reactive.Value(None)
    session_initialized = reactive.Value(False)

    # Restore session when persistent ID is received from client
    @reactive.effect
    @reactive.event(input.persistent_session_id)
    def restore_session_from_cookie():
        session_id = input.persistent_session_id()
        if session_id and len(session_id) > 0:
            persistent_id.set(session_id)
            print(f"[Session] Received persistent session ID: {session_id}")
            
            # Try to restore saved state
            saved_state = persistence.load_session(session_id)
            if saved_state:
                success = state_manager.from_dict(saved_state)
                if success:
                    # Notify client that session was restored
                    session.send_custom_message("sessionRestored", {"show_notification": False})
                    print(f"[Session] Successfully restored session: {session_id}")
            else:
                print(f"[Session] No saved state found for: {session_id} (new session)")
            
            # Mark session as initialized (ready for saving)
            session_initialized.set(True)
    
    # Auto-save session state periodically and on important changes
    @reactive.effect
    @reactive.event(
        state_manager.step_counter,
        state_manager.game_score,
        state_manager.graph,
        state_manager.participant_id,
        state_manager.current_task_index,
        state_manager.completed_tasks,
    )
    def auto_save_session():
        """Auto-save session when important state changes."""
        pid = persistent_id.get()
        # Only save once session is initialized (we've received the session ID)
        if pid and len(pid) > 0 and session_initialized.get():
            state_data = state_manager.to_dict()
            persistence.save_session(pid, state_data)
    
    # Also save on session end
    def on_session_end():
        logger.log_session_end()
        
        # Final save of session state
        pid = persistent_id.get()
        if pid and len(pid) > 0:
            state_data = state_manager.to_dict()
            persistence.save_session(pid, state_data)
            print(f"[Session] Final save on session end: {pid}")

    session.on_ended(on_session_end)

    # Participant ID modal
    @output
    @render.ui
    def participant_modal():
        """Render participant ID modal initially."""
        if not state_manager.participant_id_set.get():
            return participant_id_modal_ui()
        return ui.div()

    # Logging warning modal - polls logger for thread-safe warnings
    @reactive.poll(lambda: logger.has_pending_warning(), 2.0)
    def check_logging_warning():
        """Returns True when there's a pending warning."""
        return logger.has_pending_warning()

    @reactive.effect
    def _show_logging_warning_modal():
        has_warning = check_logging_warning()
        if has_warning:
            # Only show if participant modal is already closed (avoid conflicts)
            if state_manager.participant_id_set.get():
                # Get and clear the warning message
                warning = logger.get_pending_warning()
                if warning:
                    # Show the modal
                    m = ui.modal(
                        ui.div(
                            ui.tags.i(class_="fa fa-exclamation-triangle", style="font-size: 48px; color: #f0ad4e; margin-bottom: 15px;"),
                            ui.h4("Logging Connection Issue", style="margin-bottom: 15px;"),
                            ui.p(warning),
                            ui.p("Your actions are still being saved locally.", style="color: #666; font-size: 0.9em;"),
                            style="text-align: center; padding: 20px;"
                        ),
                        title=None,
                        easy_close=True,
                        footer=ui.modal_button("OK", class_="btn-warning")
                    )
                    ui.modal_show(m)

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

    # Initialize server modules with session-scoped state_manager
    participant_id_modal_server(input, output, session, state_manager)
    graph_ui_server(input, output, session, state_manager)
    settings_ui_server(input, output, session, state_manager)


app = App(app_ui, server)
