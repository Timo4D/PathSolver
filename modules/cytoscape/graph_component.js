// Cytoscape.js and cxtmenu extension are loaded via HTML dependencies

if (Shiny) {
  class CytoscapeOutputBinding extends Shiny.OutputBinding {
    find(scope) {
      return scope.find(".shiny-cytoscape-output");
    }

    renderValue(el, payload) {
      //Wait for cytroscape to load if it hasnt already
      if (typeof cytoscape === "undefined") {
        setTimeout(() => this.renderValue(el, payload), 100);
        return;
      }

      const { elements, style, layout } = payload;

      if (el._cytoscape) {
        // Check if the graph structure has changed (different nodes/edges)
        const currentNodeIds = new Set(el._cytoscape.nodes().map(node => node.id()));
        const newNodeIds = new Set(elements.filter(el => el.data && !el.data.source).map(el => el.data.id));
        
        const currentEdgeIds = new Set(el._cytoscape.edges().map(edge => edge.id()));
        const newEdgeIds = new Set(elements.filter(el => el.data && el.data.source).map(el => el.data.id));
        
        // Check if node count changed or node IDs are different
        const nodeStructureChanged = currentNodeIds.size !== newNodeIds.size || 
          ![...currentNodeIds].every(id => newNodeIds.has(id)) ||
          ![...newNodeIds].every(id => currentNodeIds.has(id));
        
        // Check if edge structure changed
        const edgeStructureChanged = currentEdgeIds.size !== newEdgeIds.size ||
          ![...currentEdgeIds].every(id => newEdgeIds.has(id)) ||
          ![...newEdgeIds].every(id => currentEdgeIds.has(id));

        if (nodeStructureChanged || edgeStructureChanged) {
          // Save current positions before structure change
          const currentPositions = {};
          el._cytoscape.nodes().forEach(node => {
            currentPositions[node.id()] = node.position();
          });
          
          // Update graph structure
          el._cytoscape.elements().remove();
          el._cytoscape.add(elements);
          el._cytoscape.style(style || [
            {
              selector: "node",
              style: {
                "background-color": "#4CAF50",
                color: "white",
                width: 80,
                height: 80
              },
            },
          ]);
          
          // Check if this might be a user edit (only preserve layout if reasonable)
          const isLikelyUserEdit = Math.abs(currentNodeIds.size - newNodeIds.size) <= 1;
          
          if (isLikelyUserEdit) {
            // Preserve positions for remaining nodes when user edits via context menu
            el._cytoscape.nodes().forEach(node => {
              const nodeId = node.id();
              if (currentPositions[nodeId]) {
                node.position(currentPositions[nodeId]);
              }
            });
            
            // Only run layout if no positions were preserved and no nodes have preset positions
            const nodesWithPositions = el._cytoscape.nodes().filter(node => 
              currentPositions[node.id()]
            );
            const nodesWithPresetPositions = el._cytoscape.nodes().filter(node => 
              node.position().x !== 0 || node.position().y !== 0
            );
            if (nodesWithPositions.length === 0 && nodesWithPresetPositions.length === 0) {
              el._cytoscape.layout(layout || { name: "cose" }).run();
            }
          } else {
            // Run layout for major graph structure changes
            el._cytoscape.layout(layout || { name: "cose" }).run();
          }
        } else {
          // Only styling changed - preserve positions
          const currentPositions = {};
          el._cytoscape.nodes().forEach(node => {
            currentPositions[node.id()] = node.position();
          });

          el._cytoscape.elements().remove();
          el._cytoscape.add(elements);
          el._cytoscape.style(style || [
            {
              selector: "node",
              style: {
                "background-color": "#4CAF50",
                color: "white",
                width: 80,
                height: 80
              },
            },
          ]);

          // Restore positions for existing nodes
          el._cytoscape.nodes().forEach(node => {
            const nodeId = node.id();
            if (currentPositions[nodeId]) {
              node.position(currentPositions[nodeId]);
            }
          });
        }

      } else {
        // Create new instance
        el._cytoscape = cytoscape({
          container: el,
          elements: elements,
          style: style || [
            {
              selector: "node",
              style: {
                "background-color": "#4CAF50",
                color: "white",
                width: 80,
                height: 80
              },
            },
          ],
          layout: { name: "null" }, // Start with no layout
          autoungrabify: false,
          userPanningEnabled: true,
          userZoomingEnabled: true,
          boxSelectionEnabled: false
        });

        const outputId = el.id;

        el._cytoscape.on("tap", "node", function (evt) {
          const node = evt.target;
          Shiny.setInputValue(`${outputId}_node_clicked`, {
            id: node.id(),
            label: node.data("label"),
            timestamp: Date.now()
          });
        });

        // Store edge creation state
        let edgeCreationMode = false;
        let edgeSourceNode = null;

        // Initialize cxtmenu extension for nodes
        el._cytoscape.cxtmenu({
          selector: 'node',
          commands: [
            {
              content: '🎯 Start',
              contentStyle: {},
              select: function(ele) {
                Shiny.setInputValue(`${outputId}_set_start_node`, {
                  id: ele.id(),
                  timestamp: Date.now()
                });
              }
            },
            {
              content: '🏁 Target',
              contentStyle: {},
              select: function(ele) {
                Shiny.setInputValue(`${outputId}_set_target_node`, {
                  id: ele.id(),
                  timestamp: Date.now()
                });
              }
            },
            {
              content: '🔗 Connect to...',
              contentStyle: {},
              select: function(ele) {
                if (!edgeCreationMode) {
                  // Start edge creation mode
                  edgeCreationMode = true;
                  edgeSourceNode = ele.id();
                  console.log('Edge creation mode started. Source node:', edgeSourceNode);
                  
                  // Visual feedback - highlight the source node
                  el._cytoscape.nodes().removeClass('edge-source');
                  ele.addClass('edge-source');
                  
                  // Show instruction
                  Shiny.setInputValue(`${outputId}_edge_creation_started`, {
                    source: edgeSourceNode,
                    timestamp: Date.now()
                  });
                } else {
                  // Complete edge creation
                  const targetNode = ele.id();
                  console.log('Completing edge creation. Target node:', targetNode);
                  
                  if (edgeSourceNode !== targetNode) {
                    Shiny.setInputValue(`${outputId}_create_edge`, {
                      source: edgeSourceNode,
                      target: targetNode,
                      timestamp: Date.now()
                    });
                  }
                  
                  // Reset edge creation mode
                  edgeCreationMode = false;
                  edgeSourceNode = null;
                  el._cytoscape.nodes().removeClass('edge-source');
                  
                  Shiny.setInputValue(`${outputId}_edge_creation_ended`, {
                    timestamp: Date.now()
                  });
                }
              }
            },
            {
              content: '🗑️ Delete',
              contentStyle: {},
              select: function(ele) {
                Shiny.setInputValue(`${outputId}_delete_node`, {
                  id: ele.id(),
                  timestamp: Date.now()
                });
              }
            }
          ],
          fillColor: 'rgba(0, 0, 0, 0.75)',
          activeFillColor: 'rgba(1, 105, 217, 0.75)',
          activePadding: 20,
          indicatorSize: 24,
          separatorWidth: 3,
          spotlightPadding: 4,
          minSpotlightRadius: 24,
          maxSpotlightRadius: 38,
          itemColor: 'white',
          itemTextShadowColor: 'transparent',
          zIndex: 9999,
          atMouse: false
        });

        // Initialize cxtmenu extension for edges
        el._cytoscape.cxtmenu({
          selector: 'edge',
          commands: [
            {
              content: '⚖️ Edit Weight',
              contentStyle: {},
              select: function(ele) {
                const currentWeight = ele.data('weight') || 1;
                const newWeight = prompt(`Enter new weight for edge ${ele.source().id()}-${ele.target().id()}:`, currentWeight);
                
                if (newWeight !== null && newWeight !== '') {
                  const weightValue = parseFloat(newWeight);
                  
                  if (!isNaN(weightValue) && weightValue > 0) {
                    console.log('Updating edge weight:', ele.id(), 'to', weightValue);
                    
                    Shiny.setInputValue(`${outputId}_update_edge_weight`, {
                      id: ele.id(),
                      source: ele.source().id(),
                      target: ele.target().id(),
                      weight: weightValue,
                      timestamp: Date.now()
                    });
                  } else {
                    alert('Please enter a positive number for the weight.');
                  }
                }
              }
            },
            {
              content: '🗑️ Delete Edge',
              contentStyle: {},
              select: function(ele) {
                Shiny.setInputValue(`${outputId}_delete_edge`, {
                  id: ele.id(),
                  source: ele.source().id(),
                  target: ele.target().id(),
                  timestamp: Date.now()
                });
              }
            }
          ],
          fillColor: 'rgba(0, 0, 0, 0.75)',
          activeFillColor: 'rgba(217, 105, 1, 0.75)',
          activePadding: 20,
          indicatorSize: 24,
          separatorWidth: 3,
          spotlightPadding: 4,
          minSpotlightRadius: 24,
          maxSpotlightRadius: 38,
          itemColor: 'white',
          itemTextShadowColor: 'transparent',
          zIndex: 9999,
          atMouse: false
        });

        // Store mouse position globally
        let lastMousePosition = { x: 100, y: 100 };
        
        // Track mouse position over the cytoscape container
        el.addEventListener('mousemove', function(event) {
          const rect = el.getBoundingClientRect();
          const cy = el._cytoscape;
          if (cy) {
            // Convert screen coordinates to cytoscape model coordinates
            const screenX = event.clientX - rect.left;
            const screenY = event.clientY - rect.top;
            
            // Get the rendered position (screen coordinates) and convert to model coordinates
            const renderedPosition = {
              x: screenX,
              y: screenY
            };
            
            // Convert rendered position to model position using Cytoscape's built-in method
            const modelPosition = {
              x: (renderedPosition.x - cy.pan().x) / cy.zoom(),
              y: (renderedPosition.y - cy.pan().y) / cy.zoom()
            };
            
            lastMousePosition = modelPosition;
          }
        });

        // Initialize cxtmenu extension for background (empty space)
        el._cytoscape.cxtmenu({
          selector: 'core',
          commands: [
            {
              content: '➕ Add Node',
              contentStyle: {},
              select: function(ele) {
                console.log('Add node clicked! Using stored mouse position:', lastMousePosition);
                
                Shiny.setInputValue(`${outputId}_add_node`, {
                  x: lastMousePosition.x,
                  y: lastMousePosition.y,
                  timestamp: Date.now()
                });
              }
            }
          ],
          fillColor: 'rgba(0, 0, 0, 0.75)',
          activeFillColor: 'rgba(34, 139, 34, 0.75)',
          activePadding: 20,
          indicatorSize: 24,
          separatorWidth: 3,
          spotlightPadding: 4,
          minSpotlightRadius: 24,
          maxSpotlightRadius: 38,
          itemColor: 'white',
          itemTextShadowColor: 'transparent',
          zIndex: 9999,
          atMouse: false
        });

        // Run the initial layout only once
        el._cytoscape.layout(layout || { name: "cose" }).run();
        
        // Set up resize functionality with a small delay to ensure DOM is ready
        setTimeout(() => {
          this.setupResizeHandlers(el);
        }, 100);
      }
      
      // Always try to set up resize handlers, regardless of new or existing instance
      setTimeout(() => {
        this.setupResizeHandlers(el);
      }, 200);
    }
    
    setupResizeHandlers(el) {
      const container = el.closest('.resizable-cytoscape-container');
      if (!container) {
        return;
      }
      
      const bottomHandle = container.querySelector('.resize-handle.bottom');
      if (!bottomHandle) {
        return;
      }
      
      // Prevent duplicate event listeners
      if (bottomHandle._resizeSetup) {
        return;
      }
      bottomHandle._resizeSetup = true;
      
      let isResizing = false;
      let startY, startHeight;
      let resizeThrottle = null;
      
      const startResize = (e) => {
        isResizing = true;
        startY = e.clientY;
        startHeight = parseInt(window.getComputedStyle(container).height, 10);
        
        document.body.style.cursor = 's-resize';
        document.body.style.userSelect = 'none';
        
        e.preventDefault();
        e.stopPropagation();
      };
      
      const doResize = (e) => {
        if (!isResizing) return;
        
        const dy = e.clientY - startY;
        const newHeight = Math.max(300, Math.min(startHeight + dy, 800));
        
        container.style.height = newHeight + 'px';
        
        // Throttle cytoscape resize calls to reduce flashing
        if (resizeThrottle) {
          cancelAnimationFrame(resizeThrottle);
        }
        
        resizeThrottle = requestAnimationFrame(() => {
          if (el._cytoscape) {
            el.style.width = '100%';
            el.style.height = '100%';
            el._cytoscape.resize();
          }
        });
        
        e.preventDefault();
      };
      
      const stopResize = (e) => {
        if (!isResizing) return;
        
        isResizing = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        
        // Final resize call to ensure proper sizing
        if (el._cytoscape) {
          setTimeout(() => {
            el._cytoscape.resize();
          }, 50);
        }
      };
      
      // Attach event listener for bottom resize handle only
      bottomHandle.addEventListener('mousedown', startResize);
      
      // Global mouse events for dragging
      document.addEventListener('mousemove', (e) => {
        if (isResizing) {
          doResize(e);
        }
      });
      
      document.addEventListener('mouseup', (e) => {
        if (isResizing) {
          stopResize(e);
        }
      });
      
      // Handle CSS resize property (browser native resize)
      if (window.ResizeObserver) {
        const resizeObserver = new ResizeObserver((entries) => {
          for (let entry of entries) {
            if (entry.target === container && el._cytoscape) {
              // Force the cytoscape element to take full container size
              el.style.width = '100%';
              el.style.height = '100%';
              
              requestAnimationFrame(() => {
                el._cytoscape.resize();
              });
            }
          }
        });
        
        resizeObserver.observe(container);
      }
    }
  }

  Shiny.outputBindings.register(
    new CytoscapeOutputBinding(),
    "shiny-cytoscape-output",
  );
}
