let geojsonData = null;

fetch(`${staticBaseUrl}layers/vatsim_atc.geojson`) // Adjust path as needed
    .then(response => response.json())
    .then(data => {
        geojsonData = data; // Store the geojson data for later use
        // Optionally, initialize the map with some data or wait for controller selection
    })
    .catch(error => console.error('Error loading ATC GeoJSON:', error));


function fetchControllerData() {
    fetch('/map/api/controllers/')
        .then(response => response.json())
        .then(data => {
            const controllers = data.controllers;
            // Filter controllers by type "CTR" before matching IDs for GeoJSON filtering
            const ctrControllers = controllers.filter(controller => controller.type === "CTR");

            const filteredFeatures = geojsonData.features.filter(feature =>
                ctrControllers.some(controller => controller.geoname === feature.properties.id)
            );

            updateMapWithFilteredData(filteredFeatures);
        })
        .catch(err => console.error('Error fetching ATC controller data:', err));
}

function updateMapWithFilteredData(filteredFeatures) {
    // Check if the source exists, update it; otherwise, add a new source and layer
    if (map.getSource('atc-boundaries')) {
        map.getSource('atc-boundaries').setData({
            type: 'FeatureCollection',
            features: filteredFeatures,
        });
    } else {
        map.addSource('atc-boundaries', {
            type: 'geojson',
            data: {
                type: 'FeatureCollection',
                features: filteredFeatures,
            },
        });

        map.addLayer({
            id: 'atc-boundaries',
            type: 'fill', // or 'line' depending on your preference
            source: 'atc-boundaries',
            layout: {},
            paint: {
                
                'fill-outline-color': '#FFF', // Customize the outline color
                'thickness': 0.5, // Customize the outline thickness
                'fill-color': '#088', // Customize the fill color
                'fill-opacity': 0.3, // Customize the fill opacity
            },
        });
    }
}

map.on('load', function() {
    fetchControllerData(); // Call this function to fetch controllers and update the map
});
