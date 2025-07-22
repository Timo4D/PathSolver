// Custom Cytoscape.js component for Shiny for Python
class CytoscapeGraph {
    constructor(elementId) {
        this.elementId = elementId;
        this.cy = null;
        this.layout = null;
    }

    initialize(container, options = {}) {
        // Default options
        const defaultOptions = {
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': '#666',
                        'label': 'data(id)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'color': '#fff',
                        'font-size': '14px',
                        'font-weight': 'bold',
                        'width': '30px',
                        'height': '30px'
                    }
                },
                {
                    selector: 'node.start',
                    style: {
                        'background-color': '#4CAF50'
                    }
                },
                {
                    selector: 'node.target',
                    style: {
                        'background-color': '#F44336'
                    }
                },
                {
                    selector: 'node.current',
                    style: {
                        'background-color': '#FF9800',
                        'border-width': '3px',
                        'border-color': '#E65100'
                    }
                },
                {
                    selector: 'node.visited',
                    style: {
                        'background-color': '#2196F3'
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 2,
                        'line-color': '#ccc',
                        'target-arrow-color': '#ccc',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'label': 'data(weight)',
                        'font-size': '12px',
                        'text-background-color': '#fff',
                        'text-background-opacity': 0.8,
                        'text-background-padding': '2px'
                    }
                },
                {
                    selector: 'edge.current',
                    style: {
                        'line-color': '#FF9800',
                        'target-arrow-color': '#FF9800',
                        'width': 4
                    }
                },
                {
                    selector: 'edge.shortest-path',
                    style: {
                        'line-color': '#4CAF50',
                        'target-arrow-color': '#4CAF50',
                        'width': 4
                    }
                }
            ],
            layout: {
                name: 'cose',
                idealEdgeLength: 100,
                nodeOverlap: 20,
                refresh: 20,
                fit: true,
                padding: 30,
                randomize: false,
                componentSpacing: 100,
                nodeRepulsion: 400000,
                edgeElasticity: 100,
                nestingFactor: 5,
                gravity: 80,
                numIter: 1000,
                initialTemp: 200,
                coolingFactor: 0.95,
                minTemp: 1.0
            }
        };

        // Merge user options with defaults
        const config = {
            container: container,
            elements: options.elements || [],
            style: options.style || defaultOptions.style,
            layout: options.layout || defaultOptions.layout,
            wheelSensitivity: 0.2,
            minZoom: 0.1,
            maxZoom: 3
        };

        this.cy = cytoscape(config);
        this.setupEventHandlers();
        
        return this.cy;
    }

    setupEventHandlers() {
        // Node click handler
        this.cy.on('tap', 'node', (event) => {
            const node = event.target;
            const nodeData = {
                id: node.id(),
                data: node.data()
            };
            
            // Trigger Shiny input update
            if (window.Shiny) {
                Shiny.setInputValue(`${this.elementId}_node_clicked`, nodeData, {priority: 'event'});
            }
        });

        // Edge click handler
        this.cy.on('tap', 'edge', (event) => {
            const edge = event.target;
            const edgeData = {
                id: edge.id(),
                source: edge.source().id(),
                target: edge.target().id(),
                data: edge.data()
            };
            
            if (window.Shiny) {
                Shiny.setInputValue(`${this.elementId}_edge_clicked`, edgeData, {priority: 'event'});
            }
        });
    }

    updateGraph(elements) {
        if (!this.cy) return;
        
        this.cy.elements().remove();
        this.cy.add(elements);
        this.cy.layout(this.cy.options().layout).run();
    }

    updateNodeClasses(nodeId, classes) {
        if (!this.cy) return;
        
        const node = this.cy.getElementById(nodeId);
        if (node.length > 0) {
            node.removeClass();
            node.addClass(classes);
        }
    }

    updateEdgeClasses(edgeId, classes) {
        if (!this.cy) return;
        
        const edge = this.cy.getElementById(edgeId);
        if (edge.length > 0) {
            edge.removeClass();
            edge.addClass(classes);
        }
    }

    highlightPath(path) {
        if (!this.cy || !path) return;
        
        // Reset all edges
        this.cy.edges().removeClass('shortest-path');
        
        // Highlight path edges
        for (let i = 0; i < path.length - 1; i++) {
            const edge = this.cy.edges(`[source="${path[i]}"][target="${path[i + 1]}"]`);
            if (edge.length > 0) {
                edge.addClass('shortest-path');
            }
        }
    }

    setCurrentNode(nodeId) {
        if (!this.cy) return;
        
        // Remove current class from all nodes
        this.cy.nodes().removeClass('current');
        
        // Add current class to specified node
        if (nodeId) {
            this.cy.getElementById(nodeId).addClass('current');
        }
    }

    setCurrentEdges(edgeIds) {
        if (!this.cy) return;
        
        // Remove current class from all edges
        this.cy.edges().removeClass('current');
        
        // Add current class to specified edges
        if (edgeIds && edgeIds.length > 0) {
            edgeIds.forEach(edgeId => {
                this.cy.getElementById(edgeId).addClass('current');
            });
        }
    }

    fit() {
        if (this.cy) {
            this.cy.fit();
        }
    }

    center() {
        if (this.cy) {
            this.cy.center();
        }
    }

    resize() {
        if (this.cy) {
            this.cy.resize();
        }
    }

    destroy() {
        if (this.cy) {
            this.cy.destroy();
            this.cy = null;
        }
    }
}

// Global function to create Cytoscape component
window.createCytoscapeGraph = function(elementId) {
    return new CytoscapeGraph(elementId);
};

// Initialize Cytoscape graphs on page load
$(document).ready(function() {
    // Initialize all cytoscape graph elements
    $('.cytoscape-graph').each(function() {
        var el = this;
        var $el = $(el);
        var elementId = $el.attr('id');
        
        if (!el.cytoscapeGraph) {
            el.cytoscapeGraph = new CytoscapeGraph(elementId);
            el.cytoscapeGraph.initialize(el);
            console.log('Initialized Cytoscape graph:', elementId);
        }
    });
});

// Global function to update cytoscape graph
window.updateCytoscapeGraph = function(elementId, data) {
    var el = document.getElementById(elementId);
    if (el && el.cytoscapeGraph) {
        var graph = el.cytoscapeGraph;
        
        // Update graph data
        if (data.elements) {
            graph.updateGraph(data.elements);
        }

        // Update node states
        if (data.startNode) {
            graph.cy.nodes().removeClass('start');
            graph.cy.getElementById(data.startNode).addClass('start');
        }

        if (data.targetNode) {
            graph.cy.nodes().removeClass('target');
            graph.cy.getElementById(data.targetNode).addClass('target');
        }

        if (data.visitedNodes) {
            graph.cy.nodes().removeClass('visited');
            data.visitedNodes.forEach(nodeId => {
                graph.cy.getElementById(nodeId).addClass('visited');
            });
        }

        if (data.currentNode) {
            graph.setCurrentNode(data.currentNode);
        }

        if (data.currentEdges) {
            graph.setCurrentEdges(data.currentEdges);
        }

        if (data.shortestPath) {
            graph.highlightPath(data.shortestPath);
        }

        // Fit graph to container
        if (data.fit !== false) {
            graph.fit();
        }
        
        console.log('Updated Cytoscape graph:', elementId, data);
    } else {
        console.error('Cytoscape graph not found:', elementId);
    }
};