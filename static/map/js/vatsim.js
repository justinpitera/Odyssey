// Assuming mapboxgl has been initialized and the map is created

// Initialize an object to keep track of vatsimMarkers by cid
const vatsimMarkers = {};

// Initialize an object to keep track of GeoJSON features by cid
const vatsimGeoJSON = {};

// Map to track active popups by pilot ID
const activePopups = {}; 



// Function to fetch and update pilots directly without a worker
function fetchAndUpdatePilotsDirectly() {
    fetch('https://data.vatsim.net/v3/vatsim-data.json')
        .then(response => response.json())
        .then(data => {
            const pilots = data.pilots;
            // Assuming you have a way to filter or process these pilots as needed
            updateMapWithPilots(pilots);
        })
        .catch(err => console.error('Error fetching VATSIM data:', err));
}
// Function to update the map with pilots' data
function updateMapWithPilots(pilots) {
    pilots.forEach(pilot => {
        const pilotId = `pilot-${pilot.cid}`;
        const markerLngLat = [pilot.longitude, pilot.latitude];

        // Update GeoJSON feature for each pilot
        const feature = {
            type: 'Feature',
            geometry: {
                type: 'Point',
                coordinates: markerLngLat
            },
            properties: {
                id: pilotId,
                icon: iconId, // Use the PNG icon
                name: pilot.name,
                groundspeed: pilot.groundspeed,
                altitude: pilot.altitude,
                heading: getTrueHeading(pilot.heading)
            }
        };
        // Check if there's an existing popup for this pilot and update it
        if (activePopups[pilotId]) {
            const popupContent = generatePopupContent(pilot);
            activePopups[pilotId].setHTML(popupContent);
        }

        // Update or add the feature in vatsimGeoJSON object
        vatsimGeoJSON[pilotId] = feature;
    });

    // Update or add the GeoJSON source for the pilots on the map
    if (map.getSource('vatsim')) {
        const source = map.getSource('vatsim');
        source.setData({
            type: 'FeatureCollection',
            features: Object.values(vatsimGeoJSON)
        });
    } else {
        map.addSource('vatsim', {
            type: 'geojson',
            data: {
                type: 'FeatureCollection',
                features: Object.values(vatsimGeoJSON)
            }
        });
        map.addLayer({
            id: 'vatsim-markers',
            type: 'symbol',
            source: 'vatsim',
            layout: {
                'icon-image': iconId,
                'icon-rotate': ['get', 'heading'],
                'icon-allow-overlap': true,
                'icon-size': 0.045 // Adjust size as needed
            }
        });
    }
}



function getTrueHeading(heading) {
    // Get the current bearing of the map
    const mapBearing = map.getBearing();
    // The desired rotation of the marker is the negative of the map's bearing plus the aircraft's heading.
    // This ensures the marker remains oriented to the earth, not the map's rotation.
    const rotation = heading - mapBearing;
    return rotation;
}

// Check if Web Workers are supported and initialize worker or fallback
if (window.Worker) {
    const vatsimWorker = new Worker('/static/map/js/vatsimWorker.js');

    vatsimWorker.addEventListener('message', function(e) {
        const { pilots } = e.data;
        updateMapWithPilots(pilots);
    });

    // Modify updatePilots to send message to worker
    function updatePilots() {
        let currentBounds = map.getBounds().toArray();
        // Logic to expand the bounds and request updates goes here...
        vatsimWorker.postMessage({ action: 'updatePilots', /* additional data */ });
    }
} else {
    console.log('Web Workers are not supported in your browser.');
    // Use the direct fetch and update method as a fallback
    function updatePilots() {
        fetchAndUpdatePilotsDirectly();
    }
}


// URL to your PNG image for the airplane icon
const iconId = 'airplane-icon'; // A constant ID for the PNG icon
const imageUrl = '/static/images/location-arrow-vatsim.png'; // Change this to the URL of your PNG image
function startImage() {
    console.log('Image loaded');
// Load the airplane icon once and then start the update process
if (!map.hasImage(iconId)) {
    map.loadImage(imageUrl, function(error, image) {
        if (error) throw error;
        map.addImage(iconId, image);
        
        // Initial update
        updatePilots();
    });
} else {
    // Image already exists, proceed with updating pilots
    updatePilots();
}

}


map.on('click', 'vatsim-markers', function(e) {
    var feature = e.features[0];
    var pilotId = feature.properties.id;

    if (!activePopups[pilotId]) {
        var popup = new mapboxgl.Popup()
            .setLngLat(feature.geometry.coordinates)
            .setHTML(generatePopupContent(feature.properties))
            .addTo(map)
            .on('close', () => delete activePopups[pilotId]); // Cleanup on close
        
        activePopups[pilotId] = popup;
    } else {
        // Bring the existing popup to front
        activePopups[pilotId].addTo(map);
    }
});


function generatePopupContent(pilot) {
    return `
        <h3>Pilot Information</h3>
        <p><strong>Name:</strong> ${pilot.name}</p>
        <p><strong>Groundspeed:</strong> ${pilot.groundspeed} knots</p>
        <p><strong>Altitude:</strong> ${pilot.altitude} feet</p>
        <p><strong>Heading:</strong> ${pilot.heading}°</p>
    `;
}


// Update pilots every 15 seconds
setInterval(updatePilots, 15000);

startImage();


