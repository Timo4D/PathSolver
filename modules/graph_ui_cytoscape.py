"""Graph UI module with Cytoscape.js integration."""

from htmltools import TagList
from shiny import ui, render, reactive
from shiny.types import FileInfo
import networkx as nx
import pandas as pd

from constants import DEFAULT_EDGE_LIST_PATH, STEP_FINISH
from modules.state_manager import state_manager
from modules.ui_components import (
    GraphType, create_progress_bar, create_explanation_ui,
    render_graph_generator_settings, render_error_tooltip, render_distances_table,
    graph_selection_ui
)
from modules.algorithm_logic import DijkstraStepHandler
from modules.solution_quiz import render_solution_quiz
from modules.tutorial_modal import tutorial_modal_server
from modules.cytoscape_component import CytoscapeRenderer, cytoscape_graph
from utils.graph_generators import generate_random_graph, generate_koot_example, generate_from_edge_list


def cytoscape_graph_ui():
    """Graph UI with Cytoscape.js component."""
    return ui.page_fluid(
        ui.row(
            ui.column(
                4,
                ui.card(
                    ui.card_header("Graph Controls"),
                    graph_selection_ui(),
                    ui.output_ui("graph_generator_settings"),
                    ui.br(),
                    ui.input_selectize(
                        "start_node",
                        "Start Node:",
                        choices=[],
                        selected=None
                    ),
                    ui.output_ui("start_node_error_message"),
                    ui.input_selectize(
                        "target_node", 
                        "Target Node:",
                        choices=[],
                        selected=None
                    ),
                    ui.output_ui("target_node_error_message"),
                    ui.br(),
                    ui.input_numeric(
                        "layout_seed",
                        "Layout Seed:",
                        value=42,
                        min=1,
                        max=1000
                    )
                ),
                ui.card(
                    ui.card_header("Algorithm Controls"),
                    ui.output_ui("progress_bar"),
                    ui.br(),
                    ui.output_ui("explain"),
                    ui.output_ui("render_solution_quiz_ui")
                )
            ),
            ui.column(
                8,
                ui.card(
                    ui.card_header("Graph Visualization"),
                    cytoscape_graph(
                        graph_id="cytoscape_dijkstra_graph",
                        height="600px",
                        width="100%"
                    ),
                    ui.output_ui("cytoscape_update_script"),
                    ui.br(),
                    ui.h5("Visited Nodes:"),
                    ui.output_ui("visited_nodes"),
                    ui.br(),
                    ui.output_data_frame("display_distances")
                )
            )
        )
    )


def cytoscape_graph_ui_server(input, output, session):
    """Server logic for Cytoscape graph UI."""
    # Initialize algorithm handler and renderer
    algorithm_handler = DijkstraStepHandler(state_manager)
    cytoscape_renderer = CytoscapeRenderer("cytoscape_dijkstra_graph")
    
    @output
    @render.ui
    def render_solution_quiz_ui():
        if state_manager.step_counter.get() == STEP_FINISH:
            return render_solution_quiz()

    @output
    @render.ui
    def progress_bar():
        return create_progress_bar(state_manager.step_counter.get())

    @output
    @render.ui  
    def explain():
        return create_explanation_ui(
            state_manager.step_counter.get(),
            state_manager.step_explanation.get()
        )

    @output
    @render.ui
    @reactive.event(state_manager.nodes_visited)
    def visited_nodes():
        nodes = ", ".join(
            [str(int(node)) for node in state_manager.nodes_visited.get()]
        ) if state_manager.nodes_visited.get() else "No nodes visited yet"
        return TagList(nodes)

    @reactive.Effect
    @reactive.event(input.prev_step)
    def prev_step():
        state_manager.restore_state()

    @reactive.Effect
    @reactive.event(input.next_step)
    def next_step():
        algorithm_handler.handle_next_step(input)

    @reactive.Effect
    def update_graph():
        _update_graph_based_on_selection(input)

    @output
    @render.data_frame
    @reactive.event(
        state_manager.distances_df, state_manager.step_counter,
        input.start_node, input.target_node
    )
    def display_distances():
        start = input.start_node()
        target = input.target_node()
        
        # Only render if both nodes are selected and valid
        if not start or not target:
            return render.DataTable(pd.DataFrame({"Info": ["Please select start and target nodes"]}), width="100%")
            
        return render_distances_table(
            state_manager.distances_df.get(),
            start,
            target
        )

    @reactive.Effect
    @reactive.event(input.target_node, input.start_node)
    def reset_dijkstra():
        state_manager.reset_algorithm_state()

    @reactive.Effect
    def initialize_distances():
        state_manager.reset_algorithm_state()

    @output
    @render.ui
    def graph_generator_settings():
        return render_graph_generator_settings(input.selectize_graph())

    @output
    @render.ui
    def start_node_error_message():
        return render_error_tooltip(state_manager.start_node_error.get())

    @output
    @render.ui
    def target_node_error_message():
        return render_error_tooltip(state_manager.target_node_error.get())

    @output
    @render.ui
    def edge_list_error_message():
        return render_error_tooltip(state_manager.invalid_edge_list.get())

    # Update the Cytoscape graph data
    @reactive.Effect
    @reactive.event(
        state_manager.graph, input.layout_seed, input.start_node, input.target_node,
        state_manager.current_node, state_manager.current_edges, state_manager.nodes_visited,
        state_manager.step_counter, ignore_none=False
    )
    def update_cytoscape_graph():
        G = state_manager.graph.get()
        if G is None or len(G.nodes()) == 0:
            return
        
        # Update node choices for start/target selectors
        node_choices = [str(node) for node in sorted(G.nodes())]
        ui.update_selectize("start_node", choices=node_choices, session=session)
        ui.update_selectize("target_node", choices=node_choices, session=session)
        
        # Generate layout positions
        try:
            pos = nx.spring_layout(G, seed=input.layout_seed(), k=1, iterations=50)
        except:
            pos = nx.spring_layout(G, seed=42, k=1, iterations=50)
        
        # Update renderer
        cytoscape_renderer.update_graph(G, pos)
        cytoscape_renderer.set_start_node(input.start_node())
        cytoscape_renderer.set_target_node(input.target_node())
        cytoscape_renderer.set_visited_nodes(state_manager.nodes_visited.get())
        cytoscape_renderer.set_current_node(state_manager.current_node.get())
        cytoscape_renderer.set_current_edges(state_manager.current_edges.get())
        
        # Set shortest path if algorithm is finished
        if state_manager.step_counter.get() == STEP_FINISH:
            if input.start_node() and input.target_node() and G:
                try:
                    path = nx.shortest_path(G, source=input.start_node(), target=input.target_node(), weight='weight')
                    cytoscape_renderer.set_shortest_path(path)
                except:
                    cytoscape_renderer.set_shortest_path([])
    
    # Cytoscape graph update script
    @output  
    @render.ui
    def cytoscape_update_script():
        import json
        render_data = cytoscape_renderer.render_data()
        
        # Return JavaScript that will update the Cytoscape component
        return ui.tags.script(f"""
        setTimeout(function() {{
            if (window.updateCytoscapeGraph) {{
                window.updateCytoscapeGraph('cytoscape_dijkstra_graph', {json.dumps(render_data)});
            }} else {{
                console.error('updateCytoscapeGraph function not found');
            }}
        }}, 500);
        """, type="text/javascript")

    @reactive.Effect
    @reactive.event(input.submit_solution)
    def check_user_solution():
        algorithm_handler.check_user_solution(input)

    # Handle node clicks from Cytoscape
    @reactive.Effect
    @reactive.event(input.cytoscape_dijkstra_graph_node_clicked)
    def handle_node_click():
        node_data = input.cytoscape_dijkstra_graph_node_clicked()
        if node_data:
            node_id = node_data['id']
            # You can add custom logic here for node interactions
            print(f"Node clicked: {node_id}")

    # Handle edge clicks from Cytoscape  
    @reactive.Effect
    @reactive.event(input.cytoscape_dijkstra_graph_edge_clicked)
    def handle_edge_click():
        edge_data = input.cytoscape_dijkstra_graph_edge_clicked()
        if edge_data:
            edge_id = edge_data['id']
            # You can add custom logic here for edge interactions
            print(f"Edge clicked: {edge_id}")

    @reactive.calc
    def parsed_edge_list():
        file: list[FileInfo] | None = input.edge_list_file()
        if file is None:
            return None
        return file[0]["datapath"]

    @reactive.Effect
    def use_parsed_edge_list():
        edge_list = parsed_edge_list()
        if edge_list is not None:
            try:
                with open(DEFAULT_EDGE_LIST_PATH, 'r') as file:
                    edge_list_str = file.read()
                result = generate_from_edge_list(edge_list_str)
                if isinstance(result, str):
                    state_manager.invalid_edge_list.set(True)
                    state_manager.step_explanation.set(TagList(result))
                else:
                    state_manager.invalid_edge_list.set(False)
                    state_manager.graph.set(result)
            except FileNotFoundError:
                state_manager.invalid_edge_list.set(True)
                state_manager.step_explanation.set(
                    TagList(f"Edge list file not found: {DEFAULT_EDGE_LIST_PATH}")
                )

    # Initialize tutorial modal server
    tutorial_modal_server(input, output, session)


def _update_graph_based_on_selection(input):
    """Update graph based on user selection."""
    if input.selectize_graph() == GraphType.RANDOM_GRAPH.value:
        if input.k_slider() > input.n_slider():
            state_manager.step_explanation.set(
                TagList("Please select make sure that k is not smaller than n")
            )
        else:
            graph = generate_random_graph(
                input.n_slider(), input.k_slider(), input.p_slider()
            )
            state_manager.graph.set(graph)
    elif input.selectize_graph() == GraphType.KOOT_EXAMPLE_DEUTSCHLAND.value:
        state_manager.graph.set(generate_koot_example())
    elif input.selectize_graph() == GraphType.EDGE_LIST.value:
        edge_list_input = input.edge_list_input()
        if isinstance(edge_list_input, str):
            result = generate_from_edge_list(input.edge_list_input())
            if isinstance(result, str):
                state_manager.invalid_edge_list.set(True)
                state_manager.step_explanation.set(TagList(result))
            else:
                state_manager.invalid_edge_list.set(False)
                state_manager.graph.set(result)
        else:
            state_manager.graph.set(edge_list_input)