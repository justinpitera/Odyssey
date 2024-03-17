// Assuming mapboxgl has been initialized and the map is created

// Initialize objects to keep track of markers and GeoJSON features
const ivaoMarkers = {};
const ivaoGeoJSON = {};
const activeIVAOPopups = {};

let currentSelectedIVAOPilotId = null;

const ivaoWaypointMarkers = [];


let ivaoFilterEnabled = false;

function fetchAndUpdateIVAOPilotsDirectly() {
    fetch('api/ivao-data/')  // Update this URL to your IVAO data endpoint
        .then(response => response.json())
        .then(data => {
            const pilots = data.pilots;
            if (ivaoFilterEnabled) {
                updateMapWithIVAOPilots(pilots);
            }

        })
        .catch(err => console.error('Error fetching IVAO data:', err));
}

function updateMapWithIVAOPilots(pilots) {
    pilots.forEach(pilot => {
        const pilotId = `ivao-pilot-${pilot.userId}`;
        const markerLngLat = [pilot.longitude, pilot.latitude];

        if (!ivaoMarkers[pilotId]) {
            const el = document.createElement('div');
            el.className = 'ivao-marker';
            ivaoMarkers[pilotId] = new mapboxgl.Marker(el)
                .setLngLat(markerLngLat)
                .addTo(map);
        } else {
            ivaoMarkers[pilotId].setLngLat(markerLngLat);
        }

        ivaoGeoJSON[pilotId] = {
            type: 'Feature',
            geometry: {
                type: 'Point',
                coordinates: markerLngLat
            },
            properties: {
                id: pilotId,
                icon: 'ivao-icon',
                name: pilotId,
                groundspeed: pilot.speed,
                altitude: pilot.altitude,
                callsign: pilotId,
                heading: getTrueHeading(pilot.heading)
            }
        };
    });

    if (map.getSource('ivao')) {
        map.getSource('ivao').setData({
            type: 'FeatureCollection',
            features: Object.values(ivaoGeoJSON)
        });
    } else {
        map.addSource('ivao', {
            type: 'geojson',
            data: {
                type: 'FeatureCollection',
                features: Object.values(ivaoGeoJSON)
            }
        });

        map.addLayer({
            id: 'ivao-markers',
            type: 'symbol',
            source: 'ivao',
            layout: {
                'icon-image': 'ivao-icon',
                'icon-rotate': ['get', 'heading'],
                'icon-allow-overlap': true,
                'icon-size': 0.045
            }
        });
    }
}

// Assuming getTrueHeading is defined similarly and can be shared or duplicated

const ivaoIconId = 'ivao-icon';
const ivaoImageUrl = '/static/images/location-arrow-ivao.png';

function startIVAOImage() {
    if (!map.hasImage(ivaoIconId)) {
        map.loadImage(ivaoImageUrl, function(error, image) {
            if (error) throw error;
            map.addImage(ivaoIconId, image);
            fetchAndUpdateIVAOPilotsDirectly();
        });
    } else {
        fetchAndUpdateIVAOPilotsDirectly();
    }
}


document.addEventListener('DOMContentLoaded', function() {
    const ivaoFilterCheckbox = document.getElementById('ivaoFilter');

    // Function to set a cookie
    function setCookie(name, value, days) {
        let expires = "";
        if (days) {
            let date = new Date();
            date.setTime(date.getTime() + (days*24*60*60*1000));
            expires = "; expires=" + date.toUTCString();
        }
        document.cookie = name + "=" + (value || "")  + expires + "; path=/";
    }

    // Function to get a cookie
    function getCookie(name) {
        let nameEQ = name + "=";
        let ca = document.cookie.split(';');
        for(let i=0;i < ca.length;i++) {
            let c = ca[i];
            while (c.charAt(0)==' ') c = c.substring(1,c.length);
            if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
        }
        return null;
    }

    // Read the cookie on page load and update checkbox state
    let ivaoFilterState = getCookie('ivaoFilterEnabled');
    if (ivaoFilterState !== null) {
        ivaoFilterEnabled = ivaoFilterState === 'true';
        ivaoFilterCheckbox.checked = ivaoFilterEnabled;
    } else {
        // If no cookie is found, default to false or any desired default state
        ivaoFilterEnabled = false;
        ivaoFilterCheckbox.checked = false;
    }

    // Add event listener to the IVAO filter checkbox
    ivaoFilterCheckbox.addEventListener('change', function() {
        ivaoFilterEnabled = this.checked;
        setCookie('ivaoFilterEnabled', ivaoFilterEnabled, 7); // Store choice for 7 days

        if (ivaoFilterEnabled) {
            fetchAndUpdateIVAOPilotsDirectly();
        } else {
            removeIVAODataFromMap();
        }
    });

    // Assuming mapboxgl has been initialized and the map is created here or elsewhere before this script runs
    
    // Ensure 'startIVAOImage' is called when the map loads
    map.on('load', startIVAOImage);
    
    // Adjust the setInterval as necessary
    setInterval(() => {
        if (ivaoFilterEnabled) {
            fetchAndUpdateIVAOPilotsDirectly();
        }
    }, 30000);

    // Rest of your original code...
});

function removeIVAODataFromMap() {
    // Check if the map has the IVAO source and layer, then remove them
    if (map.getSource('ivao')) {
        map.removeLayer('ivao-markers');
        map.removeSource('ivao');
    }

    // Additionally, remove any markers if they are not managed by the Mapbox GL JS layer
    Object.values(ivaoMarkers).forEach(marker => marker.remove());
    ivaoMarkers = {}; // Reset the ivaoMarkers object
}

