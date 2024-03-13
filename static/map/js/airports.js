let markers = []; // Store marker instances
let markersData = []; // Store fetched data for reuse

function updateAirportMarkers() {
  const currentZoom = map.getZoom();
  markers.forEach((marker) => marker.remove()); // Remove all markers
  markers = []; // Clear markers array

  markersData.forEach((airport) => {
    // Since the backend already filters the airports based on the zoom level,
    // there's no need for further checks here.
    // Simply create and add markers for the airports received.
    createAndAddMarker(airport);
  });
}

function createAndAddMarker(airport) {
  var el = document.createElement("div");
  el.className = "marker";
  // Assign icon based on airport type
  if (airport.type === "large_airport") {
    el.innerHTML =
      '<i class="fa-solid fa-tower-control" style="color: gray; font-size: 20px; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0px 0px 6px #000;"></i>';
  } else if (airport.type === "medium_airport") {
    el.innerHTML =
      '<i class="fa-solid fa-tower-control" style="color: gray; font-size: 20px; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0px 0px 6px #000;"></i>';
  } else if (airport.type === "heliport") {
    el.innerHTML =
      '<i class="fa-solid fa-helicopter-symbol" style="color: #013220; font-size: 14px; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0px 0px 6px #000;"></i>';
  } else if (airport.type === "small_airport") {
    el.innerHTML =
      '<i class="fa-solid fa-tower-control" style="color: gray; font-size: 14px; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0px 0px 6px #000;"></i>';
  }

  var marker = new mapboxgl.Marker(el)
    .setLngLat(
      airport.coordinates.split(",").map((coord) => parseFloat(coord.trim())),
    )
    .addTo(map);

  marker.getElement().addEventListener("click", function () {
    fetchAirportDetails(airport.ident);
  });

  markers.push(marker); // Track this marker
}

function fetchAirportDetails(airportIdent) {
// Show the airport card with loading indicators
  document.getElementById("airport-card").style.display = "block";
  document.getElementById("details").innerHTML = '<div class="loading p-4 details-container" style="color: black;"><p>Loading airport details...</p></div>'
  document.getElementById("arrivals").innerHTML = '<div class="loading p-4 details-container" style="color: black;"><p>Loading arrivals...</p></div>';
  document.getElementById("departures").innerHTML = '<div class="loading p-4 details-container" style="color: black;"><p>Loading departures...</p></div>';
  document.querySelector(".max-w-2xl .text-2xl").textContent = "Loading..."
  var url = `api/airport_details/${airportIdent}/`;

  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      // Set the airport name
      document.querySelector(".max-w-2xl .text-2xl").textContent =
        data.airportName;

      // Initialize arrivals content with a surrounding div that has a fixed height and overflow-auto
      var arrivalsContent = '<div class="max-h-96 overflow-auto space-y-4">'; // Added space-y-4 for spacing between cards
      var countOfArrivals = 0;
      var countOfDepartures = 0;
      if (data.arrivals.length === 0) {
        arrivalsContent +=
          '<div class="p-4 details-container" style="color: black;"><p>No arrivals available...</p></div>';
      } else {
        countOfArrivals = data.arrivals.length;
        countOfDepartures = data.departures.length;

        data.arrivals.forEach((arrival, index) => {
          arrivalsContent += `
                <div class="bg-white shadow overflow-hidden sm:rounded-lg">
                    <div class="p-4">
                        <div class="flex items-center justify-between mb-4">
                            <p class="text-lg font-semibold text-indigo-600" onclick="zoomToLocation(${arrival.latitude}, ${arrival.longitude})"><strong>${arrival.callsign}</strong></p>
                            <p class="px-3 py-1 text-xs leading-5 font-semibold rounded-full bg-gray-100 text-blue-500">${arrival.airline}</p>
                        </div>
                        <div class="flex items-start">
                            <i class="fas fa-plane text-2xl text-gray-800"></i>
                            <div class="ml-4">
                                <p class="text-xl font-medium text-gray-800">${arrival.aircraft}</p>
                                <p class="text-md text-gray-700">Cruise Speed: <span class="font-semibold">${arrival.cruise_speed} knots</span>, Altitude: <span class="font-semibold">${arrival.altitude} ft</span></p>
                            </div>
                        </div>
                        <div class="flex items-center justify-between space-x-4">
                            
                        <!-- Flight start icon with progress bar and flight end icon -->
                        <div class="flex items-center flex-1">
                        <div class="relative">
                            <small class="absolute top-[-10px]">${arrival.departure}</small>
                            <small>${arrival.departureTime}</small>
                        </div>
                            <!-- Progress bar container -->
                            <div class="flex-1 mx-4 bg-gray-200 rounded-full h-2.5">
                                <!-- Progress indicator -->
                                <div class="bg-blue-600 h-2.5 rounded-full" style="width: ${100 - arrival.distanceRemaining}%"></div>
                            </div>
                            <div class="relative">
                                <small class="absolute top-[-10px]">${arrival.arrival}</small>
                                <small>${arrival.arrivalTime}</small> 
                            </div>
                        </div>
                    </div>
                        <div class="mt-4">
                            <p class="text-sm text-gray-700">Route:</p>
                            <p class="text-md font-semibold text-gray-900">${arrival.route}</p>
                        </div>
                    </div>
                </div>`;
        });
      }
      arrivalsContent += "</div>"; // Close the div that sets the fixed height and overflow

      // Initialize departures content with similar changes as arrivals
      var departuresContent = '<div class="max-h-96 overflow-auto space-y-4">';
      if (data.departures.length === 0) {
        departuresContent +=
          '<div class="p-4 details-container" style="color: black;"><p>No departures available...</p></div>';
      } else {
        data.departures.forEach((departure, index) => {
          departuresContent += `
                <div class="bg-white shadow overflow-hidden sm:rounded-lg">
                    <div class="p-4">
                        <div class="flex items-center justify-between mb-4">
                            <p class="text-lg font-semibold text-indigo-600"><strong>${departure.callsign}</strong></p>
                            <p class="px-3 py-1 text-xs leading-5 font-semibold rounded-full bg-gray-100 text-blue-500">${departure.airline}</p>
                        </div>
                        <div class="flex items-start">
                            <i class="fas fa-plane text-2xl text-gray-800"></i>
                            <div class="ml-4">
                                <p class="text-xl font-medium text-gray-800">${departure.aircraft}</p>
                                <p class="text-md text-gray-700">Cruise Speed: <span class="font-semibold">${departure.cruise_speed} knots</span>, Altitude: <span class="font-semibold">${departure.altitude} ft</span></p>
                            </div>
                        </div>
                        <div class="flex items-center justify-between space-x-4">
                            
                        <!-- Flight start icon with progress bar and flight end icon -->
                        <div class="flex items-center flex-1">
                        <div class="relative">
                            <small class="absolute top-[-10px]">${departure.departure}</small>
                            <small>${departure.departureTime}</small>
                        </div>
                            <!-- Progress bar container -->
                            <div class="flex-1 mx-4 bg-gray-200 rounded-full h-2.5">
                                <!-- Progress indicator -->
                                <div class="bg-blue-600 h-2.5 rounded-full" style="width: ${100 - departure.distanceRemaining}%"></div>
                            </div>
                            <div class="relative">
                                <small class="absolute top-[-10px]">${departure.arrival}</small>
                                <small>${departure.arrivalTime}</small> 
                            </div>
                        </div>
                    </div>
                        <div class="mt-4">
                            <p class="text-sm text-gray-700">Route:</p>
                            <p class="text-md font-semibold text-gray-900">${departure.route}</p>
                        </div>
                    </div>
                </div>`;
        });
      }
      departuresContent += "</div>"; // Close the div that sets the fixed height and overflow

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

    });
}

function fetchAirportLocalTime(airportIdent) {
  var url = `api/airport_local_time/${airportIdent}/`;

  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      document.querySelector(".details-container .local-time").textContent =
        `Local Time: ${data.localTime}`;
    })
    .catch((error) => console.error("Error fetching local time:", error));
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
  if (element.classList.contains("hidden")) {
    element.classList.remove("hidden");
  } else {
    element.classList.add("hidden");
  }
}

function fetchAndDisplayAirports() {
  var bounds = map.getBounds();
  var zoomLevel = map.getZoom();

  // Include zoom level in the request
  var url = `api/airports/?northBound=${bounds.getNorth()}&southBound=${bounds.getSouth()}&eastBound=${bounds.getEast()}&westBound=${bounds.getWest()}&zoom=${zoomLevel}`;

  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      markersData = data.airports; // Update the markersData with the fetched data
      updateAirportMarkers(); // Update markers based on new data
    });
}

// Initial fetch
fetchAndDisplayAirports();

// Update markers on map move or zoom
map.on("moveend", fetchAndDisplayAirports);
map.on("zoomend", fetchAndDisplayAirports);

// Close airport card when clicking close button
document
  .getElementById("close-card-btn")
  .addEventListener("click", function () {
    document.getElementById("airport-card").style.display = "none";
  });
