function drawATCBoundaries() {
    if (map && staticBaseUrl) { 
        map.on('load', function () {
            fetch(`${staticBaseUrl}layers/vatsim_atc.geojson`)
                .then(response => response.json())
                .then(data => {
                    map.addSource('atc-boundaries', {
                        type: 'geojson',
                        data: data
                    });

                    map.addLayer({
                        id: 'atc-boundaries-layer',
                        type: 'fill', 
                        source: 'atc-boundaries',
                        paint: {
                            'fill-color': '#989696',
                            'fill-opacity': 0.3
                        }
                    });
                })
                .catch(error => console.error('Error loading GeoJSON:', error));
        });
    }
}



drawATCBoundaries();