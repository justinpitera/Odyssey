
import time
from django.http import JsonResponse
from django.core.cache import cache
import requests

from map.conversionUtility import flight_level_to_feet, speed_to_knots
# Initial headers setup
user_agent = 'SimTrail/1.0 (SimTrail; https://simtrail.com/)'
headers = {
    'User-Agent': user_agent
}

# Initial last known data cache setup
last_known_data = {}


def fetch_flightplan_from_ivao(pilots_data, user_id):
    """
    Searches for a pilot's flight plan in the provided data based on the user's ID.

    Parameters:
    - pilots_data (list): The list containing pilots' information.
    - user_id (int): The unique identifier for the pilot whose flight plan is being requested.

    Returns:
    - dict: The flight plan for the specified pilot, or None if not found.
    """
    # Iterate over the list of pilots
    for pilot in pilots_data:
        # Check if the current pilot's userId matches the requested userId
        if pilot.get('userId') == user_id:  # Using .get() for safer access
            # Pilot found, return their information (excluding the userId for privacy)
            flight_plan = {
                "latitude": pilot.get("latitude"),
                "longitude": pilot.get("longitude"),
                "heading": pilot.get("heading"),
                "altitude": pilot.get("altitude"),
                "speed": pilot.get("speed"),
                "departure": pilot.get("departure"),
                "route": pilot.get("route"),
                "arrival": pilot.get("arrival"),
            }
            return flight_plan

    # Return None if no matching pilot is found
    return None




def fetch_ivao_network(request):
    '''Fetches data from the IVAO network and returns a simplified version of the data.'''
    # The cache key for storing/retrieving the data
    cache_key = 'ivao_pilots_data_simplified'
    # Time to live for the cache in seconds
    cache_ttl = 15

    # Try fetching from cache first
    cache_response = cache.get(cache_key)
    cached_data = cache_response.get('data') if cache_response else None
    cached_time = cache_response.get('timestamp') if cache_response else None

    # Check if cached data is still within TTL
    if cached_data and cached_time and (time.time() - cached_time) < cache_ttl:
        return JsonResponse({'pilots': cached_data}, safe=False)

    try:
        # The IVAO API base URL, endpoint, and full URL
        base_url = 'https://api.ivao.aero/'
        endpoint = 'v2/tracker/whazzup'
        url = f"{base_url}{endpoint}"
        
        # Assume 'headers' contains the necessary authentication headers, including OAuth tokens if required
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            # Parse the JSON response
            original_data = response.json()
            clients_data = original_data.get('clients', [])
            pilots_data = clients_data.get('pilots',[])
            # Filter or process to get only pilot data, adjust according to the actual data structure
            # This is an assumed structure; you'll need to adapt it based on the actual API response
            simplified_data = []

            for pilot in pilots_data:
                if pilot is None:
                    continue

                last_track = pilot.get('lastTrack', {})
                
                flight_plan = pilot.get('flightPlan', {})

                departure_city = flight_plan.get('departureId', {}) if isinstance(flight_plan, dict) else {}
                arrival_city = flight_plan.get('arrivalId', {}) if isinstance(flight_plan, dict) else {}
                route = flight_plan.get('route', {}) if isinstance(flight_plan, dict) else {}
                simplified_data.append({
                    'userId': pilot.get('userId'),
                    'callsign': pilot.get('callsign') if isinstance(pilot, dict) else '',
                    'latitude': last_track.get('latitude') if isinstance(last_track, dict) else None,
                    'longitude': last_track.get('longitude') if isinstance(last_track, dict) else None,
                    'heading': last_track.get('heading') if isinstance(last_track, dict) else None,
                    'altitude': last_track.get('altitude') if isinstance(last_track, dict) else None,
                    'speed': last_track.get('groundSpeed') if isinstance(last_track, dict) else None,
                    'departure': departure_city,
                    'route': route,
                    'arrival': arrival_city,
                })


            # Cache the simplified data with a timestamp
            cache.set(cache_key, {'data': simplified_data, 'timestamp': time.time()}, cache_ttl)

            # Optionally update last known data
            global last_known_data
            last_known_data = simplified_data.copy()

            return JsonResponse({'pilots': simplified_data}, safe=False)
        else:
            raise Exception("Failed to fetch data due to unsuccessful status code.")
    except Exception as e:
        if last_known_data:
            return JsonResponse({'pilots': last_known_data}, safe=False)
        else:
            print(f"Failed to fetch new data and no cached or last known data is available. Error: {e}")
            return JsonResponse({'error': 'Failed to fetch data from IVAO and no cached or last known data is available'}, status=500)
    

def fetch_ivao_map_data():
    '''Fetches data from the IVAO network and returns a simplified version of the data.'''
    # The cache key for storing/retrieving the data
    cache_key = 'ivao_pilots_route_data'
    # Time to live for the cache in seconds
    cache_ttl = 15

    # Try fetching from cache first
    cache_response = cache.get(cache_key)
    cached_data = cache_response.get('data') if cache_response else None
    cached_time = cache_response.get('timestamp') if cache_response else None

    # Check if cached data is still within TTL
    if cached_data and cached_time and (time.time() - cached_time) < cache_ttl:
        return cached_data

    try:
        # The IVAO API base URL, endpoint, and full URL
        base_url = 'https://api.ivao.aero/'
        endpoint = 'v2/tracker/whazzup'
        url = f"{base_url}{endpoint}"
        
        # Assume 'headers' contains the necessary authentication headers, including OAuth tokens if required
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            # Parse the JSON response
            original_data = response.json()
            clients_data = original_data.get('clients', {})
            pilots_data = clients_data.get('pilots', {})
            
            # Initialize the dictionary for storing simplified pilot data
            simplified_data = {}

            for pilot in pilots_data:
                if pilot is None:
                    continue

                
                last_track = pilot.get('lastTrack', {})
                flight_plan = pilot.get('flightPlan', {})

                departure_city = flight_plan.get('departureId', None) if isinstance(flight_plan, dict) else None
                arrival_city = flight_plan.get('arrivalId', None) if isinstance(flight_plan, dict) else None
                route = flight_plan.get('route', None) if isinstance(flight_plan, dict) else None
                plannedFL = flight_level_to_feet(flight_plan.get('level', '')) if isinstance(flight_plan, dict) else None
                plannedSpeed = speed_to_knots(flight_plan.get('speed', '')) if isinstance(flight_plan, dict) else None
                aircraft_type = flight_plan.get('aircraftId', None) if isinstance(flight_plan, dict) else None

                # Use userId as the key for each pilot entry
                simplified_data[pilot.get('userId')] = {
                    'latitude': last_track.get('latitude') if isinstance(last_track, dict) else None,
                    'longitude': last_track.get('longitude') if isinstance(last_track, dict) else None,
                    'heading': last_track.get('heading') if isinstance(last_track, dict) else None,
                    'altitude': plannedFL,
                    'speed': last_track.get('groundSpeed') if isinstance(last_track, dict) else None,
                    'departure': departure_city,
                    'route': route,
                    'arrival': arrival_city,
                    'callsign': pilot.get('callsign') if isinstance(pilot, dict) else '',
                    'aircraft_short': aircraft_type,
                    'cruise_tas': plannedSpeed,
                }

            # Cache the simplified data with a timestamp
            cache.set(cache_key, {'data': simplified_data, 'timestamp': time.time()}, cache_ttl)

            # Optionally update last known data
            global last_known_data
            last_known_data = simplified_data.copy()
            return simplified_data
        else:
            raise Exception("Failed to fetch data due to unsuccessful status code.")
    except Exception as e:
        if last_known_data:
            return last_known_data
        else:
            return {'error': 'Failed to fetch data from IVAO and no cached or last known data is available'}, 500

def fetch_ivao_network(request):
    # The cache key for storing/retrieving the data
    cache_key = 'ivao_pilots_data_simplified'
    # Time to live for the cache in seconds
    cache_ttl = 15

    # Try fetching from cache first
    cache_response = cache.get(cache_key)
    cached_data = cache_response.get('data') if cache_response else None
    cached_time = cache_response.get('timestamp') if cache_response else None

    # Check if cached data is still within TTL
    if cached_data and cached_time and (time.time() - cached_time) < cache_ttl:
        return JsonResponse({'pilots': cached_data}, safe=False)

    try:
        # The IVAO API base URL, endpoint, and full URL
        base_url = 'https://api.ivao.aero/'
        endpoint = 'v2/tracker/whazzup'
        url = f"{base_url}{endpoint}"
        
        # Assume 'headers' contains the necessary authentication headers, including OAuth tokens if required
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            # Parse the JSON response
            original_data = response.json()
            clients_data = original_data.get('clients', [])
            pilots_data = clients_data.get('pilots',[])
            # Filter or process to get only pilot data, adjust according to the actual data structure
            # This is an assumed structure; you'll need to adapt it based on the actual API response
            simplified_data = []

            for pilot in pilots_data:
                if pilot is None:
                    continue

                last_track = pilot.get('lastTrack', {})
                
                flight_plan = pilot.get('flightPlan', {})

                departure_city = flight_plan.get('departureId', {}) if isinstance(flight_plan, dict) else {}
                arrival_city = flight_plan.get('arrivalId', {}) if isinstance(flight_plan, dict) else {}
                route = flight_plan.get('route', {}) if isinstance(flight_plan, dict) else {}
                simplified_data.append({
                    'userId': pilot.get('userId'),
                    'callsign': pilot.get('callsign') if isinstance(pilot, dict) else '',
                    'latitude': last_track.get('latitude') if isinstance(last_track, dict) else None,
                    'longitude': last_track.get('longitude') if isinstance(last_track, dict) else None,
                    'heading': last_track.get('heading') if isinstance(last_track, dict) else None,
                    'altitude': last_track.get('altitude') if isinstance(last_track, dict) else None,
                    'speed': last_track.get('groundSpeed') if isinstance(last_track, dict) else None,
                    'departure': departure_city,
                    'route': route,
                    'arrival': arrival_city,
                })


            # Cache the simplified data with a timestamp
            cache.set(cache_key, {'data': simplified_data, 'timestamp': time.time()}, cache_ttl)

            # Optionally update last known data
            global last_known_data
            last_known_data = simplified_data.copy()

            return JsonResponse({'pilots': simplified_data}, safe=False)
        else:
            raise Exception("Failed to fetch data due to unsuccessful status code.")
    except Exception as e:
        if last_known_data:
            return JsonResponse({'pilots': last_known_data}, safe=False)
        else:
            print(f"Failed to fetch new data and no cached or last known data is available. Error: {e}")
            return JsonResponse({'error': 'Failed to fetch data from IVAO and no cached or last known data is available'}, status=500)
        

def is_ivao_id(request, network_id):
    data = fetch_ivao_map_data()  
    print(data.keys())
    # Directly check if the network_id is a key in the data dictionary
    return int(network_id) in data.keys()