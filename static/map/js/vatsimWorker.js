self.addEventListener('message', function(e) {
    const { action, mapBounds } = e.data;
    if (action === 'updatePilots') {
        fetch('/map/api/fetch_flight_data/')
            .then(response => response.json())
            .then(data => {
                const pilots = data.pilots;
                // Process data here (e.g., filter by mapBounds, create SVGs)
                // For simplicity, we'll just send back the raw pilots data
                self.postMessage({ pilots });
            })
            .catch(err => console.log('Error fetching VATSIM data:', err));
    }
});
