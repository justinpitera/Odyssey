import aiohttp
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
import requests
import time
from django.core.cache import cache
from map.forms import ControllerForm
from map.models import Controller, VATSIMFlight
from asgiref.sync import sync_to_async

# Initial headers setup
user_agent = 'SimTrail/1.0 (SimTrail; https://simtrail.com/)'
headers = {
    'User-Agent': user_agent
}


# Cache setup
online_controllers_cache = {
    'data': None,
    'last_updated': 0,
    'update_interval': 300  # Cache duration in seconds, e.g., 5 minutes
}
vatsim_data_cache = {
    'last_updated': 0,
    'data': None,
    'update_interval': 180
}
# Initial setup for the division cache
division_cache = {}
cache_update_interval = 86400  # 24 hours in seconds

# Division to region map
DIVISION_TO_REGION_MAP = {
    "PAC": ["Y", "A", "N", "F"],
    "GBR": ["E"],
    "JPN": ["R"],
    "KOR": ["R"],
    "NZ": ["N", "Z"],
    "PRC": ["Z"],
    "ROC": ["R"],
    "SEA": ["V", "W"],
    "WA": ["O"],
    "EUD": ["E", "L", "U"],
    "USA": ["K", "P"],
    "IL": ["L"],
    "MENA": ["O", "H"],
    "RUS": ["U", "E"],
    "SSA": ["F", "H"],
    "UK": ["E"],
    "BRZ": ["S"],
    "CAN": ["C"],
    "CAR": ["T"],
    "CA": ["M"],
    "MEX": ["M"],
    "SUR": ["S"],
    "CAM": ["M"],
    "SAM": ["S"],
}


def fetch_vatsim_controllers():
    current_time = time.time()
    # Check if cached data is fresh
    if online_controllers_cache['data'] is not None and (current_time - online_controllers_cache['last_updated']) < online_controllers_cache['update_interval']:
        return online_controllers_cache['data']
    else:
        # Fetch new data if cache is stale

        response = requests.get("https://api.vatsim.net/v2/atc/online", headers=headers)
        if response.status_code == 200:
            online_controllers_cache['data'] = response.json()
            online_controllers_cache['last_updated'] = current_time
            return online_controllers_cache['data']
        else:
            return [] 


# Initial cache setup
flight_data_cache = {
    'data': None,
    'last_updated': 0,
    'update_interval': 15 # Cache duration in seconds, e.g., 5 minutes
}


@require_http_methods(["GET"])
def fetch_vatsim_data(request):
    '''Fetches VATSIM data from the VATSIM Data API and returns it as a JSON response.'''
    url = 'https://data.vatsim.net/v3/vatsim-data.json'
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError if the response status code is 4XX/5XX
        data = response.json()

        pilots_data = data.get('pilots', [])
        return JsonResponse(data, safe=False)  # `safe=False` is necessary because we're returning a list
    except requests.RequestException as e:
        return JsonResponse({'error': 'Failed to fetch VATSIM data'}, status=500)


@require_http_methods(["GET"])
def search_vatsim_pilots(request):
    '''Searches VATSIM pilots by callsign, name, or CID and returns the results as a JSON response.'''
    search_query = request.GET.get('query', '').lower()
    url = 'https://data.vatsim.net/v3/vatsim-data.json'
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        filtered_pilots = []
        for pilot in data.get('pilots', []):
            # Convert to lower case for case-insensitive search
            if search_query in pilot.get('callsign', '').lower() or \
               search_query in pilot.get('name', '').lower() or \
               search_query in str(pilot.get('cid', '')).lower():
                filtered_pilots.append(pilot)

        return JsonResponse(filtered_pilots, safe=False)
    except requests.RequestException as e:
        return JsonResponse({'error': 'Failed to fetch VATSIM data'}, status=500)
    
def get_vatsim_user_location(request, vatsim_id):
    '''Returns the latitude and longitude of a VATSIM user with the given VATSIM ID.'''
    vatsim_data = fetch_flight_data()
    for pilot in vatsim_data.get("pilots", []):
        if str(pilot.get("cid", "")) == str(vatsim_id):
            return pilot.get("latitude", 0), pilot.get("longitude", 0)
        
def fetch_flight_data():
    '''Fetches VATSIM flight data from the VATSIM Data API and returns it as a JSON response.'''
    current_time = time.time()
    # Check if the cache is fresh
    if flight_data_cache['data'] is not None and (current_time - flight_data_cache['last_updated']) < flight_data_cache['update_interval']:
        return flight_data_cache['data']
    else:
        # Define custom headers with a non-generic User-Agent
        response = requests.get("https://data.vatsim.net/v3/vatsim-data.json", headers=headers)
        if response.status_code == 200:
            # Update the cache with the new data
            flight_data_cache['data'] = response.json()
            flight_data_cache['last_updated'] = current_time
            return flight_data_cache['data']
        else:
            # In case of an error, return None or consider returning stale data if critical
            return None
        

def update_vatsim_controller_data_cache():
    '''Updates the VATSIM controller data cache if it's stale.'''
    current_time = time.time()
    # Check if the cache needs to be updated
    if current_time - vatsim_data_cache['last_updated'] > vatsim_data_cache['update_interval']:
        try:
            response = requests.get('https://api.vatsim.net/v2/atc/online')
            if response.status_code == 200:
                vatsim_data_cache['data'] = response.json()
                vatsim_data_cache['last_updated'] = current_time
            else:
                print("Failed to fetch data from VATSIM")
        except Exception as e:
            print(f"Error updating VATSIM cache: {e}")



def is_vatsim_controller_online(request, vatsim_id):
    """Check if a controller with the given VATSIM ID is online, using cached data."""
    # Ensure the cache is up to date before checking
    update_vatsim_controller_data_cache()
    # Now check the cached data
    if vatsim_data_cache['data'] is not None:
        for controller in vatsim_data_cache['data']:
            if controller['id'] == vatsim_id:
                return True
    return False


def update_vatsim_controllers(request):
    '''Fetches VATSIM controller data and updates the database with the latest information.'''
    controllers = fetch_vatsim_controllers()

    results = []
    updated_controllers = 0
    total_controllers = len(controllers)  # Get the total number of controllers

    online_count = 0
    database_controllers = Controller.objects.all()
    for index, controller in enumerate(database_controllers, start=1):
        if is_vatsim_controller_online(request, controller.vatsim_id):
            controller.is_online = True
            online_count += 1
            controller.save()
        else:
            controller.is_online = False
            controller.save()

    for index, controller in enumerate(controllers, start=1):
        search_ident = controller['callsign'].split("_")[0]
        controller_type = controller['callsign'].split("_")[-1]
        #division = fetch_controller_division(request, controller['id']).content.decode('utf-8')
        vatsim_id = controller['id']

        backendName = f'{search_ident}_{controller_type}'
        
        existing_controller = Controller.objects.filter(name=backendName).first()
        if existing_controller:
            # If the controller exists, update without changing latitude and longitude
            existing_controller.vatsim_id = vatsim_id
            existing_controller.frequency = controller.get('frequency', 0)  # Temporary placeholder for frequency
            existing_controller.type = controller_type
            existing_controller.division = None
            existing_controller.is_online = True
            existing_controller.save()
        else:
            # If the controller does not exist, create a new one
            Controller.objects.create(
                name=backendName,
                vatsim_id=vatsim_id,
                ident=search_ident,
                latitude_deg=0, 
                longitude_deg=0,
                frequency=controller.get('frequency', 0),  # Temporary placeholder for frequency
                type=controller_type,
                division=None,
                is_online=True,
                airport=None,
            )   
        updated_controllers += 1

    return JsonResponse({'message': f'{updated_controllers} controllers processed.'})
def controllers_data(request):
    controllers = Controller.objects.all().values(
        'ident', 'latitude_deg', 'longitude_deg', 'type', 'division', 'vatsim_id', 'airport_id', 'geoname'
    ).exclude(is_online=False)
    return JsonResponse({'controllers': list(controllers)})

def fetch_flightplan_from_vatsim(vatsim_id):
    """Fetches the flight plan for a given VATSIM ID from the VATSIM API."""
    url = f"https://api.vatsim.net/v2/members/{vatsim_id}/flightplans"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        flightplans = response.json()
        if flightplans:
            return flightplans[0]  
    return None


def fetch_controller_division(request, id):
    current_time = time.time()
    
    # Check if the division data is in the cache and is fresh
    if id in division_cache and current_time - division_cache[id]['last_updated'] < cache_update_interval:
        division = division_cache[id]['division']
    else:
        try:
            # Make an API request to the VATSIM API
            response = requests.get(f'https://api.vatsim.net/api/ratings/{id}', headers=headers)
            response.raise_for_status()  # Raise an error for bad responses
            
            # Extract the division from the response data
            data = response.json()
            division = data.get('division', None)
            
            if division is None:
                return HttpResponse('Division not found', status=404)
            
            # Update the cache with new data
            division_cache[id] = {'division': division, 'last_updated': current_time}
        
        except requests.RequestException as e:
            # Handle any errors that occur during the API request
            return HttpResponse(f'Error retrieving data: {str(e)}', status=500)
    
    # Look up the ICAO codes for the division
    icao_codes = DIVISION_TO_REGION_MAP.get(division, ['-1'])
    
    # Return the ICAO codes as a string in the HttpResponse
    return HttpResponse(','.join(icao_codes))

async def fetch_flight_plan(session, vatsim_id, index, count_members):
    flight_plan_url = f'https://api.vatsim.net/v2/members/{vatsim_id}/flightplans'
    try:
        async with session.get(flight_plan_url) as response:
            if 'application/json' in response.headers.get('Content-Type', ''):
                flight_plans = await response.json()
                if flight_plans:
                    return flight_plans[0]
            else:
                print(f"Non-JSON response for VATSIM ID {vatsim_id}: {response.status}, {response.headers.get('Content-Type')}")
    except aiohttp.ContentTypeError as e:
        print(f"JSON decode error for VATSIM ID {vatsim_id}: {e}")
    return None

async def save_flight_plan_to_db(plan):
    '''Saves a flight plan to the database.'''
    await sync_to_async(VATSIMFlight.objects.update_or_create, thread_sensitive=True)(
        vatsim_id=plan['vatsim_id'],
        defaults={
            'callsign': plan['callsign'],
            'departure': plan['dep'],
            'arrival': plan['arr'],
            'aircraft': plan['aircraft'],
            'cruise_speed': int(plan['cruisespeed']) if 'cruisespeed' in plan and plan['cruisespeed'].isdigit() else 0,
            'altitude': int(plan['altitude']) if 'altitude' in plan and plan['altitude'].isdigit() else 0,
            'route': plan['route'],
        }
    )


@require_http_methods(["GET"])
def vatsim_flight_details(request):
    '''Fetches VATSIM flight data and returns it as a JSON response.'''
    vatsim_data = fetch_flight_data()

    if vatsim_data is not None:
        processed_flights = process_flight_data(vatsim_data)
        return JsonResponse({"pilots": processed_flights})
    else:
        return JsonResponse({'error': 'Failed to fetch VATSIM data'}, status=500)
    

def find_pilot_by_cid(cid, vatsim_data):
    '''Finds a pilot by their VATSIM CID in the provided VATSIM data.'''
    for pilot in vatsim_data.get("pilots", []):
        if str(pilot.get("cid", "")) == str(cid):
            return pilot
    return None


def process_flight_data(data):
    '''Processes the flight data for and returns a list of flight details.'''
    flights = []
    
    for prefile in data.get('pilots', []):
        
        flight_plan = prefile.get('flight_plan')
        
        # Skip this prefile if flight_plan is None
        if not flight_plan:
            continue

        if not flight_plan.get('arrival', '') or not flight_plan.get('departure', ''):  # Skip if no arrival or departure
            continue
        
        # Extract flight_plan details
        flight_details = {
            'aircraft_short': flight_plan.get('aircraft_short', ''),
            'departure': flight_plan.get('departure', ''),
            'arrival': flight_plan.get('arrival', ''),
            'alternate': flight_plan.get('alternate', ''),
            'cruise_tas': flight_plan.get('cruise_tas', ''),
            'altitude': flight_plan.get('altitude', ''),
            'deptime': flight_plan.get('deptime', ''),
            'enroute_time': flight_plan.get('enroute_time', ''),
            'route': flight_plan.get('route', ''),
        }

        # Add pilot details
        flight_details.update({
            'name': prefile.get('name', ''),
            'callsign': prefile.get('callsign', ''),
            'transponder': prefile.get('transponder', ''),
            'cid': prefile.get('cid', ''),
            'latitude': prefile.get('latitude', ''),
            'longitude': prefile.get('longitude', ''),
        })
        
        flights.append(flight_details)
    
    return flights


def is_vatsim_id(request, network_id):
    vatsim_data = fetch_flight_data()
    for pilot in vatsim_data.get("pilots", []):
        if str(pilot.get("cid", "")) == str(network_id):
            return pilot
    return None

def find_pilot_by_cid(cid, vatsim_data):
    
    for pilot in vatsim_data.get("pilots", []):
        if str(pilot.get("cid", "")) == str(cid):
            return pilot
    return None

def fetch_vatsim_flight_data(request):

    cache_key = 'vatsim_data'
    cache_time = 15  # time in seconds for cache to be valid

    # Try to get cached data
    data = cache.get(cache_key)
    if data is not None:
        return JsonResponse(data)  # Return cached data if available

    # Fetch new data if not cached or cache is stale
    url = 'https://data.vatsim.net/v3/vatsim-data.json'
    try:
        response = requests.get(url,headers=headers)
        response.raise_for_status()
        data = response.json()
        cache.set(cache_key, data, cache_time)  # Update cache
        return JsonResponse(data)
    except requests.RequestException as e:
        return JsonResponse({'error': 'Failed to fetch VATSIM data', 'details': str(e)}, status=500)
