let trackingMode = {
    enabled: false,
    type: null, // 'vatsim' or 'ivao'
    identifier: null // unique identifier for the user
};

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const resultsDiv = document.getElementById('search-results');
    let lastSearchResults = []; // Store the last search results

    searchInput.addEventListener('keyup', function(e) {
        const searchValue = e.target.value.trim();

        if (e.keyCode === 13) { // Check if Enter was pressed
            if (lastSearchResults.length > 0) {
                const firstResult = lastSearchResults[0];
                searchInput.value = firstResult.name; // Fill the search input with the first result
                resultsDiv.style.display = 'none'; // Hide the results div
                if (firstResult.lat && firstResult.lon) {
                    zoomToLocation(firstResult.lat, firstResult.lon); 
                }
            }
            return; // Prevent further execution when Enter is pressed
        }

        if (searchValue.length > 2) { // Optional: start searching after 2 characters
            // Added fetch call for ivao data
            Promise.all([
                fetch(`/map/search_airports/?query=${encodeURIComponent(searchValue)}`)
                    .then(response => response.json()),
                fetch(`/map/api/vatsim_network/`)
                    .then(response => response.json()),
                fetch(`/map/api/ivao_network/`)
                    .then(response => response.json())
            ]).then(([originalResults, vatsimData, ivaoData]) => {
                    const vatsimResults = vatsimData.pilots.filter(pilot => pilot.name.includes(searchValue) || pilot.callsign.includes(searchValue) || pilot.cid.toString().includes(searchValue))
                    .map(pilot => ({ 
                        cid: pilot.cid,
                        name: pilot.callsign, 
                        lat: pilot.longitude, 
                        lon: pilot.latitude, 
                        arrivalAirport: pilot.flight_plan ? pilot.flight_plan.arrival : "Unknown", // Check if flight_plan exists
                        type: 'vatsim' 
                    }));
            
        
                // Process ivao data
                const ivaoResults = ivaoData.pilots.filter(pilot => pilot.callsign.includes(searchValue))
                    .map(pilot => ({
                        userId: pilot.userId,
                        name: pilot.callsign,
                        lat: pilot.latitude,
                        lon: pilot.longitude,
                        arrivalAirport: pilot.arrival,
                        type: 'ivao'
                    }));
        
                // Combine all results
                lastSearchResults = [...originalResults, ...vatsimResults, ...ivaoResults];
                displaySearchResults(lastSearchResults);
            }).catch(error => console.error('Error fetching search results:', error));
        } else {
            resultsDiv.style.display = 'none'; // Hide the results div if search input is cleared or too short
            lastSearchResults = []; // Clear last search results
        }        
    });

    function displaySearchResults(results) {
        resultsDiv.innerHTML = ''; // Clear existing results
        if (results.length > 0) {
            results.forEach(result => {
                const div = document.createElement('div');
                // Determine the icon based on the result type
                const iconClass = result.type === 'airport' ? 'fa-tower' : (result.type === 'vatsim' || result.type === 'ivao' ? 'fa-plane' : 'fa-helipad');
                // Create an icon element
                const icon = document.createElement('i');
                icon.className = `fas ${iconClass}`;
                icon.style.marginRight = '8px'; // Add some spacing between the icon and text
        
                const textContent = result.type === 'vatsim' || result.type === 'ivao'
                ? `${result.name} (${result.type.toUpperCase()})` // Dynamically label as VATSIM or IVAO based on type
                : `${result.ident} - ${result.name}`; // Include ident for other types
            
                const textNode = document.createTextNode(textContent);
        
                div.appendChild(icon);
                div.appendChild(textNode);
        
                div.style.padding = '10px';
                div.style.borderBottom = '1px solid #eee';
                div.style.cursor = 'pointer';
                div.onclick = function() {
                    searchInput.value = result.name; // Use name for selection
                    resultsDiv.style.display = 'none';
                    if (result.type === 'vatsim' ) {
                        zoomToLocation(result.lat, result.lon);
                        fetchAirportDetails(result.arrivalAirport);
                        // // Enable tracking mode
                        // trackingMode = {
                        //     enabled: true,
                        //     type: result.type,
                        //     identifier: result.cid // Assuming the callsign is a unique identifier
                        // };
                        // // Initiate tracking
                        // trackUserOnMap();
                    } else if (result.type === 'ivao' ) {
                        zoomToLocation(result.lon, result.lat);
                        fetchAirportDetails(result.arrivalAirport);
                        // // Enable tracking mode
                        // trackingMode = {
                        //     enabled: true,
                        //     type: result.type,
                        //     identifier: result.userId // Assuming the callsign is a unique identifier
                        // };
                        // // Initiate tracking
                        // trackUserOnMap();
                    } else {
                        zoomToLocation(result.lat, result.lon);
                    }
                };                
                resultsDiv.appendChild(div);
            });
            resultsDiv.style.display = 'block';
        } else {
            resultsDiv.style.display = 'none';
        }
    }
});

function zoomToLocation(lat, lng) {
    map.flyTo({
        center: [lat, lng],
        essential: true, // this animation is considered essential with respect to prefers-reduced-motion
        zoom: 13
    });
    
}

document.getElementById('clear-input').addEventListener('click', function() {
    const resultsDiv = document.getElementById('search-results');
    document.getElementById('search-input').value = ''; // Clear the input field
    document.getElementById('search-input').focus();
    resultsDiv.style.display = 'none'; // Set focus back to the input field
});

function trackUserOnMap() {
    if (!trackingMode.enabled) return; // Exit if tracking mode is not enabled

    // Example endpoint, replace with actual API URL and parameters
    const apiUrl = `/map/api/${trackingMode.type}-dataView/`;
    fetch(`${apiUrl}?identifier=${encodeURIComponent(trackingMode.identifier)}`)
        .then(response => response.json())
        .then(data => {
            // Assuming data contains latitude and longitude
            const { lat, lon } = data.location; // Adjust according to the actual data structure
            zoomToLocation(lon, lat);
        })
        .catch(error => console.error('Error updating user location:', error));

    // Repeat the tracking process every X seconds
    setTimeout(trackUserOnMap, 40000); // Adjust the timeout as needed
}
