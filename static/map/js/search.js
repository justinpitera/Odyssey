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
            Promise.all([
                fetch(`/map/api/search-airports/?query=${encodeURIComponent(searchValue)}`) // Original search endpoint
                    .then(response => response.json()),
                fetch(`/map/api/vatsim-data/`) // Your VATSIM data endpoint
                    .then(response => response.json())
            ]).then(([originalResults, vatsimData]) => {
                const vatsimResults = vatsimData.filter(pilot => pilot.name.includes(searchValue) || pilot.callsign.includes(searchValue) || pilot.cid.toString().includes(searchValue));
                lastSearchResults = [...originalResults, ...vatsimResults.map(pilot => ({ 
                    name: pilot.callsign, 
                    // These are reversed in the zoomToLocation function
                    lat: pilot.longitude, 
                    lon: pilot.latitude, 
                    
                    type: 'vatsim' 
                }))];
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
                const iconClass = result.type === 'airport' ? 'fa-tower' : (result.type === 'vatsim' ? 'fa-plane' : 'fa-helipad');
                // Create an icon element
                const icon = document.createElement('i');
                icon.className = `fas ${iconClass}`;
                icon.style.marginRight = '8px'; // Add some spacing between the icon and text
        
                // Modify textContent to exclude ident for type 'vatsim'
                const textContent = result.type === 'vatsim' 
                    ? `${result.name} (VATSIM)` // Exclude ident for vatsim type
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
                    if (result.lat && result.lon) {
                        zoomToLocation(result.lat, result.lon);
                        fetchAirportDetails(result.ident); 
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
