//import cytoscape.js
if (typeof cytoscape === "undefined") {
  // Load Cytoscape.js from CDN if not already loaded
  const script = document.createElement("script");
  script.src =
    "https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js";
  document.head.appendChild(script);
}

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
          // Graph structure changed - reset layout
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
          
          // Run layout for new graph structure
          el._cytoscape.layout(layout || { name: "cose" }).run();
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

        // Right-click context menu for nodes
        el._cytoscape.on("cxttap", "node", function (evt) {
          evt.preventDefault();
          const node = evt.target;
          const nodeId = node.id();
          const position = evt.renderedPosition;
          
          // Remove any existing context menu
          const existingMenu = document.getElementById('cytoscape-context-menu');
          if (existingMenu) {
            existingMenu.remove();
          }
          
          // Create context menu
          const contextMenu = document.createElement('div');
          contextMenu.id = 'cytoscape-context-menu';
          contextMenu.style.cssText = `
            position: absolute;
            left: ${position.x}px;
            top: ${position.y}px;
            background: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
            min-width: 150px;
          `;
          
          // Menu options
          const setStartOption = document.createElement('div');
          setStartOption.textContent = 'Set as Start Node';
          setStartOption.style.cssText = `
            padding: 10px 15px;
            cursor: pointer;
            border-bottom: 1px solid #eee;
          `;
          setStartOption.onmouseover = () => setStartOption.style.backgroundColor = '#f5f5f5';
          setStartOption.onmouseout = () => setStartOption.style.backgroundColor = 'white';
          setStartOption.onclick = () => {
            Shiny.setInputValue(`${outputId}_set_start_node`, {
              id: nodeId,
              timestamp: Date.now()
            });
            contextMenu.remove();
          };
          
          const setTargetOption = document.createElement('div');
          setTargetOption.textContent = 'Set as Target Node';
          setTargetOption.style.cssText = `
            padding: 10px 15px;
            cursor: pointer;
          `;
          setTargetOption.onmouseover = () => setTargetOption.style.backgroundColor = '#f5f5f5';
          setTargetOption.onmouseout = () => setTargetOption.style.backgroundColor = 'white';
          setTargetOption.onclick = () => {
            Shiny.setInputValue(`${outputId}_set_target_node`, {
              id: nodeId,
              timestamp: Date.now()
            });
            contextMenu.remove();
          };
          
          contextMenu.appendChild(setStartOption);
          contextMenu.appendChild(setTargetOption);
          document.body.appendChild(contextMenu);
          
          // Remove menu when clicking elsewhere
          const removeMenu = (e) => {
            if (!contextMenu.contains(e.target)) {
              contextMenu.remove();
              document.removeEventListener('click', removeMenu);
            }
          };
          setTimeout(() => document.addEventListener('click', removeMenu), 100);
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
