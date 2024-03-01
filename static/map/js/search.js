document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const resultsDiv = document.getElementById('search-results');
    let lastSearchResults = []; // Store the last search results

    searchInput.addEventListener('keyup', function(e) {
        const searchValue = e.target.value;

        if (e.keyCode === 13) { // Check if Enter was pressed
            if (lastSearchResults.length > 0) {
                const firstResult = lastSearchResults[0];
                searchInput.value = firstResult.name; // Fill the search input with the first result
                resultsDiv.style.display = 'none'; // Hide the results div
                console.log(firstResult.lat, firstResult.lon);
                zoomToLocation(firstResult.lat, firstResult.lon); // Zoom to the first search result location
            }
            return; // Prevent further execution when Enter is pressed
        }

        if (searchValue.length > 2) { // Optional: start searching after 2 characters
            fetch(`/map/search-airports/?query=${encodeURIComponent(searchValue)}`)
                .then(response => response.json())
                .then(data => {
                    lastSearchResults = data; // Update the last search results
                    displaySearchResults(data);
                })
                .catch(error => console.error('Error fetching search results:', error));
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
                const iconClass = result.type === 'airport' ? 'fa-tower' : 'fa-helipad'; // Adjust these class names based on actual Font Awesome classes
                // Create an icon element
                const icon = document.createElement('i');
                icon.className = `fas ${iconClass}`; // Ensure you have the correct Font Awesome prefix and icon classes
                icon.style.marginRight = '8px'; // Add some spacing between the icon and text
    
                // Combine icon and text in a div
                div.appendChild(icon);
                const textNode = document.createTextNode(`${result.name} - ${result.municipality}`);
                div.appendChild(textNode);
    
                div.style.padding = '10px';
                div.style.borderBottom = '1px solid #eee';
                div.style.cursor = 'pointer';
                div.onclick = function() {
                    searchInput.value = result.name;  // Fill the search input with the selected result
                    resultsDiv.style.display = 'none';  // Hide the results div
                    console.log(result.lat, result.lon);
                    zoomToLocation(result.lat, result.lon);  // Zoom to the selected location
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
