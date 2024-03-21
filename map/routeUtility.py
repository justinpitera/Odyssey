import csv
import math

from django.http import JsonResponse
from map.ivaoUtility import fetch_ivao_map_data
from map.mathUtility import haversine
import os
from django.conf import settings
import concurrent.futures
from map.models import Airport, Waypoint
from map.vatsimUtility import fetch_flightplan_from_vatsim, find_pilot_by_cid

def waypoint_coordinates(request, name):
    '''Returns the latitude and longitude of a waypoint with the given name.'''
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

def extract_waypoints_from_route(route):
    """Extracts waypoint identifiers from a flight plan route string."""
    return route.split() 


def match_waypoints_in_db(waypoints):
    """Fetches waypoints from the database and returns them in the order they appear in the waypoints list."""
    waypoints_queryset = Waypoint.objects.filter(ident__in=waypoints)
    # Create a dictionary of waypoints for fast lookup
    waypoint_dict = {wp.ident: wp for wp in waypoints_queryset}
    # Reorder waypoints based on the input list order
    ordered_waypoints = [waypoint_dict[ident] for ident in waypoints if ident in waypoint_dict]
    return ordered_waypoints


def waypoints_view(request):
    '''Returns a JSON response with all waypoints.'''
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




def construct_route(request, network_id):
    """Constructs a route from VATSIM or IVAO flight plan's waypoints, including departure and arrival airports."""
    flight_plan = fetch_flightplan_from_vatsim(network_id)
    network = 'VATSIM'
    if flight_plan is None:
        network = "IVAO"
        pilots_data = fetch_ivao_map_data()
        # Access the specific pilot's data using the network_id as a key
        pilot_data = pilots_data.get(int(network_id))  # Ensure network_id is in the correct format (str or int)
        if pilot_data:
            # Directly use the pilot_data dictionary if found
            user_flight_plan = pilot_data
        else:
            # Handle the case where the pilot's data is not found
            return JsonResponse({'error': 'Pilot data not found for the given network ID'}, status=404)
    else:
        dep_ident = flight_plan.get('dep', '')
        arr_ident = flight_plan.get('arr', '')
        route = flight_plan.get('route', '')

    if network == 'VATSIM':
        # If VATSIM, data is already set
        pass
    else:  # IVAO
        dep_ident = user_flight_plan.get('departure')
        arr_ident = user_flight_plan.get('arrival')
        route = user_flight_plan.get('route')

    response_data = {
        'network': network,
        'departure': dep_ident,
        'arrival': arr_ident,
        'route': route,
        # include any other details you need
    }

    try:
        departure_airport = Airport.objects.get(ident=dep_ident) if dep_ident else None
        arrival_airport = Airport.objects.get(ident=arr_ident) if arr_ident else None
    except Airport.DoesNotExist:
        return JsonResponse({'error': 'Airport not found'}, status=404)

    waypoint_identifiers = extract_waypoints_from_route(route)
    ordered_waypoints = match_waypoints_in_db(waypoint_identifiers)

    distance_threshold = 1000

    waypoints_data = [{
        'ident': departure_airport.ident,
        'latitude_deg': departure_airport.latitude_deg,
        'longitude_deg': departure_airport.longitude_deg
    }] if departure_airport else []

    for waypoint in ordered_waypoints:
        prev_wp = waypoints_data[-1] if waypoints_data else {'latitude_deg': departure_airport.latitude_deg, 'longitude_deg': departure_airport.longitude_deg}
        distance = haversine(prev_wp['latitude_deg'], prev_wp['longitude_deg'], waypoint.latitude_deg, waypoint.longitude_deg)

        if distance <= distance_threshold:
            waypoints_data.append({
                'ident': waypoint.ident,
                'latitude_deg': waypoint.latitude_deg,
                'longitude_deg': waypoint.longitude_deg
            })

    if arrival_airport:  # Check if arrival airport info is available
        waypoints_data.append({
            'ident': arrival_airport.ident,
            'latitude_deg': arrival_airport.latitude_deg,
            'longitude_deg': arrival_airport.longitude_deg
        })

    return JsonResponse({'waypoints': waypoints_data})




def get_remaining_distance(request, cid, vatsim_data):
    '''Calculates the remaining distance for a pilot's flight based on their current position and flight plan.'''
    if vatsim_data is None:
        return JsonResponse({"error": "Could not fetch VATSIM data"}, status=500)

    pilot_data = find_pilot_by_cid(cid, vatsim_data)
    if pilot_data is None:
        return JsonResponse({"error": "Pilot not found"}, status=404)

    flight_plan = pilot_data.get('flight_plan', {})
    route = flight_plan.get('route', '')
    current_latitude = float(pilot_data.get('latitude', 0))
    current_longitude = float(pilot_data.get('longitude', 0))

    waypoints_data = extract_waypoints_from_route(route)
    ordered_waypoints = match_waypoints_in_db(waypoints_data)
    # Parallelize total distance calculation


    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_distance = {
            executor.submit(haversine, ordered_waypoints[i].longitude_deg, ordered_waypoints[i].latitude_deg, ordered_waypoints[i + 1].longitude_deg, ordered_waypoints[i + 1].latitude_deg): i
            for i in range(len(ordered_waypoints) - 1)
        }
        total_distance = sum(future.result() for future in concurrent.futures.as_completed(future_to_distance))


    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_distance_wp = {
            executor.submit(haversine, current_longitude, current_latitude, wp.longitude_deg, wp.latitude_deg): wp
            for wp in ordered_waypoints
        }
        nearest_wp, nearest_distance = min(
            ((wp, future.result()) for future, wp in future_to_distance_wp.items()),
            key=lambda x: x[1]
        )

    # Calculate remaining distance from nearest waypoint
    remaining_distance = sum(
        haversine(wp.longitude_deg, wp.latitude_deg, ordered_waypoints[j].longitude_deg, ordered_waypoints[j].latitude_deg)
        for j, wp in enumerate(ordered_waypoints) if j >= ordered_waypoints.index(nearest_wp)
    )
    if ordered_waypoints.index(nearest_wp) > 0:
        remaining_distance += nearest_distance

    remaining_percentage = (remaining_distance / total_distance) * 100 if total_distance > 0 else 0

    print("Finished calculating distance for ", cid)
    return remaining_percentage