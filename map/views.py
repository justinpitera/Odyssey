import csv
import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from map.models import Airport
from schedule.models import Flight
from django.conf import settings
from itertools import islice
from django.contrib.auth.decorators import login_required

@login_required
def aircraft_map(request):
    try:
        userAircraft = Flight.objects.get(user=request.user, is_active=True)
        aircraft = Flight.objects.filter(is_active=True).exclude(user=request.user)#old
        userLat = userAircraft.aircraft_latitude
        userLon = userAircraft.aircraft_longitude
        context = {
            'aircraft': aircraft,
            'userAircraft': userAircraft,
            'page_title': 'Map - Odyssey',
            'userLat': userLat,
            'userLon': userLon
        }
    except Flight.DoesNotExist:
        aircraft = Flight.objects.filter(is_active=True)
        context = {
            'aircraft': aircraft,
            'page_title': 'Map - Odyssey',
        }
    return render(request, 'map/map.html', context)

def aircraft_data(request):
    # Query all active flights
    active_flights = Flight.objects.filter(is_active=True)
    
    # Serialize the data for each active flight into a list of dictionaries
    flights_data = []
    for flight in active_flights:
        flight_data = {
            'latitude': flight.aircraft_latitude,
            'longitude': flight.aircraft_longitude,
            'heading': flight.aircraft_heading,
            'altitude': flight.current_altitude,
            'ground_speed': flight.aircraft_ground_speed,
            # Assuming 'username' is the concatenated first name and last name of the flight's user
            'username': flight.user.first_name + " " + flight.user.last_name if flight.user else "Unknown",
            'userId': flight.user.id if flight.user else None,
            'flight_number': flight.flight_number,
        }
        flights_data.append(flight_data)
    
    # Return all flights data as JSON
    return JsonResponse({'flights': flights_data})



def waypoints_view(request):
    waypoints = []
    seen_names = set()  # Set to keep track of names already seen

    with open(os.path.join(settings.STATIC_ROOT, 'data', 'waypoint_data.csv'), newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row['name']
            if name not in seen_names:  # Check if name has not been added yet
                waypoints.append({
                    'name': name,
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude'])
                })
                seen_names.add(name)  # Add name to the set of seen names

    return JsonResponse({'waypoints': waypoints})




def airports_view(request):
    # Extract viewport bounds and zoom level from request parameters
    north_bound = float(request.GET.get('northBound', '90'))
    south_bound = float(request.GET.get('southBound', '-90'))
    east_bound = float(request.GET.get('eastBound', '180'))
    west_bound = float(request.GET.get('westBound', '-180'))
    zoom_level = float(request.GET.get('zoom', 10))

    # Initialize lists to hold the filtered airports and search results
    airports = []
    searchList = []

    # Query the database for all airports that are within the viewport bounds
    queryset = Airport.objects.filter(
        latitude_deg__lte=north_bound,
        latitude_deg__gte=south_bound,
        longitude_deg__lte=east_bound,
        longitude_deg__gte=west_bound,
    )

    for airport in queryset:
        include_airport = False
        coordinates = f"{airport.longitude_deg}, {airport.latitude_deg}"

        # Adjust airport inclusion based on zoom level and airport type
        if zoom_level > 10:
            include_airport = True
        elif zoom_level > 8.1 and airport.type in ['large_airport', 'medium_airport', 'heliport']:
            include_airport = True
        elif zoom_level > 4.5 and (airport.type == 'large_airport' or (airport.type == 'medium_airport' and 'international' in airport.name.lower())):
            include_airport = True

        if include_airport:
            airports.append({
                'name': airport.name,
                'type': airport.type,
                'coordinates': coordinates,
                'municipality': airport.iso_region,  # Assuming iso_region is used in place of municipality
            })

        # Assuming you want to add all queried airports to searchList regardless of the zoom level
        searchList.append({
            'name': airport.name,
            'type': airport.type,
            'coordinates': coordinates,
            'municipality': airport.iso_region,
        })

    # Handle the search query
    query = request.GET.get('query', '').lower()
    results = []

    if query:
        # Filter the already filtered queryset for names containing the query
        search_results = queryset.filter(name__icontains=query)
        for airport in search_results:
            results.append({
                'name': airport.name,
                'type': airport.type,
                'coordinates': f"{airport.longitude_deg}, {airport.latitude_deg}",
                'municipality': airport.iso_region,
            })

    # Return both the filtered list of airports and the search results
    return JsonResponse({'airports': airports, 'searchList': searchList, 'results': results}, safe=False)




def search_airports(request):
    query = request.GET.get('query', '').lower()
    results = []

    with open(os.path.join(settings.STATIC_ROOT, 'data', 'airports.csv'), newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip the header row
        for row in reader:
            if query in row[3].lower() or query in row[1].lower():  # Assuming row[3] contains the airport name
                results.append({
                    'ident': row[1],
                    'name': row[3],
                    'type': row[2],
                    'coordinates': f"{row[5]}, {row[4]}",
                    'municipality': row[10],
                    'lat': f"{row[5]}",
                    'lon': f"{row[4]}"
                })

    return JsonResponse(results, safe=False)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def import_airports_from_csv(request):
    csv_file_path = 'staticfiles/data/airports.csv'  # Ensure this path is correct and accessible
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['type'].lower() == 'closed':
                continue
            
            airport, created = Airport.objects.get_or_create(
                ident=row['ident'],
                defaults={
                    'type': row['type'],
                    'name': row['name'],
                    'latitude_deg': float(row['latitude_deg']),
                    'longitude_deg': float(row['longitude_deg']),
                    'elevation_ft': int(row['elevation_ft']) if row['elevation_ft'] else None,
                    'continent': row['continent'],
                    'iso_country': row['iso_country'],
                    'iso_region': row['iso_region'],
                }
            )
            
            if created:
                print(f"Successfully added: {airport.name} ({airport.ident})")
            else:
                print(f"Airport already exists: {airport.name} ({airport.ident})")
    return HttpResponse('Airport data imported successfully.')




from math import radians, cos, sin, asin, sqrt
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees).
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

from django.http import JsonResponse
import os
import csv
from django.conf import settings
import math

def waypoint_coordinates(request, name):
    lat = request.GET.get('lat', None)
    lon = request.GET.get('lon', None)

    # Check if lat or lon are 'undefined' or None and handle accordingly
    if lat in ('undefined', None) or lon in ('undefined', None):
        lat = 0
        lon = 0
        
    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        # Handle the case where conversion to float fails
        return JsonResponse({'error': 'Invalid latitude or longitude'}, status=400)

    filepath = os.path.join(settings.STATIC_ROOT, 'data', 'waypoint_data.csv')
    closest_distance = None
    closest_waypoint = None

    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['name'] == name:
                waypoint_lat = float(row['latitude'])
                waypoint_lon = float(row['longitude'])
                distance = math.sqrt((lat - waypoint_lat) ** 2 + (lon - waypoint_lon) ** 2)

                if closest_distance is None or distance < closest_distance:
                    closest_distance = distance
                    closest_waypoint = row

    if closest_waypoint:
        return JsonResponse({
            'name': closest_waypoint['name'],
            'latitude': float(closest_waypoint['latitude']),
            'longitude': float(closest_waypoint['longitude'])
        })
    else:
        return JsonResponse({'error': 'Waypoint not found'}, status=404)
    

def should_skip_waypoint(current, next_waypoint, previous=None, threshold=10):
    """
    Determines if a waypoint should be skipped based on its distance
    from the previous and next waypoints.
    
    Args:
        current: The current waypoint (latitude, longitude).
        next_waypoint: The next waypoint (latitude, longitude).
        previous: The previous waypoint (latitude, longitude), if any.
        threshold: The distance threshold for skipping waypoints.
    
    Returns:
        A boolean indicating whether the waypoint should be skipped.
    """
    # Calculate distance to next waypoint
    distance_to_next = haversine(current[0], current[1], next_waypoint[0], next_waypoint[1])
    
    # If there's no previous waypoint, only consider the distance to the next waypoint
    if not previous:
        return distance_to_next > threshold
    
    # Calculate distance from previous waypoint
    distance_from_previous = haversine(previous[0], previous[1], current[0], current[1])
    
    # Check if the waypoint is far from both the previous and next waypoints
    return distance_to_next > threshold and distance_from_previous > threshold
