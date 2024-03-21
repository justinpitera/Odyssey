// Assuming mapboxgl has been initialized and the map is created

// Initialize an object to keep track of vatsimMarkers by cid
const vatsimMarkers = {};

// Initialize an object to keep track of GeoJSON features by cid
const vatsimGeoJSON = {};

// Map to track active popups by pilot ID
const activePopups = {}; 

let currentSelectedPilotId = null; // Tracks the currently selected VATSIM user


const vatsimWaypointMarkers = []; // Track waypoint markers for removal




function setCookie(name, value, days) {
    var expires = "";
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days*24*60*60*1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "")  + expires + "; path=/";
}

function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}




function fetchAndUpdatePilotsDirectly() {
    // Define both fetch requests
    const fetchVATSIM = fetch('/map/api/vatsim_network/').then(response => response.json());
    const fetchIVAO = fetch('/map/api/ivao_network/').then(response => response.json());

    // Use Promise.all to wait for both requests to complete
    Promise.all([fetchVATSIM, fetchIVAO])
        .then(data => {
            // Combine the pilots data into a single object with vatsimPilots and ivaoPilots properties
            const combinedPilotsData = {
                vatsimPilots: data[0].pilots,
                ivaoPilots: data[1].pilots,
            };

            // Update the map with the combined pilots data
            updateMapWithPilots(combinedPilotsData);
        })
        .catch(err => console.error('Error fetching data from VATSIM or IVAO:', err));
}

// Function to update the map with pilots' data
function updateMapWithPilots(data) {
    console.log(data);

    // Process VATSIM pilots
    data.vatsimPilots.forEach(pilot => {
        // Assuming VATSIM pilots have a consistent structure with your existing code
        updatePilot(pilot, 'vatsim');
    });

    // Process IVAO pilots
    data.ivaoPilots.forEach(pilot => {
        // Adapt for IVAO's different structure
        updatePilot(pilot, 'ivao');
    });
}

// Function to handle individual pilot update or addition
function updatePilot(pilot, source) {
    // Use source-specific IDs and property names
    const pilotId = source === 'vatsim' ? `pilot-${pilot.cid}` : `pilot-${pilot.userId}`;
    const markerLngLat = [pilot.longitude, pilot.latitude];
    const groundspeed = source === 'vatsim' ? pilot.groundspeed : pilot.speed; // IVAO uses 'speed'
    const name = source === 'vatsim' ? pilot.name : `User ${pilot.userId}`; // Example adaptation
    const callsign = source === 'vatsim' ? pilot.callsign : `${pilot.callsign}`; // Defaulting for IVAO
    const network = source === 'vatsim' ? 'VATSIM' : 'IVAO'; 

    // Update GeoJSON feature for each pilot
    const feature = {
        type: 'Feature',
        geometry: {
            type: 'Point',
            coordinates: markerLngLat
        },
        properties: {
            id: pilotId,
            icon: iconId, // Use the PNG icon, assuming it's defined elsewhere
            name: name,
            groundspeed: groundspeed,
            altitude: pilot.altitude,
            callsign: callsign,
            network: network,
            heading: getTrueHeading(pilot.heading) // Assuming this function is defined elsewhere
        }
    };

    // Check if there's an existing popup for this pilot and update it
    if (activePopups[pilotId]) {
        const popupContent = generatePopupContent(feature.properties);
        activePopups[pilotId].setHTML(popupContent);
    }

    // Update or add the feature in vatsimGeoJSON object
    vatsimGeoJSON[pilotId] = feature;

    // Ensure the map source and layer are updated with the latest features
    updateMapSource();
}

// Ensure this function generates the popup content correctly
function generatePopupContent(properties) {
    // Adapt this based on your needs
    return `
        <h3><b>${properties.callsign}</b></h3>
        <p><strong>Name:</strong> ${properties.name}</p>
        <p><strong>Altitude:</strong> ${properties.altitude} feet</p>
        <p><strong>Groundspeed:</strong> ${properties.groundspeed} knots</p>
        <p><strong>Heading:</strong> ${properties.heading}°</p>
        <hr>
        <p><strong>Network:</strong> ${properties.network}</p>
    `;
}

function updateMapSource() {
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
    return `
        <h3><b>${pilot.callsign}</b></h3>
        <p><strong>Captain:</strong> ${pilot.name}</p>
        <p><strong>Altitude:</strong> ${pilot.altitude} feet</p>
        <p><strong>Groundspeed:</strong> ${pilot.groundspeed} knots</p>
        <p><strong>Heading:</strong> ${pilot.heading}°</p>
        <hr>
        <p><strong>Network:</strong> ${pilot.network}</p>
        
    `;
}
document.addEventListener('DOMContentLoaded', function() {
    const vatsimCheckbox = document.getElementById('vatsimFilter');

    // Set checkbox state from cookie on page load
    vatsimCheckbox.checked = getCookie('vatsimFilterEnabled') === 'true';

    // Add event listener to the VATSIM filter checkbox
    vatsimCheckbox.addEventListener('change', function() {
        setCookie('vatsimFilterEnabled', this.checked, 7); // Save state for 7 days
        
        if (this.checked) {
            updatePilots(); // Call your function to show VATSIM data
        } else {
            removeVATSIMDataFromMap(); // Call your function to hide VATSIM data
        }
    });

        // Update pilots every 15 seconds
        setInterval(updatePilots, 15000);



        map.on('load', function() {
            startImage();
        });
});

 function removeVATSIMDataFromMap() {
    // Example: Removing the VATSIM layer and source from the map
    if (map.getSource('vatsim')) {
        map.removeLayer('vatsim-markers');
        map.removeSource('vatsim');
    }

    // Additionally, remove any standalone markers if applicable
    Object.values(vatsimMarkers).forEach(marker => marker.remove());
    // Reset or clear any other relevant variables here
}








