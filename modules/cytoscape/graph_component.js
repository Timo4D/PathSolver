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
        el._cytoscape.destroy();
      }

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
        layout: layout || { name: "circle" },
      });

      const outputId = el.id;

      el._cytoscape.on("tap", "node", function (evt) {
        const node = evt.target;
        Shiny.setInputValue(`${outputId}_node_clicked`, {
          id: node.id(),
          label: node.data("label"),
        });
      });
    }
  }

  Shiny.outputBindings.register(
    new CytoscapeOutputBinding(),
    "shiny-cytoscape-output",
  );
}
