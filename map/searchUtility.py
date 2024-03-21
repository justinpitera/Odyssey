import csv
import os
from django.conf import settings
from django.http import JsonResponse
from map.vatsimUtility import fetch_vatsim_controllers
from map.models import Airport


def search_airports(request):
    '''Searches for airports based on the query string and returns a JSON response with the results.'''
    query = request.GET.get('query', '').lower()
    results = []

    with open(os.path.join(settings.STATIC_ROOT, 'data', 'airports.csv'), newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip the header row
        for row in reader:
            if query in row[3].lower() or query in row[1].lower():
                result = {
                    'ident': row[1],
                    'name': row[3],
                    'type': row[2],
                    'coordinates': f"{row[5]}, {row[4]}",
                    'municipality': row[10],
                    'lat': f"{row[5]}",
                    'lon': f"{row[4]}"
                }
                # Prepend if ident matches exactly, else append
                if query == row[1].lower():
                    results.insert(0, result)  # This puts it at the beginning of the list
                else:
                    results.append(result)

    return JsonResponse(results, safe=False)


def search_vatsim(request):
    controllers = fetch_vatsim_controllers()
    
    seen_idents = set()
    results = []

    for controller in controllers:
        search_ident = controller['callsign'].split("_")[0]
        type = controller['callsign'].split("_")[-1]


            # If ident is exactly 4 characters, match exactly the last three characters in the database
        airports = Airport.objects.filter(ident__endswith=search_ident[-3:]).exclude(type__in=['small_airport', 'heliport', 'closed'])

        for airport in airports:
            if airport.ident not in seen_idents:
                seen_idents.add(airport.ident)
                data = {
                    'ident': airport.ident,
                    'latitude_deg': airport.latitude_deg,
                    'longitude_deg': airport.longitude_deg,
                    'type': type  # Assuming you want to maintain the type as per the controller's callsign
                }
                results.append(data)

    if results:
        return JsonResponse({'airports': results})
    else:
        return JsonResponse({'error': 'No matching airports found for online controllers'}, status=404)