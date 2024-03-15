let geojsonData = null;

fetch(`${staticBaseUrl}layers/vatsim_atc.geojson`) // Adjust path as needed
    .then(response => response.json())
    .then(data => {
        geojsonData = data; // Store the geojson data for later use
    })
    .catch(error => console.error('Error loading ATC GeoJSON:', error));

let activeControllers = []; // To track currently active controllers

function fetchControllerData() {
    fetch('/map/api/controllers/')
        .then(response => response.json())
        .then(data => {
            const controllers = data.controllers;
            const ctrControllers = controllers.filter(controller =>
                controller.type === "CTR" || controller.type === "FSS");

            // Prepare to filter features within the current map view
            const viewportBounds = map.getBounds();

            // Filter and update based on viewport
            const filteredFeatures = geojsonData.features.filter(feature =>
                ctrControllers.some(controller => controller.geoname ? controller.geoname === feature.properties.id :
                    controller.ident === feature.properties.id));

            updateMapWithFilteredData(filteredFeatures, viewportBounds);
            updateActiveControllersList(ctrControllers);
        })
        .catch(err => console.error('Error fetching ATC controller data:', err));
}

function isFeatureInView(feature, bounds) {
    // Assuming the feature is a Polygon or MultiPolygon
    let coordinates = [];
    if (feature.geometry.type === 'Polygon') {
        coordinates = feature.geometry.coordinates;
    } else if (feature.geometry.type === 'MultiPolygon') {
        // Flatten MultiPolygon coordinates for simplicity; adjust based on your data structure
        coordinates = feature.geometry.coordinates.flat(1);
    } else {
        console.error('Unsupported feature type for viewport check');
        return false;
    }

    // Check if any point of the polygon(s) is within the map bounds
    return coordinates.some(polygon => 
        polygon.some(coord => {
            const lngLat = new mapboxgl.LngLat(coord[0], coord[1]);
            return bounds.contains(lngLat);
        })
    );
}

function updateActiveControllersList(newControllers) {
    const newActiveControllerIds = newControllers.map(controller => controller.geoname || controller.ident);
    activeControllers = newActiveControllerIds;
}

function updateMapWithFilteredData(filteredFeatures, viewportBounds) {
    filteredFeatures.forEach(feature => {
        const featureId = feature.properties.id;
        const isInView = isFeatureInView(feature, viewportBounds);
        const featureSourceId = featureId + '-source';
        const featureFillLayerId = featureId + '-fill';
        const featureLineLayerId = featureId + '-line';
        const featureTextLayerId = featureId + '-text';

        if (isInView) {
            // Add or update source and layers for features in view
            if (!map.getSource(featureSourceId)) {
                map.addSource(featureSourceId, { type: 'geojson', data: feature });
            } else {
                map.getSource(featureSourceId).setData(feature);
            }

            if (!map.getLayer(featureFillLayerId)) {
                map.addLayer({ id: featureFillLayerId, type: 'fill', source: featureSourceId, paint: { 'fill-color': '#088', 'fill-opacity': 0.3 } });
                map.addLayer({ id: featureLineLayerId, type: 'line', source: featureSourceId, paint: { 'line-color': '#FFF', 'line-width': 2 } });
                map.addLayer({ id: featureTextLayerId, type: 'symbol', source: featureSourceId, layout: { 'text-field': feature.properties.id + " Control", 'text-size': 12 }, paint: { 'text-color': '#FFF' }});
            }
        } else {
            // Remove features not in view
            if (map.getSource(featureSourceId)) {
                if (map.getLayer(featureFillLayerId)) map.removeLayer(featureFillLayerId);
                if (map.getLayer(featureLineLayerId)) map.removeLayer(featureLineLayerId);
                if (map.getLayer(featureTextLayerId)) map.removeLayer(featureTextLayerId);
                map.removeSource(featureSourceId);
            }
        }
    });
}

map.on('load', function() {
    fetchControllerData(); // Initial fetch of controller data
    setInterval(fetchControllerData, 10000); // Continuously update every 10 seconds

    // Add a 'moveend' event listener to refresh data based on the new viewport
    map.on('moveend', function() {
        fetchControllerData(); // This will re-fetch and update the map data according to the new viewport
    });
});
