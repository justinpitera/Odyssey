from datetime import datetime, timedelta
import pytz
from timezonefinder import TimezoneFinder
from map.models import Airport

def get_local_time_from_ident(request, airport_ident):
    '''Returns the local time of the airport with the given ident.'''
    latitude = Airport.objects.get(ident=airport_ident).latitude_deg
    longitude = Airport.objects.get(ident=airport_ident).longitude_deg

    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=longitude, lat=latitude) 

    timezone = pytz.timezone(timezone_str)
    current_local_time = datetime.now(timezone)

    # Format the date and time
    formatted_date = current_local_time.strftime("%m-%d-%y")
    formatted_time = current_local_time.strftime("%H:%M")


    return formatted_date + " " + formatted_time

def get_standard_time_of_arrival(dep_time, enroute_time):
    '''Returns the standard time of arrival given the departure time and enroute time.'''
    # Convert departure time string to datetime object
    deptime_obj = datetime.strptime(dep_time, "%H%M")
    
    # Convert enroute time string to timedelta object
    enroute_time = timedelta(hours=int(enroute_time[:2]), minutes=int(enroute_time[2:]))
    
    # Calculate arrival time
    arrival_time_obj = deptime_obj + enroute_time
    
    # Format the arrival time as a string in the desired format
    arrival_normal_time = arrival_time_obj.strftime("%I:%M %p")
    
    return arrival_normal_time

def convert_to_normal_time(time_str):
    '''Converts a 24-hour time string to a normal time string.'''
    # Convert the time string to a datetime object
    time_obj = datetime.strptime(time_str, "%H%M")
    
    # Format the datetime object as a string in the desired format
    normal_time = time_obj.strftime("%I:%M %p")
    
    return normal_time