/**
 * Job Trends Analyzer - Maps JavaScript for Heatmaps 
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the heatmaps page
    const indiaMapContainer = document.getElementById('india-map');
    const worldMapContainer = document.getElementById('world-map');
    
    // If no map containers, exit early
    if (!indiaMapContainer && !worldMapContainer) return;
    
    // Handle India Map
    if (indiaMapContainer) {
        // The actual map is injected by Flask using Folium
        // This code adds event listener for the map tab to ensure proper rendering
        const indiaMapTab = document.getElementById('india-map-tab');
        if (indiaMapTab) {
            indiaMapTab.addEventListener('shown.bs.tab', function(e) {
                // Force redraw of map when tab becomes visible
                const mapFrames = indiaMapContainer.querySelectorAll('iframe');
                if (mapFrames.length > 0) {
                    mapFrames.forEach(frame => {
                        // Trigger resize to properly display the map
                        frame.style.height = '500px';
                        frame.style.width = '100%';
                    });
                } else {
                    // If no iframe found, show error message
                    indiaMapContainer.innerHTML = `
                        <div class="alert alert-warning">
                            <i class="fas fa-exclamation-triangle"></i> 
                            No map data available. Please try scraping Internshala jobs first.
                        </div>
                    `;
                }
            });
        }
    }
    
    // Handle World Map
    if (worldMapContainer) {
        // The actual map is injected by Flask using Folium
        // This code adds event listener for the map tab to ensure proper rendering
        const worldMapTab = document.getElementById('world-map-tab');
        if (worldMapTab) {
            worldMapTab.addEventListener('shown.bs.tab', function(e) {
                // Force redraw of map when tab becomes visible
                const mapFrames = worldMapContainer.querySelectorAll('iframe');
                if (mapFrames.length > 0) {
                    mapFrames.forEach(frame => {
                        // Trigger resize to properly display the map
                        frame.style.height = '500px';
                        frame.style.width = '100%';
                    });
                } else {
                    // If no iframe found, show error message
                    worldMapContainer.innerHTML = `
                        <div class="alert alert-warning">
                            <i class="fas fa-exclamation-triangle"></i> 
                            No map data available. Please try fetching Remotive jobs first.
                        </div>
                    `;
                }
            });
        }
    }
    
    // Add info cards about map data
    const mapInfoSection = document.getElementById('map-info');
    if (mapInfoSection) {
        mapInfoSection.innerHTML = `
            <div class="row mt-4">
                <div class="col-md-6">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5 class="card-title mb-0">India Job Distribution</h5>
                        </div>
                        <div class="card-body">
                            <p class="mb-0">This heatmap shows the distribution of jobs from Internshala across different cities in India. 
                            Larger and brighter spots indicate more job opportunities in those locations.</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5 class="card-title mb-0">Global Remote Job Distribution</h5>
                        </div>
                        <div class="card-body">
                            <p class="mb-0">This heatmap visualizes the global distribution of remote jobs from the Remotive API. 
                            It highlights regions with high concentrations of remote work opportunities.</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
});
