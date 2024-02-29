mymap.removeControl(mymap.zoomControl);
// Listen for when the map stops moving
mymap.on('moveend', function() {
    let center = mymap.getCenter();
    let newLng = center.lng;

    // Assuming a standard web Mercator projection where longitude ranges from -180 to 180
    if (center.lng < -180) {
        newLng = 180 + (center.lng + 180); // If they cross the left edge, appear on the right
    } else if (center.lng > 180) {
        newLng = -180 + (center.lng - 180); // If they cross the right edge, appear on the left
    }

    // If adjustment is needed, set the new center
    if (center.lng !== newLng) {
        mymap.panTo([center.lat, newLng]);
    }
});

function rotateMap() {
    map.rotate(30); // Rotate the map by 30 degrees clockwise
}

// Modified tile layer with noWrap set to false
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18,
    noWrap: true // Set noWrap to false to allow the tiles to repeat indefinitely
}).addTo(mymap);

// Disable right-click context menu on the map
mymap.getContainer().addEventListener('contextmenu', function(e) {
    e.preventDefault();
});

// Customizing the cluster group with a specified maxClusterRadius
var markerClusterGroup = L.markerClusterGroup({
    maxClusterRadius: 5, // Adjust clustering tolerance (in pixels)
    iconCreateFunction: function(cluster) {
        return L.divIcon({ className: 'transparent-cluster-icon' }); // Custom class for transparent cluster icon
    }
});

// Optionally, set the map's minZoom and maxBounds to improve the user experience
mymap.setMinZoom(3); // Example: Set a minimum zoom level to prevent too much zooming out
// Setting maxBounds can be complex as it depends on your specific needs. It may be left unset for full world exploration.

map.on('rotate', () => {
    Object.keys(aircraftMarkers).forEach(flight_number => {
      const markerObj = aircraftMarkers[flight_number];
      if (markerObj) {
        updateIconRotation(markerObj.marker.getElement(), markerObj.heading);
      }
    });
  });