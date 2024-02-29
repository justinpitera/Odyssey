const aircraftMarkers = {};
let playerAircraftAdded = false;

function updateAircraftPositions() {
  fetchAircraftPositions()
    .then(updateMarkers)
    .catch(error => console.error('Error updating aircraft positions:', error));
}

function fetchAircraftPositions() {
  return fetch('/map/api/aircraft/telemetry')
    .then(response => response.json())
    .then(data => data.flights)
    .catch(error => console.error('Error fetching aircraft positions:', error));
}

function updateMarkers(newAircraftPositions) {
  newAircraftPositions.forEach(updateOrAddMarker);
}

function updateOrAddMarker(newAircraftPosition) {
  const isPlayerAircraft = !playerAircraftAdded;
  const aircraftHtml = getAircraftIconHtml(newAircraftPosition.heading, isPlayerAircraft);

  if (aircraftMarkers[newAircraftPosition.flight_number]) {
    updateExistingMarker(aircraftMarkers[newAircraftPosition.flight_number], newAircraftPosition);
  } else {
    addNewMarker(newAircraftPosition, isPlayerAircraft);
    if (isPlayerAircraft) playerAircraftAdded = true;
  }
}


// Future modification: put this in the template so the user can select the aircraft and color
function getAircraftIconHtml(heading, isPlayerAircraft = false) {
  const color = isPlayerAircraft ? 'orange' : 'gray';
  const size = isPlayerAircraft ? 25 : 20;
  return `<i class="fa-solid fa-location-arrow-up" style="transform: rotate(${heading}deg); color: ${color}; font-size:${size}px; text-shadow: 4px 4px 8px rgba(0,0,0,0.5); -webkit-text-stroke: 2px black; text-stroke: 2px black;"></i>`;

}

function updateExistingMarker(markerObj, position) {
  markerObj.marker.setLngLat([position.longitude, position.latitude]);
  markerObj.marker.getElement().innerHTML = getAircraftIconHtml(position.heading, markerObj.isPlayer);
}
function updateIconRotation(el, aircraftHeading) {
  // Get the current bearing of the map
  const mapBearing = map.getBearing();

  // The desired rotation of the marker is the negative of the map's bearing plus the aircraft's heading.
  // This ensures the marker remains oriented to the earth, not the map's rotation.
  const rotation = aircraftHeading - mapBearing;

  // Update the marker's rotation. Ensure the rotation is applied around the center of the marker.
  el.style.transform = `rotate(${rotation}deg)`;
  el.style.transformOrigin = 'center';
}



function addNewMarker(position, isPlayerAircraft = false) {
  const el = document.createElement('div');
  el.className = 'aircraft-marker'; // Add a class for easier CSS targeting if needed
  el.innerHTML = getAircraftIconHtml(position.heading, isPlayerAircraft);

  const newMarker = new mapboxgl.Marker(el)
    .setLngLat([position.longitude, position.latitude])
    .setPopup(new mapboxgl.Popup().setHTML(getPopupContent(position))) // Use setHTML here
    .addTo(map);

  // Store the marker with its initial heading
  aircraftMarkers[position.flight_number] = { marker: newMarker, isPlayer: isPlayerAircraft, heading: position.heading };

  // Initial rotation adjustment
  updateIconRotation(el, position.heading);
}



/**
 * Creates HTML content for an aircraft's popup with flight and position details.
 * @param {Object} position Position and flight details for the aircraft.
 * @returns {string} HTML content for the popup.
 */
function getPopupContent(position) {
  return `Flight Number: ${position.flight_number}<br>` +
         `Altitude: ${position.altitude} feet<br>` +
         `Latitude: ${position.latitude}<br>` +
         `Longitude: ${position.longitude}`;
}



let isMapRotated = false; // Tracks the state of map rotation

document.getElementById('toggle-rotation').addEventListener('click', toggleMapRotation);


function toggleMapRotation() {
  const playerAircraftKey = Object.keys(aircraftMarkers).find(key => aircraftMarkers[key].isPlayer);
  const playerAircraftMarker = aircraftMarkers[playerAircraftKey];

  if (playerAircraftMarker) {
    const position = playerAircraftMarker.marker.getLngLat();
    const currentHeading = playerAircraftMarker.heading;

    if (isMapRotated) {
      // Reset map rotation, zoom, and pitch to default values
      map.flyTo({
        center: position,
        zoom: 10, // Set to your default zoom level
        pitch: 0, // Reset pitch to 0 for a straight down view
        bearing: 0, // Reset bearing to north
        duration: 1000
      });
      isMapRotated = false;
    } else {
      // Rotate map to match aircraft's heading, zoom in, and adjust pitch for better view
      map.flyTo({
        center: position,
        zoom: 10, // Zoom in closer
        pitch: 45, // Tilt the map for a more three-dimensional perspective
        bearing: currentHeading, // Rotate map to match aircraft's heading
        duration: 1000
      });
      isMapRotated = true;
    }
  }
}


function continuouslyFollowAircraft() {
  if (isMapRotated) {
    const playerAircraftKey = Object.keys(aircraftMarkers).find(key => aircraftMarkers[key].isPlayer);
    const playerAircraftMarker = aircraftMarkers[playerAircraftKey];
    if (playerAircraftMarker) {
      const position = playerAircraftMarker.marker.getLngLat();
      const currentHeading = playerAircraftMarker.heading;

      map.flyTo({
        center: position,
        zoom: 10, // Adjust as needed for the best view
        pitch: 45, // Adjust as needed
   
        bearing: currentHeading,
        essential: true, // This ensures the map moves even if the user hasn't interacted with the map recently
        duration: 1000
      });
    }
  }
}

// Update this to your existing interval, or create a new one
setInterval(continuouslyFollowAircraft, 1000); 
// Assuming `map` is your Mapbox GL JS map instance
setInterval(updateAircraftPositions, 1000);
map.on('rotate', () => {
  Object.keys(aircraftMarkers).forEach(flight_number => {
    const markerObj = aircraftMarkers[flight_number];
    if (markerObj) {
      updateIconRotation(markerObj.marker.getElement(), markerObj.heading);
    }
  });
});
