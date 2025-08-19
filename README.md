# PathSolver

An interactive web application built with Python Shiny that visualizes the Dijkstra shortest path algorithm. Users can interact with graph data structures and step through the algorithm execution with real-time visual feedback.

## Features

- **Interactive Graph Visualization**: Built with Cytoscape.js for dynamic graph manipulation
- **Step-by-Step Algorithm Execution**: Watch Dijkstra's algorithm progress with visual updates
- **Multiple Graph Types**: Random graphs, predefined examples, and custom edge lists
- **Prediction Game**: Test your understanding by predicting algorithm outcomes
- **Solution Quiz**: Interactive quiz after algorithm completion
- **Tutorial System**: Guided walkthrough for new users
- **Internationalization**: Support for multiple languages (English, German)
- **Admin Settings**: Password-protected configuration panel
- **Responsive Design**: Works across different screen sizes

## Installation

### Prerequisites
- Python 3.11 or higher 
- pip package manager

### Setup
```bash
git clone https://github.com/Timo4D/PathSolver
cd pathsolver
pip install -r requirements.txt
```

## Usage

### Running the Application
```bash
# Run with auto-reload and browser launch
shiny run --reload app.py
```

## Architecture

### Core Components

- **app.py**: Main application entry point with Shiny UI layout
- **modules/**: Feature modules organized by functionality
  - `state_manager.py`: Centralized reactive state management
  - `graph_ui.py`: Main UI components and server logic
  - `algorithm_logic.py`: Dijkstra algorithm implementation
  - `cytoscape/`: Interactive graph visualization components
- **utils/**: Graph operations and utility functions
- **localization/**: Internationalization system with translation files
- **config.json**: Runtime configuration for features and settings

### Key Technologies

- **Shiny for Python**: Reactive web framework
- **NetworkX**: Graph data structures and algorithms
- **Cytoscape.js**: Interactive graph visualization
- **Matplotlib**: Graph plotting utilities
- **Pandas**: Data manipulation for results tables

## Configuration

The application is configurable through `config.json`:

```json
{
  "settings": {
    "game_feature_enabled": true,
    "visualization_mode": "cytoscape",
    "solution_quiz_enabled": true,
    "admin_password": "admin123"
  }
}
```

### Configuration Options

- `game_feature_enabled`: Enable/disable prediction game
- `visualization_mode`: Graph visualization engine ("cytoscape" or "matplotlib")
- `solution_quiz_enabled`: Enable/disable post-algorithm quiz
- `password_protected`: Require password for admin settings
- `admin_password`: Password for accessing admin panel

## Internationalization

The application supports multiple languages. To add a new language:

1. Create a new translation file in `localization/translations/`
2. Follow the existing JSON structure from `en.json`
3. Update the language selector in the UI

Current supported languages:
- English (`en.json`)
- German (`de.json`)

## Development

### Project Structure
```
pathsolver/
├── app.py                 # Main application
├── config.json           # Configuration
├── modules/              # Feature modules
│   ├── state_manager.py  # State management
│   ├── graph_ui.py       # Main UI
│   ├── cytoscape/        # Graph visualization
│   └── ...
├── utils/                # Utilities
├── localization/         # i18n support
└── requirements.txt      # Dependencies
```

### Adding New Features

1. Add reactive state variables to StateManager if needed
2. Create UI components following existing patterns
3. Implement server logic using reactive patterns
4. Update configuration in `config.json` for runtime control
5. Internationalize user-facing text

### Code Style

- Follow standard Python conventions
- Use reactive programming patterns with Shiny
- Separate UI components from business logic
- Ensure NetworkX and Cytoscape.js compatibility

## License

See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly through browser interaction
5. Submit a pull request
