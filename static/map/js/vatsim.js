// Assuming mapboxgl has been initialized and the map is created

// Initialize an object to keep track of vatsimMarkers by cid
const vatsimMarkers = {};

// Function to create an SVG element with rotation and drop shadow
function createRotatedSvg(heading) {
    const shadowFilter = `
        <filter id="dropshadow" height="130%">
            <feGaussianBlur in="SourceAlpha" stdDeviation="3"/>
            <feOffset dx="2" dy="2" result="offsetblur"/>
            <feComponentTransfer>
                <feFuncA type="linear" slope="0.5"/>
            </feComponentTransfer>
            <feMerge> 
                <feMergeNode/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
    `;
    const svgPath = `M429.6 92.1c4.9-11.9 2.1-25.6-7-34.7s-22.8-11.9-34.7-7l-352 144c-14.2 5.8-22.2 20.8-19.3 35.8s16.1 25.8 31.4 25.8H224V432c0 15.3 10.8 28.4 25.8 31.4s30-5.1 35.8-19.3l144-352z`;

    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512" width="50" height="50">
                <defs>
                    ${shadowFilter}
                </defs>
                <path d="${svgPath}" transform="translate(112, 128) rotate(${heading}, 112, 128) scale(0.25)" fill="#000" />
                <path d="${svgPath}" transform="translate(112, 128) rotate(${heading}, 112, 128) scale(0.25)" fill="#00ffff"/>
            </svg>`;
}

// Check if Web Workers are supported
if (window.Worker) {
    const vatsimWorker = new Worker('/static/map/js/vatsimWorker.js');

    vatsimWorker.addEventListener('message', function(e) {
        const { pilots } = e.data;
        updateMapWithPilots(pilots);
    });

    function updatePilots() {
        let currentBounds = map.getBounds().toArray();
        // Expand the bounds by a certain percentage, for example, 10%
        let expansionRatio = 0.1;
        let latDiff = (currentBounds[1][1] - currentBounds[0][1]) * expansionRatio;
        let lngDiff = (currentBounds[1][0] - currentBounds[0][0]) * expansionRatio;
        // Expanded bounds
        let expandedBounds = [
            [currentBounds[0][0] - lngDiff, currentBounds[0][1] - latDiff], // Southwest corner
            [currentBounds[1][0] + lngDiff, currentBounds[1][1] + latDiff]  // Northeast corner
        ];
        vatsimWorker.postMessage({ action: 'updatePilots', mapBounds: expandedBounds });
    }    
} else {
    console.log('Web Workers are not supported in your browser.');
}

function updateMapWithPilots(pilots) {
    const bounds = map.getBounds(); // Get the current bounds of the map viewport

    pilots.forEach(pilot => {
        const pilotId = `pilot-${pilot.cid}`;
        const markerLngLat = [pilot.longitude, pilot.latitude];

        // Create or update marker
        if (!vatsimMarkers[pilotId]) {
            // Create marker if not already present
            const el = document.createElement('div');
            el.innerHTML = createRotatedSvg(pilot.heading);
            el.firstChild.style.display = 'block';

            const popup = new mapboxgl.Popup({ offset: 25 });

            const marker = new mapboxgl.Marker(el)
                .setLngLat(markerLngLat)
                .setPopup(popup)
                .addTo(map);

            vatsimMarkers[pilotId] = { marker, popup };
        } else {
            // Update marker if already present
            const marker = vatsimMarkers[pilotId].marker;
            const el = document.createElement('div');
            el.innerHTML = createRotatedSvg(pilot.heading);
            marker.getElement().replaceChild(el.firstChild, marker.getElement().firstChild);
            marker.setLngLat(markerLngLat);
        }

        // Update popup if marker is within the viewport
        if (bounds.contains(markerLngLat)) {
            const popup = vatsimMarkers[pilotId].popup;
            popup.setHTML(`
                Name: ${pilot.name}<br>
                Speed: ${pilot.groundspeed} kts<br>
                Altitude: ${pilot.altitude} ft<br>
                Location: ${pilot.latitude.toFixed(2)}, ${pilot.longitude.toFixed(2)}
            `);
        }
    });
}




// Initial update
updatePilots();

// Update pilots every 15 seconds
setInterval(updatePilots, 15000);
