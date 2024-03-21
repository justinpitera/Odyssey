import csv
from datetime import datetime, timedelta
import json

from xml.etree import ElementTree
from django.http import HttpResponse, JsonResponse
from django.shortcuts import  render
from map.models import Airline
from map.forms import ControllerForm
from map.ivaoUtility import fetch_ivao_map_data, is_ivao_id
from map.models import Airport, Controller
from schedule.models import Flight

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

from map.vatsimUtility import *

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
            'page_title': 'Simtrail Network',
            'userLat': userLat,
            'userLon': userLon
        }
    except Flight.DoesNotExist:
        aircraft = Flight.objects.filter(is_active=True)
        context = {
            'aircraft': aircraft,
            'page_title': 'Simtrail',
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



from map.timeUtility import get_local_time_from_ident, get_standard_time_of_arrival, convert_to_normal_time

def process_flight(flight, airport_ident, source_type):
    '''Processes a single flight and returns its details if it is relevant to the specified airport.'''
    # Initialize common variables; some might need adjustments based on the source type
    vatsimID = None
    departureTime = None  # Placeholder, calculate based on available data
    enrouteTime = None  # Placeholder, might need to calculate or may not be available
    arrivalTime = None  # Placeholder, calculate based on available data
    airline = "N/A"  # Default value, adjust as necessary

    if source_type == 'vatsim':
        from django.core.exceptions import ObjectDoesNotExist

        if flight['arrival'] == airport_ident or flight['departure'] == airport_ident:
            vatsimID = flight['cid']
            departureTime = convert_to_normal_time(flight['deptime'])
            enrouteTime = flight['enroute_time']
            arrivalTime = get_standard_time_of_arrival(flight['deptime'], flight['enroute_time'])
            try:
                airline_query = Airline.objects.filter(icao=flight['callsign'][:3]).only('name')
                airline = airline_query.first().name if airline_query.exists() else "N/A"
            except ObjectDoesNotExist:
                airline = "N/A"
            # Airline logic remains the same as in your original function
            # Add additional VATSIM-specific processing here
    elif source_type == 'ivao':
        if flight['arrival'] == airport_ident or flight['departure'] == airport_ident:
            departureTime = "Unknown"  # This would need your logic to determine or convert
            enrouteTime = "Unknown"  # Depending on whether you can calculate or have equivalent data
            arrivalTime = "Unknown"  # Similar to departureTime, requires conversion or calculation
            try:
                airline_query = Airline.objects.filter(icao=flight['callsign'][:3]).only('name')
                airline = airline_query.first().name if airline_query.exists() else "N/A"
            except ObjectDoesNotExist:
                airline = "N/A"

    # Common processing continues here, assuming you can normalize some data between the two sources
    flight_info = {
            'callsign': flight['callsign'],
            'departure': flight['departure'],
            'arrival': flight['arrival'],
            'aircraft': flight['aircraft_short'],
            'cruise_speed': flight['cruise_tas'],
            'altitude': flight['altitude'],
            'route': flight['route'],  
            'departureTime': departureTime,
            'enrouteTime': enrouteTime,
            'arrivalTime': arrivalTime,
            'airline': airline,
            'latitude': flight['latitude'],
            'longitude': flight['longitude'],
            'distanceRemaining': 10 # This assumes distanceRemaining is meaningful for both arrivals and departures
    }
    return flight_info if flight_info['departure'] == airport_ident or flight_info['arrival'] == airport_ident else None



def airport_details(request, airport_ident):
    '''Returns details of the specified airport, including arrivals and departures from VATSIM and IVAO.'''
    vatsim_data = fetch_flight_data()  # Make sure this fetches VATSIM flight data
    ivao_data = fetch_ivao_map_data()  # Make sure this fetches IVAO flight data

    if vatsim_data is None and ivao_data is None:
        return JsonResponse({'error': 'Failed to fetch flight data'}, status=500)

    all_flights = []
    # Initialize counters
    vatsim_arrivals = vatsim_departures = ivao_arrivals = ivao_departures = 0

    # Process VATSIM flights if available
    if vatsim_data is not None:
        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(process_flight, flight, airport_ident, 'vatsim') for flight in process_flight_data(vatsim_data)]
            for future in futures:
                result = future.result()
                if result:
                    if result['arrival'] == airport_ident:
                        vatsim_arrivals += 1
                    elif result['departure'] == airport_ident:
                        vatsim_departures += 1
                    all_flights.append(result)

    # Process IVAO flights if available
    if ivao_data is not None:
        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(process_flight, flight_details, airport_ident, 'ivao') for flight_details in ivao_data.values()]
            for future in futures:
                result = future.result()
                if result:
                    if result['arrival'] == airport_ident:
                        ivao_arrivals += 1
                    elif result['departure'] == airport_ident:
                        ivao_departures += 1
                    all_flights.append(result)

    arrivals = [flight for flight in all_flights if flight['arrival'] == airport_ident]
    departures = [flight for flight in all_flights if flight['departure'] == airport_ident]

    try:
        airport = Airport.objects.only('name', 'ident', 'iso_region').get(ident=airport_ident)
    except Airport.DoesNotExist:
        return JsonResponse({'error': 'Airport not found'}, status=404)

    airportName = airport.name
    airportIdent = airport.ident
    airportRegion = airport.iso_region
    airportLocalTime = get_local_time_from_ident(request, airport_ident)
    
    return JsonResponse({
        'arrivals': arrivals,
        'departures': departures,
        'vatsimArrivals': vatsim_arrivals,
        'vatsimDepartures': vatsim_departures,
        'ivaoArrivals': ivao_arrivals,
        'ivaoDepartures': ivao_departures,
        'airportName': airportName,
        'airportIdent': airportIdent,
        'airportRegion': airportRegion,
        'airportLocalTime': airportLocalTime,
    })



def user_location(request, type):
    '''Returns the latitude and longitude of a user based on their network ID.'''
    identifier = request.GET.get('identifier', '')
    
    # Assuming which_network() correctly identifies the network based on the identifier
    network = which_network(request, identifier)

    if network == 'IVAO':
        # Handle IVAO case (not implemented here)
        return JsonResponse({'error': 'IVAO not supported'}, status=400)

    elif network == 'VATSIM':
        latitude, longitude = get_vatsim_user_location(request=request, vatsim_id=identifier)
        if latitude is not None and longitude is not None:
            # Found the VATSIM user's location
            location_data = {
                'location': {
                    'lat': latitude,
                    'lon': longitude
                }
            }
            return JsonResponse(location_data)
        else:
            # VATSIM user not found or no location data available
            return JsonResponse({'error': 'VATSIM user not found or no location data'}, status=404)
    
    else:
        # Handle case where network is neither IVAO nor VATSIM
        return JsonResponse({'error': 'Unknown network'}, status=400)
    
async def fetch_and_save_inbound_flights():
    '''Fetches flight plans of online VATSIM members and saves them to the database.'''
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


def which_network(request, network_id):
    network_id = int(network_id)
    if is_vatsim_id(request, network_id):
        return 'VATSIM'
    elif is_ivao_id(request, network_id):
        return 'IVAO'
    else:
        return JsonResponse({'error': 'Invalid network ID'}, status=400)

@csrf_exempt
def import_airline_data(request):
    csv_file_path = 'staticfiles/data/airlines.csv'  # Ensure this path is correct and accessible
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Check if ICAO is 'N/A' or empty and replace it with None
            icao = row['ICAO'] if row['ICAO'] not in ('N/A', '') else None


           # Skip rows where Name or ICAO is 'N/A', empty, or ICAO is not exactly 3 letters
            if row['Name'] in ('N/A', '') or row['ICAO'] in ('N/A', '') or len(row['ICAO']) != 3:
                continue
            # Using get_or_create correctly to handle existing records
            airline, created = Airline.objects.get_or_create(
                name=row['Name'], 
                defaults={
                    'icao': icao,
                }
            )
            if created:
                print(f"Created airline: {airline.name}")
            else:
                print(f"Airline already exists: {airline.name}")

    return HttpResponse('Airline data imported successfully.')

