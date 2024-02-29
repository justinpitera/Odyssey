from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from accounts.models import User
from schedule.forms import FlightForm
from schedule.models import Flight
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import random
import csv
from django.conf import settings
import os
from datetime import datetime
from django.db.models.functions import ExtractWeekDay
from .models import Flight

@login_required
def schedule(request):
    page_title = 'Schedule - Odyssey'

    # Retrieve flights for the current user, ordered by departure time (closest date first)
    flights = Flight.objects.filter(user=request.user).order_by('departure_time')
    has_active_flights = any(flight.is_active for flight in flights)

    context = {
        'page_title': page_title,
        'flights': flights,
        'has_active_flights': has_active_flights,
    }

    return render(request, 'schedule/schedule.html', context)


def create_flight(request):
    if request.method == 'POST':
        form = FlightForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('schedule')  # Assuming you have a view that lists all flights
    else:
        form = FlightForm()
    return render(request, 'schedule/create_flight.html', {'form': form})


@csrf_exempt  
@require_http_methods(["POST"])  
def update_altitude(request, flight_id):
    new_altitude = request.POST.get('new_altitude', None)
    if not new_altitude:
        return JsonResponse({'error': 'Missing new altitude'}, status=400)

    try:
        flight = Flight.objects.get(id=flight_id)
        flight.current_altitude = new_altitude  
        flight.save()
        return JsonResponse({'success': True})
    except Flight.DoesNotExist:
        return JsonResponse({'error': 'Flight not found'}, status=404)
    


    
@csrf_exempt  # Disable CSRF protection for this view
@require_http_methods(["POST"])  
def update_landing_rate(request, flight_id):
    landing_rate = request.POST.get('landing_rate', None)
    if not landing_rate:
        return JsonResponse({'error': 'Missing landing rate'}, status=400)

    try:
        flight = Flight.objects.get(id=flight_id)
        flight.landing_rate = landing_rate  # Assuming your model attribute is current_altitude
        flight.save()
        return JsonResponse({'success': True})
    except Flight.DoesNotExist:
        return JsonResponse({'error': 'Flight not found'}, status=404)
        

@login_required
def generate_schedule(request, user_id):
    user = request.user
    if user.id != int(user_id):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    k_airports = get_k_airports()  
    if not k_airports:
        return JsonResponse({'error': 'No K-airports found'}, status=500)

    start_date = timezone.now()
    work_days = sorted(random.sample(range(7), 5))  # Choose and sort 5 random days for the pilot to work

    # Initialize storage for scheduled flights
    scheduled_flights = {day: [] for day in work_days}  # Each day will hold a list of (start, end) times
    daily_work_hours = {day: 0 for day in work_days}  # Track work hours per day
    total_work_hours = 0  # Track total work hours in the week
    weekly_hour_limit = 10  # Define weekly work hours limit
    daily_hour_limit = 2  # Assuming a max of 2 hours of flights can be scheduled per day for simplicity

    for day in work_days:
        while daily_work_hours[day] < daily_hour_limit and total_work_hours < weekly_hour_limit:
            departure_airport_icao = random.choice(k_airports)
            destination_airport_icao = random.choice([airport for airport in k_airports if airport != departure_airport_icao])

            # Loop to ensure generated flight time does not conflict and does not exceed daily or weekly limit
            conflict = True  # Assume conflict to enter the loop
            while conflict:
                random_hour = random.randint(6, 21)  # Adjusted to ensure within work hours
                random_minute = random.randint(0, 59)
                departure_time = start_date + timedelta(days=day, hours=random_hour, minutes=random_minute)

                # Assume each flight lasts an average of 2 hours
                potential_end_time = departure_time + timedelta(hours=2)
                if daily_work_hours[day] + 2 > daily_hour_limit or total_work_hours + 2 > weekly_hour_limit:
                    break  # Stop trying to schedule more flights for this day if limit is exceeded

                # Check for time conflict
                conflict = False
                for start, end in scheduled_flights[day]:
                    if not (potential_end_time <= start or departure_time >= end):
                        conflict = True
                        break

                if not conflict:
                    scheduled_flights[day].append((departure_time, potential_end_time))
                    daily_work_hours[day] += 2  # Add 2 hours to the daily work hours
                    total_work_hours += 2  # Add 2 hours to the total work hours

            if conflict:  # If unable to schedule a new flight due to conflict, break to try next day
                break

            # Only create flight objects if no conflict for the day and within work hour limits
            if not conflict and daily_work_hours[day] <= daily_hour_limit and total_work_hours <= weekly_hour_limit:
                departure_icao = departure_airport_icao['icao']
                destination_icao = destination_airport_icao['icao']
                Flight.objects.create(
                    user=User.objects.get(id=user_id),
                    flight_number=f"{random.randint(1000, 9999)}",
                    departure=departure_icao,
                    destination=destination_icao,
                    departure_time=departure_time,
                    aircraft="Boeing 737",
                    capacity=160,
                    price=random.randint(100, 500),
                    available_seats=random.randint(50, 160),
                    current_altitude=0,
                    target_altitude=35000,
                    landing_rate=0,
                    is_active=False,
                    completed=False
                )

    return redirect('schedule')


def get_k_airports():
    k_airports = []
    file_path = os.path.join(settings.STATIC_ROOT, 'data', 'airport_data.csv')
    exclude_keywords = ['base', 'military', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']  # Exclude airports with these keywords

    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['ident'].startswith('L') and row['type'] == 'large_airport' or row['ident'].startswith('K') and row['type'] == 'large_airport' or row['ident'].startswith('E') and row['type'] == 'large_airport':
                if not any(keyword in row['name'].lower() for keyword in exclude_keywords):
                    k_airports.append({'icao': row['ident']})
    return k_airports


def generate_flight_plan(departure, destination):
    # Assume a simple flight plan generation based on departure and destination
    return f"https://dispatch.simbrief.com/options/custom?airline=&fltnum=&orig={departure}&dest={destination}&altn=&basetype=B737"

def generate_and_store_flight_plan(request, flight_id):
    # Ensure the user is authenticated and has the right permissions
    if not request.user.is_authenticated:
        return HttpResponse("You need to be logged in to perform this action.", status=401)

    flight = get_object_or_404(Flight, pk=flight_id)

    # Generate the flight plan URL
    flight_plan_url = generate_flight_plan(flight.departure, flight.destination)

    # Store the flight plan URL in the database
    flight.flight_plan = flight_plan_url
    flight.save()

    return redirect('schedule')


@login_required
def flight(request):
    # Fetch the active flight for the current user
    try:
        active_flight = Flight.objects.get(user=request.user, is_active=True)
        # If an active flight exists, pass it to your template or return it as a JSON response
        context = {
            'active_flight': active_flight,
        }
        return render(request, 'schedule/active_flight.html', context)
    except Flight.DoesNotExist:
        # If no active flight exists for the user, handle accordingly (e.g., show a message or redirect)
        return HttpResponse('No active flight found for the user.', status=404)







