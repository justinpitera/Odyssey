import csv

from django.http import HttpResponse
import pandas as pd
from map.models import Airport, Waypoint
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

