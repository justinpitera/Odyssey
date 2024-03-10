
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
        el.innerHTML = '<i class="fa-solid fa-tower-control" style="color: gray; font-size: 20px; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0px 0px 6px #000;"></i>';
    } else if (airport.type === 'medium_airport') {
        el.innerHTML = '<i class="fa-solid fa-tower-control" style="color: gray; font-size: 20px; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0px 0px 6px #000;"></i>'; 
    } else if (airport.type === 'heliport') {
        el.innerHTML = '<i class="fa-solid fa-helicopter-symbol" style="color: #013220; font-size: 14px; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0px 0px 6px #000;"></i>'; 
    } else if (airport.type === 'small_airport') {
        el.innerHTML = '<i class="fa-solid fa-tower-control" style="color: gray; font-size: 14px; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0px 0px 6px #000;"></i>'; 
    }

    var marker = new mapboxgl.Marker(el)
        .setLngLat(airport.coordinates.split(',').map(coord => parseFloat(coord.trim())))
        .addTo(map);

    marker.getElement().addEventListener('click', function() {
        fetchAirportDetails(airport.ident);
    });

    markers.push(marker); // Track this marker
}








function fetchAirportDetails(airportIdent) {
    var url = `api/airport_details/${airportIdent}/`;

    fetch(url)
    .then(response => response.json())
    .then(data => {
        document.querySelector(".max-w-md .text-2xl").textContent = data.airportName;

        // Initialize arrivals and departures content with a surrounding div that has a fixed height and overflow-auto
        var arrivalsContent = '<div class="max-h-96 overflow-auto">';
        data.arrivals.forEach((arrival, index) => {
            arrivalsContent += `
            <div class="bg-white shadow overflow-hidden sm:rounded-md">
                <ul>
                    <li>
                        <a href="#" class="block hover:bg-gray-50" onclick="toggleDropdown('arrival-${index}')">
                            <div class="px-4 py-4 sm:px-6">
                                <div class="flex items-center justify-between">
                                    <p class="text-sm font-medium text-indigo-600 truncate">${arrival.callsign} - ${arrival.departure} -> ${arrival.arrival}</p>
                                    <div class="ml-2 flex-shrink-0 flex">
                                        <p class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Details</p>
                                    </div>
                                </div>
                            </div>
                        </a>
                        <div id="arrival-${index}" class="hidden px-4 py-4 sm:px-6">
                            <p>Callsign: ${arrival.callsign}</p>
                            <p>Aircraft: ${arrival.aircraft}</p>
                            <p>Altitude: ${arrival.altitude} ft</p>
                            <p>Cruise Speed: ${arrival.cruise_speed} knots</p>
                            <p>Route: ${arrival.route}</p>
                        </div>
                    </li>
                </ul>
            </div>`;
        });
        arrivalsContent += '</div>'; // Close the div that sets the fixed height and overflow

        var departuresContent = '<div class="max-h-96 overflow-auto">';
        data.departures.forEach((departure, index) => {
            departuresContent += `
            <div class="bg-white shadow overflow-hidden sm:rounded-md">
                <ul>
                    <li>
                        <a href="#" class="block hover:bg-gray-50" onclick="toggleDropdown('departure-${index}')">
                        <div class="px-4 py-4 sm:px-6">
                            <div class="flex items-center justify-between">
                                <p class="text-sm font-medium text-indigo-600 truncate">${departure.callsign} - ${departure.departure} -> ${departure.arrival}</p>
                                <div class="ml-2 flex-shrink-0 flex">
                                    <p class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Details</p>
                                </div>
                            </div>
                        </div>
                    </a>
                    <div id="departure-${index}" class="hidden px-4 py-4 sm:px-6">
                        <p>Callsign: ${departure.callsign}</p>
                        <p>Aircraft: ${departure.aircraft}</p>
                        <p>Altitude: ${departure.altitude} ft</p>
                        <p>Cruise Speed: ${departure.cruise_speed} knots</p>
                        <p>Route: ${departure.route}</p>
                    </div>
                    </li>
                </ul>
            </div>`;
        });
        departuresContent += '</div>'; // Close the div that sets the fixed height and overflow

        document.getElementById("arrivals").innerHTML = arrivalsContent;
        document.getElementById("departures").innerHTML = departuresContent;
        document.getElementById("airport-card").style.display = "block";
    });
}







// Helper function to toggle dropdown visibility
function toggleDropdown(id) {
    var element = document.getElementById(id);
    if (element.classList.contains('hidden')) {
        element.classList.remove('hidden');
    } else {
        element.classList.add('hidden');
    }
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

// Close airport card when clicking close button
document.getElementById("close-card-btn").addEventListener("click", function() {
    document.getElementById("airport-card").style.display = "none";
});
