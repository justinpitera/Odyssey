
let markers = []; // Store marker instances
let markersData = []; // Store fetched data for reuse

function updateAirportMarkers() {
    const currentZoom = map.getZoom();
    markers.forEach(marker => marker.remove()); // Remove all markers
    markers = []; // Clear markers array

    markersData.forEach(airport => {
        // Since the backend already filters the airports based on the zoom level,
        // there's no need for further checks here.
        // Simply create and add markers for the airports received.
        createAndAddMarker(airport);
    });
}


function createAndAddMarker(airport) {
    var el = document.createElement('div');
    el.className = 'marker';
    // Assign icon based on airport type
    if (airport.type === 'large_airport') {
        el.innerHTML = '<i class="fa-solid fa-tower-control" style="color: gray; font-size: 20px; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0px 0px 6px #000;" "></i>'; // Example icon for large airports
    } else if (airport.type === 'medium_airport') {
        el.innerHTML = '<i class="fa-solid fa-tower-control" style="color: gray; font-size: 20px; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0px 0px 6px #000;" "></i>'; // Example icon for medium airports
    } else if (airport.type === 'heliport') {
        el.innerHTML = '<i class="fa-solid fa-helicopter-symbol" style="color: #013220; font-size: 14px; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0px 0px 6px #000;" ></i>'; // Example icon for heliports with black outline and shadow
    } else if (airport.type === 'small_airport') {
    el.innerHTML = '<i class="fa-solid fa-tower-control" style="color: gray; font-size: 14px; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0px 0px 6px #000;" ></i>'; // Example icon for heliports with black outline and shadow
    // Example icon for heliports
    }



    var marker = new mapboxgl.Marker(el)
        .setLngLat(airport.coordinates.split(',').map(coord => parseFloat(coord.trim())))
        .setPopup(new mapboxgl.Popup({ offset: 25 })
        .setHTML('<h3>' + airport.name + '</h3><p>' + airport.municipality + '</p>'))
        .addTo(map);

    markers.push(marker); // Track this marker
}




function fetchAndDisplayAirports() {
    var bounds = map.getBounds();
    var zoomLevel = map.getZoom();

    // Include zoom level in the request
    var url = `api/airports/?northBound=${bounds.getNorth()}&southBound=${bounds.getSouth()}&eastBound=${bounds.getEast()}&westBound=${bounds.getWest()}&zoom=${zoomLevel}`;

    fetch(url)
    .then(response => response.json())
    .then(data => {
        markersData = data.airports; // Update the markersData with the fetched data
        updateAirportMarkers(); // Update markers based on new data
    });
}

// Initial fetch
fetchAndDisplayAirports();

// Update markers on map move or zoom
map.on('moveend', fetchAndDisplayAirports);
map.on('zoomend', fetchAndDisplayAirports);