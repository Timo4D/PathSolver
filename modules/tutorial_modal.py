from shiny import reactive, ui, render
from localization import _


def tutorial_modal():
    return ui.input_action_button("tutorial", _("tutorial_button")),


class InteractiveTutorial:
    """Interactive tutorial system that guides users through each UI element."""
    
    def __init__(self):
        self.current_step = reactive.value(0)
        self.is_active = reactive.value(False)
        self.show_skip_option = reactive.value(True)
        
        # Tutorial steps with their content and target elements
        self.steps = self.get_localized_steps()
    
    def get_localized_steps(self):
        """Get tutorial steps with localized text."""
        return [
            {
                "title": _("tutorial_welcome_title"),
                "content": _("tutorial_welcome_content"),
                "highlight_element": None,
                "action": None
            },
            {
                "title": _("tutorial_graph_selection_title"),
                "content": _("tutorial_graph_selection_content"),
                "highlight_element": "selectize_graph",
                "action": _("tutorial_graph_settings_action")
            },
            {
                "title": _("tutorial_prediction_game_title"),
                "content": _("tutorial_prediction_game_content"),
                "highlight_element": "game_enabled",
                "action": _("tutorial_prediction_game_action")
            },
            {
                "title": _("tutorial_graph_settings_title"),
                "content": _("tutorial_graph_settings_content"),
                "highlight_element": "graph_generator_settings",
                "action": _("tutorial_graph_settings_action")
            },
            {
                "title": _("tutorial_start_node_title"),
                "content": _("tutorial_start_node_content"),
                "highlight_element": "start_node",
                "action": _("tutorial_start_node_action")
            },
            {
                "title": _("tutorial_target_node_title"), 
                "content": _("tutorial_target_node_content"),
                "highlight_element": "target_node",
                "action": _("tutorial_target_node_action")
            },
            {
                "title": _("tutorial_algorithm_controls_title"),
                "content": _("tutorial_algorithm_controls_content"),
                "highlight_element": "next_step",
                "action": _("tutorial_algorithm_controls_action")
            },
            {
                "title": _("tutorial_distances_table_title"),
                "content": _("tutorial_distances_table_content"),
                "highlight_element": "display_distances",
                "action": _("tutorial_distances_table_action")
            },
            {
                "title": _("tutorial_visited_nodes_title"),
                "content": _("tutorial_visited_nodes_content"),
                "highlight_element": "visited_nodes",
                "action": _("tutorial_visited_nodes_action")
            },
            {
                "title": _("tutorial_algorithm_explanation_title"),
                "content": _("tutorial_algorithm_explanation_content"),
                "highlight_element": "explain",
                "action": _("tutorial_algorithm_explanation_action")
            },
            {
                "title": _("tutorial_ready_title"),
                "content": _("tutorial_ready_content"),
                "highlight_element": None,
                "action": None
            }
        ]
    
    def get_current_step(self):
        return self.steps[self.current_step()]
    
    def has_next_step(self):
        return self.current_step() < len(self.steps) - 1
    
    def has_previous_step(self):
        return self.current_step() > 0
    
    def next_step(self):
        if self.has_next_step():
            self.current_step.set(self.current_step() + 1)
    
    def previous_step(self):
        if self.has_previous_step():
            self.current_step.set(self.current_step() - 1)
    
    def start_tutorial(self):
        self.current_step.set(0)
        self.is_active.set(True)
        self.show_skip_option.set(True)
    
    def end_tutorial(self):
        self.is_active.set(False)
        self.show_skip_option.set(False)


def tutorial_modal_server(input, output, session):
    tutorial = InteractiveTutorial()
    
    @reactive.effect
    @reactive.event(input.tutorial)
    def show_tutorial():
        tutorial.start_tutorial()
        show_tutorial_modal()
    
    def show_tutorial_modal():
        current_step = tutorial.get_current_step()
        
        # Create modal content
        modal_content = []
        
        # Step counter
        modal_content.append(
            ui.div(
                _("tutorial_step_counter", step=tutorial.current_step() + 1, total=len(tutorial.steps)),
                style="text-align: center; color: #666; font-size: 0.9em; margin-bottom: 10px;"
            )
        )
        
        # Step title
        modal_content.append(ui.h4(current_step["title"]))
        
        # Step content
        modal_content.append(ui.p(current_step["content"]))
        
        # Highlight indicator if element is being highlighted
        if current_step["highlight_element"]:
            element_name = current_step['highlight_element'].replace('_', ' ').title()
            modal_content.append(
                ui.div(
                    _("tutorial_highlight_element", element=element_name),
                    style="background-color: #fff3cd; padding: 8px; border-radius: 5px; font-weight: 500; margin: 8px 0; border-left: 4px solid #ff6b35;"
                )
            )
        
        # Action hint if present
        if current_step["action"]:
            modal_content.append(
                ui.div(
                    _("tutorial_action_hint", action=current_step['action']),
                    style="background-color: #e7f3ff; padding: 10px; border-radius: 5px; font-style: italic; margin: 10px 0;"
                )
            )
        
        # Navigation buttons
        nav_buttons = []
        
        # Skip button (only show at start)
        if tutorial.show_skip_option() and tutorial.current_step() == 0:
            nav_buttons.append(
                ui.input_action_button(
                    "tutorial_skip", 
                    _("tutorial_skip"),
                    class_="btn-secondary"
                )
            )
        
        # Previous button
        if tutorial.has_previous_step():
            nav_buttons.append(
                ui.input_action_button(
                    "tutorial_previous", 
                    _("tutorial_previous"),
                    class_="btn-outline-primary"
                )
            )
        
        # Next/Finish button
        if tutorial.has_next_step():
            nav_buttons.append(
                ui.input_action_button(
                    "tutorial_next", 
                    _("tutorial_next"),
                    class_="btn-primary"
                )
            )
        else:
            nav_buttons.append(
                ui.input_action_button(
                    "tutorial_finish", 
                    _("tutorial_finish"),
                    class_="btn-success"
                )
            )
        
        modal_content.append(
            ui.div(
                *nav_buttons,
                style="display: flex; justify-content: space-between; margin-top: 20px;"
            )
        )
        
        # Create and show modal with custom styling
        m = ui.modal(
            *modal_content,
            title=_("interactive_tutorial"),
            easy_close=False,
            footer=None,
            size='m'
        )
        
        # Add custom CSS and JavaScript to remove backdrop blur and make dialog draggable
        modal_custom_css = ui.tags.style("""
            /* Completely remove backdrop */
            .modal-backdrop {
                display: none !important;
                background: none !important;
                background-color: transparent !important;
                backdrop-filter: none !important;
                opacity: 0 !important;
            }
            
            /* Ensure modal shows without backdrop */
            .modal.show {
                background: none !important;
            }
            
            /* Style the modal dialog */
            .modal-dialog {
                position: fixed !important;
                top: 20px !important;
                right: 20px !important;
                margin: 0 !important;
                max-width: 400px !important;
                width: 400px !important;
                z-index: 1060 !important;
            }
            
            /* Make modal draggable */
            .modal-header {
                cursor: move;
                background-color: #007bff;
                color: white;
                border-radius: 0.375rem 0.375rem 0 0;
                user-select: none;
            }
            
            .modal-title {
                color: white !important;
                font-weight: 600;
                pointer-events: none;
            }
            
            /* Add shadow for better visibility */
            .modal-content {
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
                border: 2px solid #007bff !important;
                border-radius: 0.5rem !important;
            }
            
            /* Style the modal body */
            .modal-body {
                font-size: 0.95rem;
                line-height: 1.5;
            }
            
            /* Dragging state */
            .modal-dialog.dragging {
                transition: none !important;
            }
        """)
        
        # JavaScript for draggable functionality
        draggable_js = ui.tags.script(f"""
            // Tutorial draggable functionality - Step {tutorial.current_step() + 1}
            (function() {{
                let tutorialState = {{
                    isDragging: false,
                    currentX: 0,
                    currentY: 0,
                    initialX: 0,
                    initialY: 0,
                    xOffset: 0,
                    yOffset: 0
                }};
                
                function makeTutorialDraggable() {{
                    const modal = document.querySelector('.modal-dialog');
                    const header = document.querySelector('.modal-header');
                    
                    if (!modal || !header) {{
                        setTimeout(makeTutorialDraggable, 100);
                        return;
                    }}
                    
                    // Remove existing listeners to avoid duplicates
                    header.removeEventListener('mousedown', dragStart);
                    document.removeEventListener('mousemove', drag);
                    document.removeEventListener('mouseup', dragEnd);
                    
                    // Add new listeners
                    header.addEventListener('mousedown', dragStart);
                    document.addEventListener('mousemove', drag);
                    document.addEventListener('mouseup', dragEnd);
                    
                    // Preserve position if modal was already moved
                    if (tutorialState.xOffset !== 0 || tutorialState.yOffset !== 0) {{
                        modal.style.transform = `translate(${{tutorialState.xOffset}}px, ${{tutorialState.yOffset}}px)`;
                        modal.style.top = '0px';
                        modal.style.right = 'auto';
                        modal.style.left = '0px';
                    }}
                }}
                
                function dragStart(e) {{
                    tutorialState.initialX = e.clientX - tutorialState.xOffset;
                    tutorialState.initialY = e.clientY - tutorialState.yOffset;
                    
                    const header = document.querySelector('.modal-header');
                    if (e.target === header || header.contains(e.target)) {{
                        tutorialState.isDragging = true;
                        const modal = document.querySelector('.modal-dialog');
                        modal.classList.add('dragging');
                    }}
                }}
                
                function drag(e) {{
                    if (tutorialState.isDragging) {{
                        e.preventDefault();
                        tutorialState.currentX = e.clientX - tutorialState.initialX;
                        tutorialState.currentY = e.clientY - tutorialState.initialY;
                        
                        tutorialState.xOffset = tutorialState.currentX;
                        tutorialState.yOffset = tutorialState.currentY;
                        
                        const modal = document.querySelector('.modal-dialog');
                        const rect = modal.getBoundingClientRect();
                        const maxX = window.innerWidth - rect.width;
                        const maxY = window.innerHeight - rect.height;
                        
                        tutorialState.currentX = Math.min(Math.max(0, tutorialState.currentX), maxX);
                        tutorialState.currentY = Math.min(Math.max(0, tutorialState.currentY), maxY);
                        
                        modal.style.transform = `translate(${{tutorialState.currentX}}px, ${{tutorialState.currentY}}px)`;
                        modal.style.top = '0px';
                        modal.style.right = 'auto';
                        modal.style.left = '0px';
                    }}
                }}
                
                function dragEnd(e) {{
                    tutorialState.initialX = tutorialState.currentX;
                    tutorialState.initialY = tutorialState.currentY;
                    tutorialState.isDragging = false;
                    const modal = document.querySelector('.modal-dialog');
                    if (modal) modal.classList.remove('dragging');
                }}
                
                // Initialize draggable functionality
                setTimeout(makeTutorialDraggable, 50);
            }})();
        """)
        
        # JavaScript to force remove backdrop
        remove_backdrop_js = ui.tags.script("""
            setTimeout(function() {
                // Remove all modal backdrops
                const backdrops = document.querySelectorAll('.modal-backdrop');
                backdrops.forEach(backdrop => backdrop.remove());
                
                // Ensure body doesn't have modal-open class side effects
                document.body.style.overflow = 'auto';
                document.body.style.paddingRight = '';
            }, 50);
        """)
        
        # Add the CSS and JavaScript, then show modal
        ui.insert_ui(ui.tags.head(modal_custom_css), selector="head", where="beforeEnd")
        ui.insert_ui(draggable_js, selector="body", where="beforeEnd")
        ui.insert_ui(remove_backdrop_js, selector="body", where="beforeEnd")
        ui.modal_show(m)
    
    @reactive.effect
    @reactive.event(input.tutorial_next)
    def handle_next():
        tutorial.next_step()
        show_tutorial_modal()
    
    @reactive.effect  
    @reactive.event(input.tutorial_previous)
    def handle_previous():
        tutorial.previous_step()
        show_tutorial_modal()
    
    @reactive.effect
    @reactive.event(input.tutorial_finish, input.tutorial_skip)
    def handle_finish():
        tutorial.end_tutorial()
        ui.modal_remove()
        
        # Clean up any remaining backdrop elements
        cleanup_js = ui.tags.script("""
            setTimeout(function() {
                const backdrops = document.querySelectorAll('.modal-backdrop');
                backdrops.forEach(backdrop => backdrop.remove());
                document.body.style.overflow = 'auto';
                document.body.style.paddingRight = '';
                document.body.classList.remove('modal-open');
            }, 100);
        """)
        ui.insert_ui(cleanup_js, selector="body", where="beforeEnd")
    
    # Add highlight effect for elements when tutorial is active
    @render.ui
    def tutorial_highlight_style():
        if not tutorial.is_active():
            return ""
        
        current_step = tutorial.get_current_step()
        highlight_element = current_step.get("highlight_element")
        
        if not highlight_element:
            return ""
        
        # CSS to highlight the target element
        return ui.tags.style(f"""
            #{highlight_element} {{
                border: 3px solid #007bff !important;
                border-radius: 5px !important;
                box-shadow: 0 0 10px rgba(0, 123, 255, 0.5) !important;
            }}
            
        """)
    
    # Return the tutorial object so main server can access state
    return tutorial

