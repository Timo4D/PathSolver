"""Participant ID entry module for evaluation studies."""

from shiny import ui, render, reactive
# Note: state_manager is now passed as a parameter to participant_id_modal_server for session isolation


def participant_id_modal_ui():
    """Create the participant ID entry modal."""
    return ui.div(
        ui.div(
            ui.div(
                ui.div(
                    ui.h3("Welcome to PathSolver Evaluation", class_="mb-3"),
                    ui.p(
                        "This application is part of a research study. "
                        "Please enter your participant ID to continue.",
                        class_="mb-3"
                    ),
                    ui.input_text(
                        "participant_id_input",
                        "Participant ID:",
                        placeholder="e.g., P001, USER123, etc.",
                        width="100%"
                    ),
                    ui.p(
                        "Note: Your participant ID will be used to track your session for research purposes only.",
                        class_="text-muted small mb-3"
                    ),
                    ui.input_action_button(
                        "confirm_participant_id",
                        "Start Session",
                        class_="btn-primary btn-lg w-100"
                    ),
                    ui.output_ui("participant_id_error"),
                    class_="card p-4 shadow-lg",
                    style="max-width: 500px; width: 100%;"
                ),
                class_="d-flex justify-content-center align-items-center",
                style="min-height: 100vh; padding: 20px;"
            ),
            id="participant_modal_overlay",
            style="""
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                z-index: 9999;
                display: flex;
                justify-content: center;
                align-items: center;
            """
        ),
        ui.tags.script("""
            // Prevent closing modal with escape key or clicking outside
            $(document).ready(function() {
                $(document).on('keydown', function(e) {
                    if (!window.participantIdSet && e.key === 'Escape') {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                });

                $('#participant_modal_overlay').on('click', function(e) {
                    if (!window.participantIdSet && e.target === this) {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                });
            });
        """)
    )


def participant_id_modal_server(input, output, session, state_manager):
    """Server logic for participant ID modal.
    
    Args:
        input: Shiny input object
        output: Shiny output object
        session: Shiny session object
        state_manager: Session-scoped StateManager instance
    """

    @output
    @render.ui
    def participant_id_error():
        """Display error message if participant ID is invalid."""
        return ui.div()

    @reactive.Effect
    @reactive.event(input.confirm_participant_id)
    async def handle_participant_id():
        """Handle participant ID submission."""
        participant_id = input.participant_id_input()

        # Validate participant ID
        if not participant_id or not participant_id.strip():
            # Show error message
            @render.ui
            def participant_id_error():
                return ui.div(
                    ui.tags.div(
                        "⚠️ Please enter a valid participant ID.",
                        class_="alert alert-danger mt-3"
                    )
                )
            return

        # Clean the participant ID (remove extra whitespace)
        participant_id = participant_id.strip()

        # Set the participant ID in state manager
        state_manager.set_participant_id(participant_id)

        # Hide the modal using JavaScript
        await session.send_custom_message('hideParticipantModal', {})

        # Show success notification
        ui.notification_show(
            f"Session started with participant ID: {participant_id}",
            type="success",
            duration=3
        )
