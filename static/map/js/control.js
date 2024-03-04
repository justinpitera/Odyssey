function fetchAndUpdateATCControllersDirectly() {
    fetch('/map/api/controllers/')
        .then(response => response.json())
        .then(data => {
            const controllers = data.controllers; // Adjust according to the JSON structure
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

    controllers.forEach(controller => {
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
            // update or add the GeoJSON source for ATC Approach
        updateOrCreateSource('vatsim-atc-approach', approachFeatures);
        // update or add the GeoJSON source for ATC Tower and Ground
        updateOrCreateSource('vatsim-atc-tower-ground', towerAndGroundFeatures);
    });


    function updateOrCreateSource(sourceId, features) {
        if (map.getSource(sourceId)) {
            // Update the existing source's data
            map.getSource(sourceId).setData({
                type: 'FeatureCollection',
                features: features
            });
        } else {
            // Add new source
            map.addSource(sourceId, {
                type: 'geojson',
                data: {
                    type: 'FeatureCollection',
                    features: features
                }
            });
    
            // Based on the sourceId, decide whether to add a circle or symbol layer
            if (sourceId.includes('approach')) {
                // Add circle layer for Approach if it doesn't exist
                if (!map.getLayer(`${sourceId}-circle`)) {
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

                    });
                }
            } else {
                // Add symbol layer for Tower and Ground if it doesn't exist
                if (!map.getLayer(`${sourceId}-symbol`)) {
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

                    });
                }
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
    const sourceId = `vatsim-atc-${type}`;
    const layerId = `${sourceId}-${type === 'approach' ? 'circle' : 'symbol'}`;

    if (!map.getLayer(layerId)) {
        if (type === 'approach') {
            map.addLayer({
                id: layerId,
                type: 'circle',
                source: sourceId,
                paint: {
                    'circle-color': '#00ff00',
                    'circle-opacity': 0.5,
                    'circle-radius': {
                        'base': 20, // Adjust base size for better visibility
                        'stops': [[5, 10], [15, 40]] // Adjust stops for dynamic sizing
                    }
                }
                // Removed minzoom property
            });
        } else {
            // Adjust symbol layer for Tower and Ground
            map.addLayer({
                id: layerId,
                type: 'symbol',
                source: sourceId,
                layout: {
                    'text-field': '{type}', // Use direct type for text
                    'text-size': {
                        'base': 12, // Adjust text size for visibility
                        'stops': [[5, 12], [15, 24]] // Adjust stops for dynamic sizing
                    }
                },
                paint: {
                    'text-color': '#ffffff', // Example text color, adjust as needed
                }
                // Removed minzoom property
            });
        }
    }
}



map.on('moveend', fetchAndUpdateATCControllersDirectly());
fetchAndUpdateATCControllersDirectly();
setInterval(fetchAndUpdateATCControllersDirectly, 15000);

// Initialize objects to keep track of GeoJSON features
const vatsimPilotGeoJSON = {};
const vatsimATCGeoJSON = {};
