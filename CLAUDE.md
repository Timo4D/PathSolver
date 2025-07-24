# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PathSolver is a Python Shiny web application that visualizes the Dijkstra shortest path algorithm. The application allows users to interact with graph data structures and step through the algorithm execution with visual feedback.

## Development Commands

### Setup and Installation
```bash
pip install --upgrade pip wheel shiny htmltools shinyswatch
pip install -r requirements.txt
```

### Running the Application
```bash
# Run with auto-reload and browser launch
shiny run --reload --launch-browser app.py

# Alternative entry point
python run.py
```

## Architecture Overview

### Core Application Structure
- **app.py**: Main application entry point with Shiny UI layout and server setup
- **constants.py**: Application-wide constants and configuration
- **modules/**: Core application modules organized by functionality
- **utils/**: Utility functions for graph operations and data processing

### Key Architectural Components

**State Management (`modules/state_manager.py`)**
- Centralized reactive state management using Shiny's reactive system
- Manages graph data, algorithm progress, UI state, and step-by-step execution
- All state changes flow through the StateManager singleton instance

**UI Architecture (`modules/graph_ui.py`)**
- Modular UI components with clear separation between UI definition and server logic
- `graph_ui()` provides the UI layout, `graph_ui_server()` handles all server-side logic
- Reactive rendering patterns for dynamic content updates

**Algorithm Logic (`modules/algorithm_logic.py`)**
- `DijkstraStepHandler` class manages step-by-step algorithm execution
- Integrates with StateManager for progress tracking and visualization updates

**Graph Operations (`utils/`)**
- `graph_generators.py`: Functions for creating different types of graphs (random, examples, from edge lists)
- `graph_utils.py`: Core graph manipulation and plotting utilities using NetworkX and Matplotlib

### Data Flow
1. User interactions trigger reactive updates in StateManager
2. Algorithm logic processes steps and updates state
3. UI components reactively render based on state changes
4. Graph visualizations update through matplotlib integration

### Key Dependencies
- **Shiny**: Web framework for Python with reactive programming model
- **NetworkX**: Graph data structure and algorithms library
- **Matplotlib**: Graph visualization and plotting
- **Pandas**: Data manipulation for algorithm results tables
- **HTMLtools**: HTML generation utilities for Shiny

## Development Notes

### Module Organization
The codebase follows a modular structure where each module has a specific responsibility:
- UI components are separated from business logic
- State management is centralized but accessed through reactive patterns
- Algorithm implementation is isolated from presentation concerns

### Working with Graph Data
Graph data is managed through NetworkX Graph objects stored in reactive state. When modifying graph operations, ensure compatibility with the existing NetworkX-based graph utilities in `utils/graph_utils.py`.

### Adding New Features
When extending the application:
1. Add new reactive state variables to StateManager if needed
2. Create UI components in appropriate modules
3. Implement server logic following the existing reactive patterns
4. Update the main graph_ui_server function to wire new components