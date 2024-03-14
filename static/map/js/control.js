
let geojsonData = null;

fetch(`${staticBaseUrl}layers/vatsim_atc.geojson`) // Adjust path as needed
    .then(response => response.json())
    .then(data => {
        geojsonData = data; // Store the geojson data for later use
        // Optionally, initialize the map with some data or wait for controller selection
    })
    .catch(error => console.error('Error loading ATC GeoJSON:', error));

let activeControllers = []; // To track currently active controllers

function fetchControllerData() {
    fetch('/map/api/controllers/')
        .then(response => response.json())
        .then(data => {
            const controllers = data.controllers;
            // Filter controllers by type "CTR" before matching IDs for GeoJSON filtering
            const ctrControllers = controllers.filter(controller => 
                controller.type === "CTR" || controller.type === "FSS");

            // Update the map with filtered data
            const filteredFeatures = geojsonData.features.filter(feature =>
                ctrControllers.some(controller => controller.geoname === feature.properties.id));
            console.log(filteredFeatures);
            updateMapWithFilteredData(filteredFeatures);

            // Update active controllers list for next update cycle
            updateActiveControllersList(ctrControllers);
        })
        .catch(err => console.error('Error fetching ATC controller data:', err));
}

function updateActiveControllersList(newControllers) {
    const newActiveControllers = newControllers.map(controller => controller.geoname);

    // Find controllers that went offline
    const offlineControllers = activeControllers.filter(id => !newActiveControllers.includes(id));

    // Remove layers for offline controllers
    offlineControllers.forEach(controllerId => {
        if (map.getLayer(controllerId)) {
            map.removeLayer(controllerId);
            map.removeSource(controllerId);
        }
    });

    // Update the activeControllers list
    activeControllers = newActiveControllers;
}

function updateMapWithFilteredData(filteredFeatures) {
    // Assume all features are from new or existing controllers
    filteredFeatures.forEach(feature => {
        const featureId = feature.properties.id;
        const featureSourceId = featureId + '-source'; // Unique ID for the source
        const featureFillLayerId = featureId + '-fill'; // Unique ID for the fill layer
        const featureLineLayerId = featureId + '-line'; // Unique ID for the line (outline) layer

        // Check if the source exists, update it; otherwise, add a new source
        if (map.getSource(featureSourceId)) {
            map.getSource(featureSourceId).setData(feature);
        } else {
            map.addSource(featureSourceId, {
                type: 'geojson',
                data: feature,
            });
        }

        // Check if the fill layer exists; if not, add it
        if (!map.getLayer(featureFillLayerId)) {
            map.addLayer({
                id: featureFillLayerId,
                type: 'fill',
                source: featureSourceId,
                layout: {},
                paint: {
                    'fill-color': '#088',
                    'fill-opacity': 0.3,
                },
            });
        }

        // Check if the line (outline) layer exists; if not, add it
        if (!map.getLayer(featureLineLayerId)) {
            map.addLayer({
                id: featureLineLayerId,
                type: 'line',
                source: featureSourceId,
                layout: {},
                paint: {
                    'line-color': '#FFF', // Outline color
                    'line-width': 1, // Adjust for desired thickness
                },
            });
        }
    });
}   

// Initial fetch and map setup
map.on('load', function() {
    fetchControllerData(); // Call this function to fetch controllers and update the map

    // Set an interval for auto-updating controller data
    setInterval(fetchControllerData, 10000); // Update every 10 seconds
});
