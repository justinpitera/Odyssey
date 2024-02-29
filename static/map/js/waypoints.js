// Assumes the Mapbox GL JS map instance 'map' has been initialized and added to the page

/**
 * Fetches flight plan data from an API.
 * @param {String} url - The API URL to fetch flight plan data.
 * @returns {Promise<Object>} A promise that resolves to the flight plan data.
 */
function fetchFlightPlanData(url) {
    return fetch(url)
        .then(response => response.json())
        .catch(error => console.error('Error fetching flight plan data:', error));
}

/**
 * Processes waypoints to draw the route and markers.
 * @param {Object} data - The flight plan data including waypoints.
 */
function processAndDrawRoute(data) {
    const waypoints = data.navlog.fix; // Assumes a specific data structure
    const routePoints = waypoints.map(wp => ({
        type: 'Feature',
        geometry: {
            type: 'Point',
            coordinates: [wp.pos_long, wp.pos_lat]
        },
        properties: {
            ident: wp.ident
        }
    }));

    // Calculate the cumulative distance to each waypoint, including TOD calculation
    let totalDistance = 0;
    let todCumulativeDistance = 0;
    let foundTOD = false;
    routePoints.reduce((prev, current, index) => {
        if (index > 0) {
            const distance = calculateDistance(prev.geometry.coordinates, current.geometry.coordinates);
            totalDistance += distance;
            if (!foundTOD && prev.properties.ident === 'TOD') {
                todCumulativeDistance = totalDistance;
                foundTOD = true;
            }
        }
        return current;
    });

    const todPosition = todCumulativeDistance / totalDistance;

    drawRoute(routePoints, todPosition); // Now correctly passing todPosition
    drawWaypointsMarkers(routePoints); // Draw markers

}




function calculateDistance(coord1, coord2) {
    const [lon1, lat1] = coord1;
    const [lon2, lat2] = coord2;
    const R = 6371e3; // Earth's radius in meters
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;

    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    const distance = R * c; // Distance in meters
    return distance;
}


function drawRoute(routePoints, todPosition) {
    // Initialize an array to hold segments of the route, with each segment being a GeoJSON LineString
    let segments = [];
    let currentSegment = [routePoints[0].geometry.coordinates]; // Start with the first point

    for (let i = 1; i < routePoints.length; i++) {
        const prevPoint = routePoints[i - 1].geometry.coordinates;
        const currPoint = routePoints[i].geometry.coordinates;
        const longDiff = currPoint[0] - prevPoint[0];

        // Check if crossing the antimeridian
        if (Math.abs(longDiff) > 180) {
            // Finish the current segment and start a new one
            segments.push({
                type: 'Feature',
                properties: {},
                geometry: {
                    type: 'LineString',
                    coordinates: currentSegment
                }
            });
            currentSegment = [currPoint]; // Start a new segment with the current point
        } else {
            // Continue adding to the current segment
            currentSegment.push(currPoint);
        }
    }

    // Add the last segment
    segments.push({
        type: 'Feature',
        properties: {},
        geometry: {
            type: 'LineString',
            coordinates: currentSegment
        }
    });

    // Now, handle each segment as a separate GeoJSON object
    segments.forEach((segment, index) => {
        const segmentId = `route-segment-${index}`;
        if (map.getSource(segmentId)) {
            map.getSource(segmentId).setData(segment);
        } else {
            map.addSource(segmentId, {
                type: 'geojson',
                data: segment,
                lineMetrics: true, // Enable lineMetrics for gradient calculations
            });
            map.addLayer({
                id: segmentId,
                type: 'line',
                source: segmentId,
                layout: {},
                paint: {
                    'line-width': 6,
                    // Adjust the line-gradient to start at the TOD waypoint
                    'line-gradient': [
                        'interpolate',
                        ['linear'],
                        ['line-progress'],
                        0, 'rgba(50, 205, 50, 0.5)', // Use a more transparent color before TOD
                        0.88, 'rgba(3, 252, 240, 1)', // Start of TOD
                        1, 'rgba(255, 0, 0, 1)' // End color
                    ]
                }
            });
        }
    });
}



function drawTODMarker(routePoints, todPosition) {
    let totalDistance = 0;
    let distances = [0]; // Starting with 0 distance at the first point

    // Calculate cumulative distances for each waypoint
    for (let i = 1; i < routePoints.length; i++) {
        const distance = calculateDistance(routePoints[i - 1].geometry.coordinates, routePoints[i].geometry.coordinates);
        totalDistance += distance;
        distances.push(totalDistance);
    }

    // Find TOD position in absolute terms (meters)
    const todAbsolutePosition = todPosition * totalDistance;

    // Find the segment where TOD is located
    let todCoordinates;
    for (let i = 0; i < distances.length - 1; i++) {
        if (todAbsolutePosition >= distances[i] && todAbsolutePosition <= distances[i + 1]) {
            // Interpolate to find exact TOD coordinates
            const segmentFraction = (todAbsolutePosition - distances[i]) / (distances[i + 1] - distances[i]);
            todCoordinates = [
                routePoints[i].geometry.coordinates[0] + (routePoints[i + 1].geometry.coordinates[0] - routePoints[i].geometry.coordinates[0]) * segmentFraction,
                routePoints[i].geometry.coordinates[1] + (routePoints[i + 1].geometry.coordinates[1] - routePoints[i].geometry.coordinates[1]) * segmentFraction,
            ];
            break;
        }
    }

        // Convert each TOD coordinate string into a [longitude, latitude] format
    const convertedTODCoordinates = todCoordinates.map(coord => {
        // Split the string into two parts at the minus sign
        // Note: This assumes that all latitudes are negative, which might not always be the case
        let parts = coord.split('-').map((part, index) => {
            // Prepend a minus sign back to all parts except the first (longitude)
            return (index > 0 ? -1 : 1) * parseFloat(part);
        });

        // Correct for the initial longitude if it's supposed to be negative
        if (coord.startsWith('-')) {
            parts[0] = -parts[0]; // Convert longitude to negative
        }

        return parts; // Return the converted parts as the new coordinate array
    });


    if (todCoordinates) {
        // Draw a marker at TOD coordinates
        console.log('TOD coordinates:', todCoordinates);
        console.log('Converted TOD coordinates:', convertedTODCoordinates);
        new mapboxgl.Marker()
            .setLngLat(convertedTODCoordinates[0], convertedTODCoordinates[1])
            .addTo(map);
    }
}







// Draws markers for the given waypoints, hiding them until zoomed in closely
function drawWaypointsMarkers(waypoints) {
    // Define the minimum zoom level required to display the waypoints
    const minZoomLevelToShowWaypoints = 6.5;

    const markers = []; // Keep track of all created markers

    waypoints.forEach(wp => {
        // Create a HTML element for each waypoint
        const el = document.createElement('div');
        el.className = 'waypoint-icon';
        el.innerHTML = `<i class="fa-duotone fa-triangle" style="color: white;"></i> <span style="color: white;">${wp.properties.ident}</span>`;

        // Create a marker but don't add it to the map yet
        const marker = new mapboxgl.Marker(el)
            .setLngLat(wp.geometry.coordinates);

        markers.push(marker); // Store the marker for later use
    });

    function updateMarkersVisibility() {
        const zoom = map.getZoom(); // Get the current zoom level

        markers.forEach(marker => {
            if (zoom >= minZoomLevelToShowWaypoints) {
                // If the zoom level is high enough, add the marker to the map if it's not already added
                if (!marker._map) marker.addTo(map);
            } else {
                // If the zoom level is too low, remove the marker from the map if it's added
                if (marker._map) marker.remove();
            }
        });
    }

    // Update markers visibility initially and whenever the map is zoomed
    map.on('zoom', updateMarkersVisibility);
    updateMarkersVisibility();
}


/**
 * Main function to draw waypoints and route.
 */
function drawWaypointsAndRoute() {
    const simBriefApiUrl = 'https://www.simbrief.com/api/xml.fetcher.php?userid=833267&json=1';

    fetchFlightPlanData(simBriefApiUrl)
        .then(processAndDrawRoute);
}

drawWaypointsAndRoute();
