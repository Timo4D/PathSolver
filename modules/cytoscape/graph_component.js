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
                width: 60,
                height: 60
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
            
            // Only run layout if no positions were preserved
            const nodesWithPositions = el._cytoscape.nodes().filter(node => 
              currentPositions[node.id()]
            );
            if (nodesWithPositions.length === 0) {
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
                width: 60,
                height: 60
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
                width: 60,
                height: 60
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
          });
        });

        // Initialize cxtmenu extension
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

        // Run the initial layout only once
        el._cytoscape.layout(layout || { name: "cose" }).run();
      }
    }
  }

  Shiny.outputBindings.register(
    new CytoscapeOutputBinding(),
    "shiny-cytoscape-output",
  );
}
