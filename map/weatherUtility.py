import csv
import os
from django.conf import settings
import requests
import gzip
import shutil
from django.http import HttpResponse, JsonResponse
from map.mathUtility import haversine, convert_inhg_to_mb
from map.models import Airport
# Initial headers setup
user_agent = 'SimTrail/1.0 (SimTrail; https://simtrail.com/)'
headers = {
    'User-Agent': user_agent
}

def fetch_metars(request):
    # Get the METAR data from the Aviation Weather Center
    zip_file_url = 'https://aviationweather.gov/data/cache/metars.cache.csv.gz'
    temp_zip_path = 'temp_metars.zip'
    file_path_metars = os.path.join(settings.STATIC_ROOT, 'data', 'metars.csv')
    try:
        # Download the ZIP file
        response = requests.get(zip_file_url, headers=headers)
        response.raise_for_status()  # Check if the download was successful


        
        # Save the ZIP file
        with open(temp_zip_path, 'wb') as temp_zip:
            temp_zip.write(response.content)

        with gzip.open('temp_metars.zip', 'rb') as f_in:
            with open(file_path_metars, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        # delete the temporary ZIP file after extraction
        os.remove(temp_zip_path)

        # Get Tafs from the same source
        zip_file_url = 'https://aviationweather.gov/data/cache/tafs.cache.csv.gz'
        temp_zip_path = 'temp_tafs.zip'
        file_path_tafs = os.path.join(settings.STATIC_ROOT, 'data', 'tafs.csv')

        # Download the ZIP file
        response = requests.get(zip_file_url, headers=headers)
        response.raise_for_status()  # Check if the download was successful

        # Save the ZIP file
        with open(temp_zip_path, 'wb') as temp_zip:
            temp_zip.write(response.content)

        with gzip.open('temp_tafs.zip', 'rb') as f_in:
            with open(file_path_tafs, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        # delete the temporary ZIP file after extraction
        os.remove(temp_zip_path)

        return HttpResponse("Files downloaded and extracted successfully.")
    except Exception as e:
        # Handle errors
        return HttpResponse(f"An error occurred: {e}")

def find_closest_metar_or_taf(file_path, airport, metar_file_path):
    closest_metar_taf = None
    closest_metar = None  # To store the closest METAR
    min_distance = float('inf')
    min_distance_metar = float('inf')

    # First, find the closest METAR for supplementary data
    with open(metar_file_path, newline='') as csvfile:
        for _ in range(5):  # Skip headers
            next(csvfile)
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not row.get('latitude') or not row.get('longitude'):
                continue
            current_distance = haversine(float(row['longitude']), float(row['latitude']),
                                         airport.longitude_deg, airport.latitude_deg)
            if current_distance < min_distance_metar:
                min_distance_metar = current_distance
                closest_metar = row

    # Then, find the closest entry in the specified file (METAR or TAF)
    with open(file_path, newline='') as csvfile:
        for _ in range(5):
            next(csvfile)
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not row.get('latitude') or not row.get('longitude'):
                continue
            if row.get('station_id') == airport.ident:
                return row, 0, closest_metar  # Return the matching data with distance 0 and closest METAR
            current_distance = haversine(float(row['longitude']), float(row['latitude']),
                                         airport.longitude_deg, airport.latitude_deg)
            if current_distance < min_distance:
                min_distance = current_distance
                closest_metar_taf = row

    return closest_metar_taf, min_distance, closest_metar


def get_metar(request, ident):
    # Remove this if using for a separate utility, replace with another csv scan for airports.csv
    try:
        airport = Airport.objects.get(ident=ident)
    except Airport.DoesNotExist:
        return JsonResponse({'error': 'Airport not found'}, status=404)

    metar_file_path = os.path.join(settings.STATIC_ROOT, 'data', 'metars.csv')
    taf_file_path = os.path.join(settings.STATIC_ROOT, 'data', 'tafs.csv')

    # Find the closest METAR and TAF, along with the closest METAR for augmentation
    closest_metar, metar_distance, _ = find_closest_metar_or_taf(metar_file_path, airport, metar_file_path)
    closest_taf, taf_distance, closest_metar_for_taf = find_closest_metar_or_taf(taf_file_path, airport, metar_file_path)

    if closest_metar or closest_taf:
        # If both METAR and TAF are found, decide based on the shortest distance
        if closest_taf and (not closest_metar or taf_distance < metar_distance):
            # If TAF is chosen but lacks certain data, augment it with data from the closest METAR
            for key in ['wind_dir_degrees', 'wind_speed_kt', 'altim_in_hg']:
                if key not in closest_taf or not closest_taf[key]:
                    closest_taf[key] = closest_metar_for_taf.get(key)
            if 'altim_in_hg' not in closest_taf:
                # Convert altim_in_hg from METAR and add to TAF
                altim_in_hg = closest_metar_for_taf.get('altim_in_hg')
                if altim_in_hg:
                    altim_in_hg = float(altim_in_hg)  # Ensure it's a float for conversion
                    closest_taf['altim_in_mb'] = convert_inhg_to_mb(altim_in_hg)
            return JsonResponse(closest_taf, safe=False)
        else:
            # Convert altim_in_hg from METAR to mb/hPa before returning, if present
            if 'altim_in_hg' in closest_metar:
                altim_in_hg = float(closest_metar['altim_in_hg'])  # Ensure it's a float for conversion
                closest_metar['altim_in_mb'] = convert_inhg_to_mb(altim_in_hg)
            return JsonResponse(closest_metar, safe=False)
    else:
        return JsonResponse({'error': 'METAR/TAF information not found'}, status=404)


