// Assuming mapboxgl has been initialized and the map is created

// Initialize an object to keep track of vatsimMarkers by cid
const vatsimMarkers = {};

// Initialize an object to keep track of GeoJSON features by cid
const vatsimGeoJSON = {};

// Map to track active popups by pilot ID
const activePopups = {}; 

let currentSelectedPilotId = null; // Tracks the currently selected VATSIM user


const vatsimWaypointMarkers = []; // Track waypoint markers for removal

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

    // Listen for the 'load' event on your map instance
    map.on('load', function() {
        // Once the map has loaded, you can safely add your event listener for incoming data
        vatsimWorker.addEventListener('message', function(e) {
            const { pilots } = e.data;
            // Since the map is now fully loaded, it's safe to update the map
            updateMapWithPilots(pilots);
        });
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


const iconId = 'airplane-icon'; 
const imageUrl = '/static/images/location-arrow-vatsim.png'; 
function startImage() {
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
    const vatsimId = pilotId.replace('pilot-', ''); // Extract VATSIM ID from the pilot ID

    // Fetch flight plan waypoints for the clicked VATSIM player
    fetch(`api/construct_route/${vatsimId}`)
        .then(response => response.json())
        .then(data => {
            drawFlightPlan(data.waypoints);
        })
        .catch(error => console.error('Error fetching flight plan waypoints:', error));

    if (!activePopups[pilotId]) {
        var popup = new mapboxgl.Popup()
            .setLngLat(feature.geometry.coordinates)
            .setHTML(generatePopupContent(feature.properties))
            .addTo(map)
            .on('close', () => {
                delete activePopups[pilotId]; // Cleanup on close
                if (currentSelectedPilotId === pilotId) {
                    removeFlightRoute(); // Call a function to remove/hide the flight route
                    currentSelectedPilotId = null; // Reset the current selected pilot ID
                }
            });
        
        activePopups[pilotId] = popup;
        currentSelectedPilotId = pilotId; // Update the currently selected pilot ID
    } else {
        // Bring the existing popup to front
        activePopups[pilotId].addTo(map);
    }
});


function removeFlightRoute() {
    if (map.getLayer('flightRouteLayer')) {
        map.removeLayer('flightRouteLayer');
        map.removeSource('flightRoute');
    }
    
    // Remove all waypoint markers
    vatsimWaypointMarkers.forEach(marker => marker.remove());
    vatsimWaypointMarkers.length = 0; // Clear the array after removing the markers
}



function drawFlightPlan(waypoints) {
    const route = {
        'type': 'Feature',
        'properties': {},
        'geometry': {
            'type': 'LineString',
            'coordinates': waypoints.map(wp => [wp.longitude_deg, wp.latitude_deg])
        }
    };

    // Check if the map already has a source for the route, update it if yes, or add a new one if no
    if (map.getSource('flightRoute')) {
        map.getSource('flightRoute').setData(route);
    } else {
        map.addSource('flightRoute', {
            'type': 'geojson',
            'data': route
        });

        map.addLayer({
            'id': 'flightRouteLayer',
            'type': 'line',
            'source': 'flightRoute',
            'layout': {
                'line-join': 'round',
                'line-cap': 'round'
            },
            'paint': {
                'line-color': '#ff7e5f', 
                'line-width': 4,
                'line-opacity': 0.8
            }
        });
    }

    // Now, draw the waypoints markers after drawing the flight plan
    drawWaypointsMarkers(waypoints);
}

/**
 * Draws markers for the given waypoints, using Font Awesome triangle icons.
 * @param {Array} waypoints - The waypoints to draw markers for.
 */
function drawWaypointsMarkers(waypoints) {
    // Clear existing waypoint markers before drawing new ones
    vatsimWaypointMarkers.forEach(marker => marker.remove());
    vatsimWaypointMarkers.length = 0; // Reset the array

    waypoints.forEach(wp => {
        const el = document.createElement('div');
        el.className = 'waypoint-icon';
        el.innerHTML = `<i class="fa-duotone fa-triangle"></i><span style="display:block;">${wp.ident}</span>`;
        el.style.fontSize = '14px'; // Adjust icon size as needed
        el.style.color = 'gray'; // Adjust icon color as needed
        el.style.textAlign = 'center'; // Ensure text aligns under the icon
        el.firstChild.style.transform = 'translateY(-50%) scale(0.8)'; // Adjust the icon position and size

        // Create the marker and add it to the map
        const marker = new mapboxgl.Marker(el)
            .setLngLat([wp.longitude_deg, wp.latitude_deg])
            .addTo(map);

        // Add the marker to the vatsimWaypointMarkers array for later reference
        vatsimWaypointMarkers.push(marker);
    });
}




function generatePopupContent(pilot) {
    const vatsimId = pilot.id.replace('pilot-', '');
    return `
        <h3>Pilot Information</h3>
        <p><strong>Name:</strong> ${pilot.name}</p>
        <p><strong>Groundspeed:</strong> ${pilot.groundspeed} knots</p>
        <p><strong>Altitude:</strong> ${pilot.altitude} feet</p>
        <p><strong>Heading:</strong> ${pilot.heading}°</p>
        <p><strong>VATSIM ID:</strong> ${vatsimId}</p> <!-- Extracted from the pilot ID ; For testing purposes, remove later *** -->
    `;
}


// Update pilots every 15 seconds
setInterval(updatePilots, 15000);

startImage();







