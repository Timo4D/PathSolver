// Folium map component for Shiny
// Folium generates its own HTML with embedded JavaScript, so this is minimal

if (Shiny) {
  class FoliumOutputBinding extends Shiny.OutputBinding {
    find(scope) {
      return scope.find(".shiny-folium-output");
    }

    renderValue(el, html) {
      // Clear previous content
      el.innerHTML = '';
      
      // Insert Folium HTML directly
      if (html && typeof html === 'string') {
        el.innerHTML = html;
        
        // Ensure all child elements are properly contained
        const mapElements = el.querySelectorAll('*');
        mapElements.forEach(element => {
          // Reset any absolute positioning that might escape the container
          if (element.style.position === 'fixed') {
            element.style.position = 'absolute';
          }
          // Ensure elements don't overflow the container
          if (element.style.zIndex && parseInt(element.style.zIndex) > 2000) {
            element.style.zIndex = '1000';
          }
        });
        
        // Execute any embedded scripts in the Folium HTML
        const scripts = el.querySelectorAll('script');
        scripts.forEach(script => {
          if (script.innerHTML) {
            try {
              eval(script.innerHTML);
            } catch (e) {
              console.warn('Error executing Folium script:', e);
            }
          }
        });
      } else {
        el.innerHTML = '<p>No map data available</p>';
      }
    }
  }

  Shiny.outputBindings.register(
    new FoliumOutputBinding(),
    "shiny-folium-output"
  );
}