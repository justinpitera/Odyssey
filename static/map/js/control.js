function fetchAndUpdateATCControllersDirectly() {
    fetch('/map/search_vatsim')
        .then(response => response.json())
        .then(data => {
            const controllers = data.airports; // Assuming this is the structure
            updateMapWithATCControllers(controllers);
        })
        .catch(err => console.error('Error fetching ATC controller data:', err));
}

function updateMapWithATCControllers(controllers) {
    // Filter controllers to include only those within the current viewport
    const visibleControllers = controllers.filter(controller => {
        const controllerLngLat = [controller.longitude_deg, controller.latitude_deg];
        return map.getBounds().contains(controllerLngLat);
    });

    // Prepare data for different types
    const approachFeatures = [];
    const towerAndGroundFeatures = [];

    visibleControllers.forEach(controller => {
        const markerLngLat = [controller.longitude_deg, controller.latitude_deg];
        const feature = {
            type: 'Feature',
            geometry: {
                type: 'Point',
                coordinates: markerLngLat
            },
            properties: {
                id: `atc-${controller.ident}`,
                name: controller.ident,
                type: controller.type // Assuming this contains 'approach', 'tower', or 'ground'
            }
        };

        if (controller.type === 'approach') {
            approachFeatures.push(feature);
        } else {
            towerAndGroundFeatures.push(feature);
        }
    });

    // Update or add the GeoJSON source for ATC Approach
    updateOrCreateSource('vatsim-atc-approach', approachFeatures);
    // Update or add the GeoJSON source for ATC Tower and Ground
    updateOrCreateSource('vatsim-atc-tower-ground', towerAndGroundFeatures);

    // Function to update or create source and corresponding layer
    function updateOrCreateSource(sourceId, features) {
        if (map.getSource(sourceId)) {
            map.getSource(sourceId).setData({
                type: 'FeatureCollection',
                features: features
            });
        } else {
            map.addSource(sourceId, {
                type: 'geojson',
                data: {
                    type: 'FeatureCollection',
                    features: features
                }
            });

            if (sourceId === 'vatsim-atc-approach') {
                // Add circle layer for Approach
                map.addLayer({
                    id: `${sourceId}-circle`,
                    type: 'circle',
                    source: sourceId,
                    paint: {
                        'circle-color': '#00ff00',
                        'circle-opacity': 0.5,
                        'circle-radius': {
                            'base': 30,
                            'stops': [[12, 30], [22, 250]]
                        }
                    },
                    minzoom: 4.5,
                });
            } else {
                // Add symbol layer for Tower and Ground
                map.addLayer({
                    id: `${sourceId}-symbol`,
                    type: 'symbol',
                    source: sourceId,
                    layout: {
                        'text-field': ['get', 'type'],
                        'text-variable-anchor': ['top', 'bottom', 'left', 'right'],
                        'text-justify': 'auto',
                        'text-size': 24
                    },
                    paint: {
                        'text-color': ['match', ['get', 'type'], 'tower', '#ff0000', 'ground', '#008000', '#ffffff'],
                    },
                    minzoom: 3,
                });
            }
        }
    }
}

function updateOrCreateSourceForATCType(type, feature) {
    const sourceId = `vatsim-atc-${type}`;

    if (map.getSource(sourceId)) {
        const data = map.getSource(sourceId).getData();
        data.features.push(feature);
        map.getSource(sourceId).setData(data);
    } else {
        map.addSource(sourceId, {
            type: 'geojson',
            data: {
                type: 'FeatureCollection',
                features: [feature]
            }
        });
        addLayerForType(type);
    }
}

function addLayerForType(type) {
    switch(type) {
        case 'approach':
            // Add circle layer for approach
            map.addLayer({
                id: `vatsim-atc-${type}-circle`,
                type: 'circle',
                source: `vatsim-atc-${type}`,
                paint: {
                    'circle-color': '#00ff00',
                    'circle-opacity': 0.5,
                    'circle-radius': {
                        'base': 30,
                        'stops': [[12, 30], [22, 250]]
                    }
                },
                minzoom: 4.5,
            });
            break;
        case 'tower':
        case 'ground':
            // Add symbol layer for tower and ground with text as T or G
            map.addLayer({
                id: `vatsim-atc-${type}-symbol`,
                type: 'symbol',
                source: `vatsim-atc-${type}`,
                layout: {
                    'text-field': ['get', 'symbol'],
                    'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
                    'text-size': 12
                },
                paint: {
                    'text-color': ['get', 'color']
                },
                minzoom: 4.5,
            });
            break;
    }
}

// Event listeners and initial fetch as before
map.on('moveend', fetchAndUpdateATCControllersDirectly);
map.on('zoomend', fetchAndUpdateATCControllersDirectly);
fetchAndUpdateATCControllersDirectly();
setInterval(fetchAndUpdateATCControllersDirectly, 15000);

// Initialize objects to keep track of GeoJSON features
const vatsimPilotGeoJSON = {};
const vatsimATCGeoJSON = {};
