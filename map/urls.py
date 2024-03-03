from django.urls import path
from .views import aircraft_data, aircraft_map, waypoints_view, waypoint_coordinates, airports_view, search_airports, import_airports_from_csv, fetch_vatsim_data, search_vatsim

urlpatterns = [
    path('', aircraft_map, name='map'),
    path('api/aircraft/telemetry', aircraft_data, name='aircraft_telemetry'),
    path('api/waypoints/', waypoints_view, name='waypoints'),
    path('api/waypoint-coordinates/<str:name>/', waypoint_coordinates, name='waypoint_coordinates'),
    path('api/airports/', airports_view, name='airports'),
    path('search-airports/', search_airports, name='search-airports'),
    path('import-airports/', import_airports_from_csv, name='import-airports'),
    path('vatsim-data/', fetch_vatsim_data, name='fetch-vatsim-data'),
    path('search_vatsim', search_vatsim, name='search_airport'),  # For class-based
]
