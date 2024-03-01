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
 * Calculates the distance between two coordinates.
 * @param {Array} coord1 - The first coordinate [longitude, latitude].
 * @param {Array} coord2 - The second coordinate [longitude, latitude].
 * @returns {number} The distance in meters.
 */
function calculateDistance(coord1, coord2) {
    // Haversine formula to calculate distance
    const R = 6371e3; // Earth's radius in meters
    const φ1 = coord1[1] * Math.PI / 180;
    const φ2 = coord2[1] * Math.PI / 180;
    const Δφ = (coord2[1] - coord1[1]) * Math.PI / 180;
    const Δλ = (coord2[0] - coord1[0]) * Math.PI / 180;
    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c; // Distance in meters
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

    drawRoute(routePoints); // Draw the route
    drawWaypointsMarkers(routePoints); // Draw markers for waypoints
}

/**
 * Draws the route on the map, splitting it at the TOD for gradient simulation.
 * @param {Array} routePoints - The route points.
 */
function drawRoute(routePoints) {
    // Assuming TOD is correctly identified and marked in your waypoints
    let todIndex = routePoints.findIndex(point => point.properties.ident === 'TOD');
    if (todIndex === -1) {
        console.error('TOD waypoint not found.');
        return;
    }

    // Split the route at the TOD index
    const preTODPoints = routePoints.slice(0, todIndex + 1);
    const postTODPoints = routePoints.slice(todIndex);

    // Draw pre-TOD segment
    drawRouteSegment(preTODPoints, 'pre-TOD', '#007cbf'); // Blue color for pre-TOD
    // Draw post-TOD segment
    drawRouteSegment(postTODPoints, 'post-TOD', '#ff0000'); // Red color for post-TOD
}

/**
 * Draws a segment of the route with a specified color.
 * @param {Array} segmentPoints - The points in the route segment.
 * @param {String} segmentId - The ID for the segment.
 * @param {String} color - The color for the segment.
 */
function drawRouteSegment(segmentPoints, segmentId, color) {
    const coordinates = segmentPoints.map(point => point.geometry.coordinates);
    const routeFeature = {
        type: 'Feature',
        properties: {},
        geometry: {
            type: 'LineString',
            coordinates: coordinates
        }
    };

    if (map.getSource(segmentId)) {
        map.getSource(segmentId).setData(routeFeature);
    } else {
        map.addSource(segmentId, {
            type: 'geojson',
            data: routeFeature
        });
        map.addLayer({
            id: segmentId,
            type: 'line',
            source: segmentId,
            layout: {},
            paint: {
                'line-width': 6,
                'line-color': color
            }
        });
    }
}

/**
 * Draws markers for the given waypoints, using Font Awesome triangle icons.
 * @param {Array} waypoints - The waypoints to draw markers for.
 */
function drawWaypointsMarkers(waypoints) {
    waypoints.forEach(wp => {
        // Create a div element for the marker with a Font Awesome triangle icon
        const el = document.createElement('div');
        el.className = 'waypoint-icon';
        el.innerHTML = `<i class="fa-duotone fa-triangle"></i><span>${wp.properties.ident}</span>`;
        el.style.fontSize = '14px'; // Adjust icon size as needed
        el.style.color = 'gray'; // Adjust icon color as needed
        el.style.textAlign = 'center'; // Ensure text aligns under the icon
        el.firstChild.style.transform = 'translateY(-50%)'; // Adjust the icon position

        // Create and add the marker to the map
        new mapboxgl.Marker(el)
            .setLngLat(wp.geometry.coordinates)
            .addTo(map);
    });
}


/**
 * Main function to draw waypoints and route.
 */
function drawWaypointsAndRoute() {
    const simBriefApiUrl = 'https://www.simbrief.com/api/xml.fetcher.php?userid=833267&json=1'; // Replace with your actual API URL

    fetchFlightPlanData(simBriefApiUrl)
        .then(processAndDrawRoute)
        .catch(error => console.error('Failed to draw waypoints and route:', error));
}

drawWaypointsAndRoute();