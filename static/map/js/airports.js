
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
        // Set the airport name
        document.querySelector(".max-w-2xl .text-2xl").textContent = data.airportName;

        // Initialize arrivals content with a surrounding div that has a fixed height and overflow-auto
        var arrivalsContent = '<div class="max-h-96 overflow-auto space-y-4">'; // Added space-y-4 for spacing between cards
        var countOfArrivals = 0
        var countOfDepartures = 0;
        if (data.arrivals.length === 0) {
            
            arrivalsContent += '<div class="p-4 details-container" style="color: black;"><p>No arrivals available...</p></div>';
            
        } else {
            countOfArrivals = data.arrivals.length;
            countOfDepartures = data.departures.length;


            data.arrivals.forEach((arrival, index) => {
                arrivalsContent += `
                <div class="bg-white shadow overflow-hidden sm:rounded-lg"> <!-- Changed rounded-md to rounded-lg and removed sm: -->
                    <ul class="divide-y divide-gray-200"> <!-- Added divide-y and divide-gray-200 for separation -->
                        <li class="p-4 hover:bg-gray-50"> <!-- Added padding here and hover effect directly -->
                            <div onclick="toggleDropdown('arrival-${index}')" class="cursor-pointer">
                                <div class="flex items-center justify-between">
                                    <p class="text-sm font-medium text-indigo-600 truncate"><strong>${arrival.callsign}</strong> - ${arrival.departure} <i class="fa-solid fa-arrow-right"></i> ${arrival.arrival}</p>
                                    <div class="ml-2 flex-shrink-0 flex">
                                        <p class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Details</p>
                                    </div>
                                </div>
                                <div id="arrival-${index}" class="hidden mt-4">
                                <div class="flex items-center">
                                <!-- Flight start icon -->
                                <i class="fas fa-plane-departure"></i>

                                <!-- Progress bar container -->
                                <div class="w-full bg-gray-200 rounded-full h-4 mx-4">
                                    <!-- Progress indicator -->
                                    <div class="bg-blue-600 h-4 rounded-full" style="width: ${100-arrival.distanceRemaining}%"></div>
                                </div>

                                <!-- Flight end icon -->
                                <i class="fas fa-plane-arrival"></i>
                                </div>

                                </div>
                                <hr>
                                <p><i class="fas fa-plane"></i> Aircraft: ${arrival.aircraft}</p>
                                <p><i class="fas fa-arrows-alt-v"></i> Cruise Altitude: ${arrival.altitude} ft</p>
                                <p><i class="fas fa-tachometer-alt"></i> Cruise Speed: ${arrival.cruise_speed} knots</p>
                                <p><i class="fas fa-route"></i> Route: ${arrival.route}</p>
                                <p>Remaining: ${arrival.distanceRemaining}</p>
                            </div>
                        </li>
                    </ul>
                </div>`;
            });
        }
        arrivalsContent += '</div>'; // Close the div that sets the fixed height and overflow

        // Initialize departures content with similar changes as arrivals
        var departuresContent = '<div class="max-h-96 overflow-auto space-y-4">';
        if (data.departures.length === 0) {
            departuresContent += '<div class="p-4 details-container" style="color: black;"><p>No departures available...</p></div>';
        } else {
            data.departures.forEach((departure, index) => {
                departuresContent += `
                <div class="bg-white shadow overflow-hidden sm:rounded-lg">
                    <ul class="divide-y divide-gray-200">
                        <li class="p-4 hover:bg-gray-50">
                            <div onclick="toggleDropdown('departure-${index}')" class="cursor-pointer">
                                <div class="flex items-center justify-between">
                                    <p class="text-sm font-medium text-indigo-600 truncate"><strong>${departure.callsign}</strong> - ${departure.departure} <i class="fa-solid fa-arrow-right"></i> ${departure.arrival}</p>
                                    <div class="ml-2 flex-shrink-0 flex">
                                        <p class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Details</p>
                                    </div>
                                </div>
                                    <div id="departure-${index}" class="hidden mt-4">
                                    <p><i class="fas fa-plane"></i> Aircraft: ${departure.aircraft}</p>
                                    <p><i class="fas fa-arrows-alt-v"></i> Altitude: ${departure.altitude} ft</p>
                                    <p><i class="fas fa-tachometer-alt"></i> Cruise Speed: ${departure.cruise_speed} knots</p>
                                    <p><i class="fas fa-route"></i> Route: ${departure.route}</p>
                                    <p>Remaining: ${departure.distanceRemaining}</p>

                                </div>
                            
                            </div>
                        </li>
                    </ul>
                </div>`;
            });
        }
        departuresContent += '</div>'; // Close the div that sets the fixed height and overflow


        // Initialize airport details content
        var detailsContent = `
            <div class="p-4 details-container" style="color: black;">
                <p><strong><i class="fa-solid fa-signature"></i></strong> ${data.airportName}</p>
                <hr>
                <p><strong><i class="fa-solid fa-passport"></i></strong> ${data.airportIdent}</p>
                <hr>
                <p><strong><i class="fa-solid fa-location-dot"></i></i></strong> ${data.airportRegion}</p>
                <hr>
                <p><strong><i class="fa-solid fa-clock"></i></strong> ${data.airportLocalTime}</p>
                <hr>
                <p><strong><i class="fa-solid fa-plane-arrival"></i></strong> ${countOfArrivals}</p>
                <p><strong><i class="fa-solid fa-plane-departure"></i></strong> ${countOfDepartures}</p>
            </div>
        `;


        // Populate the tabs with the fetched data
        document.getElementById("details").innerHTML = detailsContent;
        document.getElementById("arrivals").innerHTML = arrivalsContent;
        document.getElementById("departures").innerHTML = departuresContent;


        // Show the airport card
        document.getElementById("airport-card").style.display = "block";
    });
}

function fetchAirportLocalTime(airportIdent) {
    var url = `api/airport_local_time/${airportIdent}/`; // Adjust the URL as per your actual API endpoint

    fetch(url)
    .then(response => response.json())
    .then(data => {
        document.querySelector(".details-container .local-time").textContent = `Local Time: ${data.localTime}`;
    })
    .catch(error => console.error('Error fetching local time:', error));
}

// This function sets up the periodic update
function setupLiveTimeUpdate(airportIdent, interval) {
    // Immediately update the time once
    fetchAirportLocalTime(airportIdent);

    // Set up the interval for live updating
    setInterval(() => {
        fetchAirportLocalTime(airportIdent);
    }, interval); // interval in milliseconds, e.g., 60000 for 1 minute
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
