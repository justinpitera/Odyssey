// Assuming mapboxgl has been initialized and the map is created

// Initialize an object to keep track of GeoJSON features for airports
const airportsGeoJSON = {
    type: 'FeatureCollection',
    features: []
};

// Extend airportIcons to include sizes for different types of airports
const airportIcons = {
    large_airport: { id: 'large-airport-icon', url: '/static/images/airport.png', size: 0.1 },
    medium_airport: { id: 'medium-airport-icon', url: '/static/images/medium-airport.png', size: 0.08 },
    small_airport: { id: 'small-airport-icon', url: '/static/images/small-airport.png', size: 0.06 },
    heliport: { id: 'heliport-icon', url: '/static/images/helipad.png', size: 0.075 }
};

// Function to load icons (unchanged)
function loadIcons(callback) {
    const iconsToLoad = Object.keys(airportIcons).length;
    let iconsLoaded = 0;

    Object.values(airportIcons).forEach(icon => {
        if (!map.hasImage(icon.id)) {
            map.loadImage(icon.url, (error, image) => {
                if (error) throw error;
                map.addImage(icon.id, image);
                iconsLoaded++;
                if (iconsLoaded === iconsToLoad) {
                    callback(); // All icons loaded, proceed to callback
                }
            });
        } else {
            iconsLoaded++;
            if (iconsLoaded === iconsToLoad) {
                callback(); // All icons loaded, proceed to callback
            }
        }
    });
}

// Function to fetch and display airports
function fetchAndDisplayAirports() {
    const bounds = map.getBounds();
    const zoomLevel = map.getZoom();

    const url = `api/airports/?northBound=${bounds.getNorth()}&southBound=${bounds.getSouth()}&eastBound=${bounds.getEast()}&westBound=${bounds.getWest()}&zoom=${zoomLevel}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const airports = data.airports;
            updateMapWithAirports(airports);
        })
        .catch(err => console.error('Error fetching airports:', err));
}

// Function to update the map with airports' data (MODIFIED FOR DYNAMIC SIZING)
function updateMapWithAirports(airports) {
    airportsGeoJSON.features = []; // Clear existing features

    airports.forEach(airport => {
        const markerLngLat = airport.coordinates.split(',').map(coord => parseFloat(coord.trim()));
        const iconInfo = airportIcons[airport.type] || airportIcons['small_airport']; // Fallback to small_airport

        const feature = {
            type: 'Feature',
            geometry: { type: 'Point', coordinates: markerLngLat },
            properties: {
                id: `airport-${airport.id}`,
                name: airport.name,
                icon: iconInfo.id,
                size: iconInfo.size // Include size in properties
            }
        };

        airportsGeoJSON.features.push(feature);
    });

    if (map.getSource('airports')) {
        map.getSource('airports').setData(airportsGeoJSON);
    } else {
        map.addSource('airports', { type: 'geojson', data: airportsGeoJSON });
        map.addLayer({
            id: 'airport-markers',
            type: 'symbol',
            source: 'airports',
            layout: {
                'icon-image': ['get', 'icon'],
                'icon-size': ['get', 'size'], // Dynamic sizing based on feature properties
                'icon-allow-overlap': true
            }
        });
    }
}

// Load icons and then fetch and display airports
loadIcons(fetchAndDisplayAirports);

// Update airports on map move or zoom
map.on('moveend', fetchAndDisplayAirports);
map.on('zoomend', fetchAndDisplayAirports);
