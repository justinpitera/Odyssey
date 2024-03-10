import csv
import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from map.forms import ControllerForm
from map.models import Airport, Controller
from schedule.models import Flight
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Q
from django.views.decorators.http import require_http_methods
import requests
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import asyncio
import aiohttp
from django.forms.models import model_to_dict
from asgiref.sync import sync_to_async

@login_required
def aircraft_card(request):
    return render(request, 'map/airport.html')

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
            'page_title': 'Odyssey Network',
            'userLat': userLat,
            'userLon': userLon
        }
    except Flight.DoesNotExist:
        aircraft = Flight.objects.filter(is_active=True)
        context = {
            'aircraft': aircraft,
            'page_title': 'Odyssey Network',
        }
    return render(request, 'map/map.html', context)

def aircraft_data(request):
    # Query all active flights
    active_flights = Flight.objects.filter(is_active=True)
    
    flights_data = []
    for flight in active_flights:
        flight_data = {
            'latitude': flight.aircraft_latitude,
            'longitude': flight.aircraft_longitude,
            'heading': flight.aircraft_heading,
            'altitude': flight.current_altitude,
            'ground_speed': flight.aircraft_ground_speed,
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



@require_http_methods(["GET"])
def fetch_vatsim_data(request):
    url = 'https://data.vatsim.net/v3/vatsim-data.json'
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError if the response status code is 4XX/5XX
        data = response.json()

        pilots_data = data.get('pilots', [])
        # You can now process pilots_data as needed or return it directly
        print(pilots_data)
        return JsonResponse(pilots_data, safe=False)  # `safe=False` is necessary because we're returning a list
    except requests.RequestException as e:
        return JsonResponse({'error': 'Failed to fetch VATSIM data'}, status=500)

@require_http_methods(["GET"])
def search_vatsim_pilots(request):
    search_query = request.GET.get('query', '').lower()
    url = 'https://data.vatsim.net/v3/vatsim-data.json'
    try:
        response = requests.get(url)
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
                'ident': airport.ident,
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



def airport_details(request, airport_ident):
    arrivals_queryset = VATSIMFlight.objects.filter(arrival=airport_ident)
    departures_queryset = VATSIMFlight.objects.filter(departure=airport_ident)

    airportName = Airport.objects.get(ident=airport_ident).name
    # Manually construct the list of dictionaries for serialization
    arrivals = [{
        'vatsim_id': flight.vatsim_id,
        'callsign': flight.callsign,
        'departure': flight.departure,
        'arrival': flight.arrival,
        'aircraft': flight.aircraft,
        'cruise_speed': flight.cruise_speed,
        'altitude': flight.altitude,
        'route': flight.route,
    } for flight in arrivals_queryset]

    departures = [{
        'vatsim_id': flight.vatsim_id,
        'callsign': flight.callsign,
        'departure': flight.departure,
        'arrival': flight.arrival,
        'aircraft': flight.aircraft,
        'cruise_speed': flight.cruise_speed,
        'altitude': flight.altitude,
        'route': flight.route,
    } for flight in departures_queryset]

    return JsonResponse({
        'arrivals': arrivals,
        'departures': departures,
        'airportName': airportName
    })







def search_airports(request):
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

from django.http import JsonResponse
from .models import Airport, VATSIMFlight, Waypoint

def fetch_online_controllers():
    url = "https://api.vatsim.net/v2/atc/online"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return []
    



# Ensure this map is defined in your code
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

def fetch_controller_division(request, id):
    try:
        # Make an API request to the VATSIM API
        response = requests.get(f'https://api.vatsim.net/api/ratings/{id}')
        response.raise_for_status()  # Raise an error for bad responses
        
        # Extract the division from the response data
        data = response.json()
        division = data.get('division', None)
        
        if division is None:
            return HttpResponse('Division not found', status=404)
        
        # Look up the ICAO codes for the division
        icao_codes = DIVISION_TO_REGION_MAP.get(division, ['-1'])
        
        # Return the ICAO codes as a string in the HttpResponse
        return HttpResponse(','.join(icao_codes))
    except requests.RequestException as e:
        # Handle any errors that occur during the API request
        return HttpResponse(f'Error retrieving data: {str(e)}', status=500)


def search_vatsim(request):
    controllers = fetch_online_controllers()
    
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

def update_vatsim_controllers(request):
    controllers = fetch_online_controllers()

    results = []
    updated_controllers = 0
    total_controllers = len(controllers)  # Get the total number of controllers

    online_count = 0
    database_controllers = Controller.objects.all()
    for index, controller in enumerate(database_controllers, start=1):
        print(f"Fetching request to see if {controller.vatsim_id} @ {controller.ident} is online. {index} of {len(database_controllers)}")
        if is_online(request, controller.vatsim_id):
            print(f"Controller {controller.vatsim_id} @ {controller.ident} is still online.")
            controller.is_online = True
            online_count += 1
            controller.save()
        else:
            print(f"Controller {controller.vatsim_id} @ {controller.ident} is now offline.")
            controller.is_online = False
            controller.save()

    print("Request complete: ", online_count, " controllers reported online.")
    for index, controller in enumerate(controllers, start=1):
        print(f"Processing data for controller {index} of {total_controllers}: {controller['id']}")
        search_ident = controller['callsign'].split("_")[0]
        controller_type = controller['callsign'].split("_")[-1]
        division = fetch_controller_division(request, controller['id']).content.decode('utf-8')
        vatsim_id = controller['id']

        backendName = f'{search_ident}_{controller_type}'
        
        # Find or create the associated airport
        division_tuple = tuple(division.replace(",", ""))  # Remove spaces and commas, then convert to tuple
        airports = Airport.objects.filter(ident__endswith=search_ident[-3:]).exclude(type__in=['closed', 'heliport'])

        query = Q()
        for letter in division_tuple:
            query |= Q(ident__startswith=letter)
        print(division_tuple)

        airport = airports.filter(query).first()
        if airport is None:
            print(f"No matching airport found for controller {vatsim_id} @ {backendName} with division {division}")
            continue

        # Check if the controller exists
        existing_controller = Controller.objects.filter(name=backendName).first()
        if existing_controller:
            # If the controller exists, update without changing latitude and longitude
            existing_controller.vatsim_id = vatsim_id
            existing_controller.frequency = controller.get('frequency', 0)  # Temporary placeholder for frequency
            existing_controller.type = controller_type
            existing_controller.division = division
            existing_controller.is_online = True
            existing_controller.save()
            print(f"Updated {backendName} with VATSIM ID: {vatsim_id}")
        else:
            # If the controller does not exist, create a new one
            Controller.objects.create(
                name=backendName,
                vatsim_id=vatsim_id,
                ident=search_ident,
                latitude_deg=airport.latitude_deg,
                longitude_deg=airport.longitude_deg,
                frequency=controller.get('frequency', 0),  # Temporary placeholder for frequency
                type=controller_type,
                division=division,
                is_online=True,
                airport=airport,
            )
            print(f"Created {backendName} with VATSIM ID: {vatsim_id}")
        updated_controllers += 1

    return JsonResponse({'message': f'{updated_controllers} controllers processed.'})
def controllers_data(request):
    controllers = Controller.objects.all().values(
        'ident', 'latitude_deg', 'longitude_deg', 'type', 'division', 'vatsim_id', 'airport_id'
    ).exclude(is_online=False)
    return JsonResponse({'controllers': list(controllers)})

def add_controller(request):
    if request.method == 'POST':
        form = ControllerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('map')  # Redirect to a new URL
    else:
        form = ControllerForm()  # An unbound form

    return render(request, 'map/add_controller.html', {'form': form})


def is_online(request, vatsim_id):
    try:
        response = requests.get('https://api.vatsim.net/v2/atc/online')
        if response.status_code == 200:
            controllers = response.json()
            for controller in controllers:
                if controller['id'] == vatsim_id:
                    return True
            # If the loop completes without finding the ID, they are offline
            return False
        else:
            return JsonResponse({'error': 'Failed to fetch data from VATSIM'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from django.http import JsonResponse
from .models import Waypoint
import requests

def fetch_flightplan_from_vatsim(vatsim_id):
    """Fetches the flight plan for a given VATSIM ID from the VATSIM API."""
    url = f"https://api.vatsim.net/v2/members/{vatsim_id}/flightplans"
    response = requests.get(url)
    if response.status_code == 200:
        flightplans = response.json()
        if flightplans:
            return flightplans[0]  
    return None

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

def construct_route(request, vatsim_id):
    """Constructs a route from VATSIM flight plan's waypoints, including departure and arrival airports."""
    flight_plan = fetch_flightplan_from_vatsim(vatsim_id)
    if not flight_plan:
        return JsonResponse({'error': 'Flight plan not found'}, status=404)

    # Extract route and airport identifiers
    dep_ident = flight_plan.get('dep', '')
    arr_ident = flight_plan.get('arr', '')
    route = flight_plan.get('route', '')

    # Find airports in the database
    try:
        departure_airport = Airport.objects.get(ident=dep_ident)
        arrival_airport = Airport.objects.get(ident=arr_ident)
    except Airport.DoesNotExist:
        return JsonResponse({'error': 'Airport not found'}, status=404)

    waypoint_identifiers = extract_waypoints_from_route(route)
    ordered_waypoints = match_waypoints_in_db(waypoint_identifiers)

    distance_threshold = 1000

    # Initialize the list of waypoints data, starting with the departure airport
    waypoints_data = [{
        'ident': departure_airport.ident,
        'latitude_deg': departure_airport.latitude_deg,
        'longitude_deg': departure_airport.longitude_deg
    }]

    # Iterate over the waypoints, skipping those too far away from the previous one
    for i in range(len(ordered_waypoints)):
        prev_wp = waypoints_data[-1] if waypoints_data else departure_airport
        curr_wp = ordered_waypoints[i]
        distance = haversine(prev_wp['latitude_deg'], prev_wp['longitude_deg'], curr_wp.latitude_deg, curr_wp.longitude_deg)

        if distance <= distance_threshold:
            waypoints_data.append({
                'ident': curr_wp.ident,
                'latitude_deg': curr_wp.latitude_deg,
                'longitude_deg': curr_wp.longitude_deg
            })

    # Add the arrival airport to the end of the waypoints data
    waypoints_data.append({
        'ident': arrival_airport.ident,
        'latitude_deg': arrival_airport.latitude_deg,
        'longitude_deg': arrival_airport.longitude_deg
    })

    return JsonResponse({'waypoints': waypoints_data})




def import_waypoints_data(request):
    # Hardcoded path to your CSV file
    csv_file_path = 'staticfiles/data/waypoint_data.csv'
    
    results = pd.read_csv(csv_file_path)
    length = len(results)


    with open(csv_file_path, newline='') as csv_file:
        reader = csv.reader(csv_file)
        next(reader, None)  # Skip the header row if your CSV has one
        for index, row in enumerate(reader, start=1):
            ident, latitude_deg, longitude_deg = row  # Adjust according to your CSV structure
            
            # Attempt to find a Waypoint with the same ident, latitude_deg, and longitude_deg
            waypoint_exists = Waypoint.objects.filter(
                ident=ident,
                latitude_deg=float(latitude_deg),
                longitude_deg=float(longitude_deg)
            ).exists()

            # If the waypoint does not exist, create it
            if not waypoint_exists:
                Waypoint.objects.create(
                    ident=ident,
                    latitude_deg=float(latitude_deg),
                    longitude_deg=float(longitude_deg)
                )

            print(f"Processed {index} of {length} waypoints")
    return HttpResponse("Waypoints imported successfully, duplicates skipped.", status=200)

async def fetch_flight_plan(session, vatsim_id, index, count_members):
    print(f"Fetching flight plan for {vatsim_id}. {index} of {count_members}")
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

async def fetch_and_save_inbound_flights():
    online_members_url = 'https://api.vatsim.net/v2/members/online'
    async with aiohttp.ClientSession() as session:
        async with session.get(online_members_url) as response:
            if response.status == 200:
                online_members = await response.json()

                count_members = len(online_members)
                tasks = [fetch_flight_plan(session, member['id'], index + 1, count_members) for index, member in enumerate(online_members)]

                flight_plans = await asyncio.gather(*tasks)

                for plan in flight_plans:
                    if plan:
                        await save_flight_plan_to_db(plan)
                print("Flight plans updated in the database.")

def inbound_flights(request):
    asyncio.run(fetch_and_save_inbound_flights())
    return JsonResponse({'status': 'Flight plans updated in the database.'})