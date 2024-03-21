self.addEventListener('message', function(e) {
    const { action, mapBounds } = e.data;
    if (action === 'updatePilots') {
        // Define both fetch requests
        const fetchVATSIM = fetch('/map/api/vatsim_network/').then(response => response.json());
        const fetchIVAO = fetch('/map/api/ivao_network/').then(response => response.json());

        // Use Promise.all to wait for both requests to complete
        Promise.all([fetchVATSIM, fetchIVAO])
            .then(data => {
                // data[0] contains the response from fetchVATSIM
                // data[1] contains the response from fetchIVAO

                const pilotsVATSIM = data[0].pilots;
                const pilotsIVAO = data[1].pilots;

                // Process data here (e.g., filter by mapBounds, create SVGs)
                // For simplicity, this example sends back the raw data
                // Combine or process data as needed
                const pilots = {
                    vatsimPilots: pilotsVATSIM,
                    ivaoPilots: pilotsIVAO
                };

                self.postMessage({ pilots });
            })
            .catch(err => console.log('Error fetching data:', err));
    }
});
