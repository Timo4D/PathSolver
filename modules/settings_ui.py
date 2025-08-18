"""Settings UI module for PathSolver application."""

from shiny import ui, render, reactive, req
from modules.state_manager import state_manager
from localization import _, get_available_languages


def settings_ui():
    """Create the settings page UI."""
    return ui.div(
        ui.h2("Settings", class_="mb-4"),
        ui.output_ui("settings_content")
    )


def settings_ui_server(input, output, session):
    """Server logic for the settings UI."""
    
    @output
    @render.ui
    @reactive.event(state_manager.settings_unlocked, state_manager.force_game_difficulty, state_manager.game_enabled, state_manager.force_game_mode, state_manager.graph_font_size, state_manager.current_language, state_manager.solution_quiz_enabled, state_manager.force_solution_quiz)
    def settings_content():
        """Render settings content based on unlock status."""
        
        # Display settings control - always available (accessibility feature)
        display_settings_control = ui.div(
            ui.h4(_("display_settings"), class_="mb-3"),
            ui.input_selectize(
                "app_language",
                _("app_language"),
                choices=get_available_languages(),
                selected=state_manager.current_language()
            ),
            ui.p(
                _("language_help"),
                class_="text-muted small"
            ),
            ui.hr(),
            ui.input_slider(
                "graph_font_size",
                _("graph_font_size"),
                min=8,
                max=36,
                value=state_manager.graph_font_size(),
                step=1,
                post="px"
            ),
            ui.p(
                _("font_size_help"),
                class_="text-muted small"
            ),
            class_="card p-3 mb-4"
        )
        
        if not state_manager.settings_unlocked():
            # Show password protection form with display settings control
            return ui.div(
                display_settings_control,
                ui.div(
                    ui.h4("Administrative Settings", class_="mb-3"),
                    ui.p("Administrative settings are password protected. Please enter the admin password to access them."),
                    ui.input_password("admin_password", "Admin Password:", placeholder="Enter password"),
                    ui.input_action_button("authenticate", "Unlock Settings", class_="btn-primary"),
                    ui.output_ui("auth_message"),
                    class_="card p-3 mb-4 border-warning"
                )
            )
        else:
            # Show settings controls
            return ui.div(
                display_settings_control,
                # Game Feature Toggle
                ui.div(
                    ui.h4("Game Features", class_="mb-3"),
                    ui.input_switch(
                        "settings_game_enabled",
                        "Enable Prediction Game",
                        value=state_manager.game_enabled()
                    ),
                    ui.p(
                        "When enabled, users can predict which node will be visited next during algorithm execution.",
                        class_="text-muted small"
                    ),
                    ui.hr(),
                    ui.div(
                        ui.input_switch(
                            "force_game_mode",
                            "Force Game Mode Always On",
                            value=state_manager.force_game_mode() if state_manager.game_enabled() else False
                        ),
                        ui.p(
                            "When enabled, the prediction game will always be active and users cannot turn it off." + 
                            (" (Requires game feature to be enabled)" if not state_manager.game_enabled() else ""),
                            class_="text-muted small"
                        ),
                        id="force_game_mode_section",
                        style="opacity: 1" if state_manager.game_enabled() else "opacity: 0.5"
                    ),
                    ui.hr(),
                    ui.div(
                        ui.input_selectize(
                            "force_game_difficulty",
                            "Force Game Difficulty",
                            choices={
                                "user_choice": "Allow User Choice",
                                "easy": "🟢 Easy - Full hints and distances shown",
                                "medium": "🟡 Medium - Some visual aids hidden",
                                "hard": "🔴 Hard - Minimal visual information"
                            },
                            selected="user_choice" if state_manager.force_game_difficulty.get() is None else state_manager.force_game_difficulty.get()
                        ),
                        ui.p(
                            "When set, users cannot change the difficulty level and must use the specified setting." +
                            (" (Only applies when game feature is enabled)" if not state_manager.game_enabled() else ""),
                            class_="text-muted small"
                        ),
                        id="force_difficulty_section",
                        style="opacity: 1" if state_manager.game_enabled() else "opacity: 0.5"
                    ),
                    class_="card p-3 mb-4"
                ),
                
                # Solution Quiz Feature Toggle
                ui.div(
                    ui.h4(_("solution_quiz_settings"), class_="mb-3"),
                    ui.input_switch(
                        "settings_solution_quiz_enabled",
                        _("enable_solution_quiz"),
                        value=state_manager.solution_quiz_enabled()
                    ),
                    ui.p(
                        _("solution_quiz_help"),
                        class_="text-muted small"
                    ),
                    ui.hr(),
                    ui.div(
                        ui.input_switch(
                            "force_solution_quiz",
                            _("force_solution_quiz"),
                            value=state_manager.force_solution_quiz() if state_manager.solution_quiz_enabled() else False
                        ),
                        ui.p(
                            _("force_solution_quiz_help") + 
                            (" " + _("requires_quiz_enabled") if not state_manager.solution_quiz_enabled() else ""),
                            class_="text-muted small"
                        ),
                        id="force_solution_quiz_section",
                        style="opacity: 1" if state_manager.solution_quiz_enabled() else "opacity: 0.5"
                    ),
                    class_="card p-3 mb-4"
                ),
                
                # Visualization Mode Toggle
                ui.div(
                    ui.h4("Graph Visualization", class_="mb-3"),
                    ui.input_radio_buttons(
                        "visualization_mode",
                        "Visualization Mode:",
                        choices={
                            "cytoscape": "Interactive Cytoscape.js (Recommended)",
                            "matplotlib": "Static Matplotlib Plots"
                        },
                        selected=state_manager.visualization_mode()
                    ),
                    ui.p(
                        "Cytoscape.js provides interactive graphs with drag-and-drop functionality. "
                        "Matplotlib provides static plots with traditional appearance.",
                        class_="text-muted small"
                    ),
                    class_="card p-3 mb-4"
                ),
                
                # Lock settings button (only if password protected)
                ui.div(
                    ui.input_action_button(
                        "lock_settings", 
                        "Lock Settings", 
                        class_="btn-warning"
                    ),
                    class_="text-center mt-4"
                ) if state_manager.config["settings"]["password_protected"] else None,
                
                # Current settings display
                ui.div(
                    ui.h5("Current Settings", class_="mb-3"),
                    ui.output_ui("current_settings"),
                    class_="card p-3 mt-4 bg-light"
                )
            )
    
    # Authentication message output
    @output
    @render.ui
    def auth_message():
        return ui.div()
    
    # Current settings display
    @output
    @render.ui
    def current_settings():
        game_status = "Enabled" if state_manager.game_enabled() else "Disabled"
        force_game_status = "Yes" if state_manager.force_game_mode() else "No"
        force_difficulty = state_manager.force_game_difficulty.get()
        force_difficulty_status = force_difficulty.title() if force_difficulty else "User Choice"
        quiz_status = "Enabled" if state_manager.solution_quiz_enabled() else "Disabled"
        force_quiz_status = "Yes" if state_manager.force_solution_quiz() else "No"
        viz_mode = "Interactive (Cytoscape.js)" if state_manager.visualization_mode() == "cytoscape" else "Static (Matplotlib)"
        font_size = state_manager.graph_font_size()
        
        return ui.div(
            ui.p(f"Game Feature: {game_status}"),
            ui.p(f"Force Game Mode: {force_game_status}"),
            ui.p(f"Force Game Difficulty: {force_difficulty_status}"),
            ui.p(f"Solution Quiz: {quiz_status}"),
            ui.p(f"Force Solution Quiz: {force_quiz_status}"),
            ui.p(f"Visualization Mode: {viz_mode}"),
            ui.p(f"Graph Font Size: {font_size}px"),
            ui.p(f"Password Protection: {'Yes' if state_manager.config['settings']['password_protected'] else 'No'}")
        )
    
    # Authentication handler
    @reactive.Effect
    @reactive.event(input.authenticate)
    def handle_authentication():
        password = input.admin_password()
        if password:
            if state_manager.authenticate_settings(password):
                # Clear password field and show success message
                ui.update_text("admin_password", value="")
                ui.notification_show(
                    "Settings unlocked successfully!", 
                    type="success",
                    duration=3
                )
            else:
                ui.notification_show(
                    "Incorrect password. Please try again.", 
                    type="error",
                    duration=3
                )
    
    # Lock settings handler
    @reactive.Effect
    @reactive.event(input.lock_settings)
    def handle_lock_settings():
        state_manager.lock_settings()
        ui.notification_show(
            "Settings have been locked.", 
            type="info",
            duration=3
        )
    
    # Game feature toggle handler
    @reactive.Effect
    def handle_game_toggle():
        if state_manager.settings_unlocked():
            enabled = input.settings_game_enabled()
            if enabled is not None:
                # If disabling game feature, also disable force mode
                if not enabled and state_manager.force_game_mode():
                    state_manager.update_force_game_mode(False)
                    ui.update_switch("force_game_mode", value=False)
                
                state_manager.update_game_setting(enabled)
                status = "enabled" if enabled else "disabled"
                ui.notification_show(
                    f"Game feature {status}.", 
                    type="success",
                    duration=2
                )
                
                # Update the force game mode toggle visibility/state
                ui.update_switch("force_game_mode", value=state_manager.force_game_mode() if enabled else False)
    
    # Force game mode handler
    @reactive.Effect
    def handle_force_game_mode():
        if state_manager.settings_unlocked():
            enabled = input.force_game_mode()
            if enabled is not None:
                # Only allow force mode if main game feature is enabled
                if enabled and not state_manager.game_enabled():
                    ui.update_switch("force_game_mode", value=False)
                    ui.notification_show(
                        "Cannot force game mode when game feature is disabled.", 
                        type="warning",
                        duration=3
                    )
                    return
                
                state_manager.update_force_game_mode(enabled)
                status = "enabled" if enabled else "disabled"
                ui.notification_show(
                    f"Force game mode {status}.", 
                    type="success",
                    duration=2
                )
    
    # Force game difficulty handler
    @reactive.Effect
    @reactive.event(input.force_game_difficulty)
    def handle_force_game_difficulty():
        if state_manager.settings_unlocked():
            difficulty = input.force_game_difficulty()
            
            # Allow processing of values
            if difficulty is not None:
                # Convert "user_choice" to None for "Allow User Choice"
                difficulty_value = difficulty if difficulty != "user_choice" else None
                current_difficulty = state_manager.force_game_difficulty.get()
                
                if difficulty_value != current_difficulty:  # Only update if actually changed
                    state_manager.update_force_game_difficulty(difficulty_value)
                    difficulty_name = difficulty_value.title() if difficulty_value else "User Choice"
                    ui.notification_show(
                        f"Force game difficulty set to {difficulty_name}.", 
                        type="success",
                        duration=2
                    )
    
    # Visualization mode handler
    @reactive.Effect
    def handle_visualization_mode():
        if state_manager.settings_unlocked():
            mode = input.visualization_mode()
            if mode is not None:
                current_mode = state_manager.visualization_mode()
                if mode != current_mode:  # Only update if actually changed
                    state_manager.update_visualization_mode(mode)
                    mode_name = "Interactive (Cytoscape.js)" if mode == "cytoscape" else "Static (Matplotlib)"
                    ui.notification_show(
                        f"Visualization mode changed to {mode_name}.", 
                        type="success",
                        duration=2
                    )
    
    # Language handler - always active (accessibility feature)  
    @reactive.Effect
    def handle_language():
        language = input.app_language()
        if language is not None:
            current_lang = state_manager.current_language()
            if language != current_lang:  # Only update if actually changed
                if state_manager.update_language(language):
                    ui.notification_show(
                        _("language_changed", language=language), 
                        type="success",
                        duration=2
                    )
                    # Force UI refresh by invalidating all reactive components
                    state_manager.current_language.set(language)
    
    # Solution quiz feature toggle handler
    @reactive.Effect
    def handle_solution_quiz_toggle():
        if state_manager.settings_unlocked():
            enabled = input.settings_solution_quiz_enabled()
            if enabled is not None:
                # If disabling solution quiz feature, also disable force mode
                if not enabled and state_manager.force_solution_quiz():
                    state_manager.update_force_solution_quiz(False)
                    ui.update_switch("force_solution_quiz", value=False)
                
                state_manager.update_solution_quiz_setting(enabled)
                status = "enabled" if enabled else "disabled"
                ui.notification_show(
                    f"Solution quiz feature {status}.", 
                    type="success",
                    duration=2
                )
                
                # Update the force solution quiz toggle visibility/state
                ui.update_switch("force_solution_quiz", value=state_manager.force_solution_quiz() if enabled else False)
    
    # Force solution quiz handler
    @reactive.Effect
    def handle_force_solution_quiz():
        if state_manager.settings_unlocked():
            enabled = input.force_solution_quiz()
            if enabled is not None:
                # Only allow force mode if main solution quiz feature is enabled
                if enabled and not state_manager.solution_quiz_enabled():
                    ui.update_switch("force_solution_quiz", value=False)
                    ui.notification_show(
                        "Cannot force solution quiz when solution quiz feature is disabled.", 
                        type="warning",
                        duration=3
                    )
                    return
                
                state_manager.update_force_solution_quiz(enabled)
                status = "enabled" if enabled else "disabled"
                ui.notification_show(
                    f"Force solution quiz {status}.", 
                    type="success",
                    duration=2
                )
    
    # Font size handler - always active (accessibility feature)
    @reactive.Effect
    def handle_font_size():
        font_size = input.graph_font_size()
        if font_size is not None:
            current_size = state_manager.graph_font_size()
            if font_size != current_size:  # Only update if actually changed
                state_manager.update_graph_font_size(font_size)
                ui.notification_show(
                    _("font_size_changed", size=font_size), 
                    type="success",
                    duration=2
                )
    
    # Initialize settings inputs based on current state
    @reactive.Effect
    def initialize_settings():
        # Language and font size are always available (accessibility features)
        ui.update_selectize("app_language", selected=state_manager.current_language())
        ui.update_slider("graph_font_size", value=state_manager.graph_font_size())
        
        if state_manager.settings_unlocked():
            ui.update_switch("settings_game_enabled", value=state_manager.game_enabled())
            ui.update_switch("force_game_mode", value=state_manager.force_game_mode())
            ui.update_selectize("force_game_difficulty", selected="user_choice" if state_manager.force_game_difficulty.get() is None else state_manager.force_game_difficulty.get())
            ui.update_switch("settings_solution_quiz_enabled", value=state_manager.solution_quiz_enabled())
            ui.update_switch("force_solution_quiz", value=state_manager.force_solution_quiz())
            ui.update_radio_buttons("visualization_mode", selected=state_manager.visualization_mode())