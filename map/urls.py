from django.urls import path
from .views import aircraft_data, aircraft_map, waypoints_view, waypoint_coordinates, airports_view, search_airports, import_airports_from_csv, fetch_vatsim_data, fetch_controller_division, search_vatsim, update_vatsim_controllers, controllers_data, add_controller

urlpatterns = [
    path('', aircraft_map, name='map'),
    path('api/aircraft/telemetry', aircraft_data, name='aircraft_telemetry'),
    path('api/waypoints/', waypoints_view, name='waypoints'),
    path('api/waypoint-coordinates/<str:name>/', waypoint_coordinates, name='waypoint_coordinates'),
    path('api/airports/', airports_view, name='airports'),
    path('search-airports/', search_airports, name='search-airports'),
    path('import-airports/', import_airports_from_csv, name='import-airports'),
    path('vatsim-data/', fetch_vatsim_data, name='fetch-vatsim-data'),
    path('search_vatsim', search_vatsim, name='search_airport'),  
    path('fetch_controller_division/<int:id>', fetch_controller_division, name='fetch_controller_divisions'),
    path('update_vatsim_controllers', update_vatsim_controllers, name='update_vatsim_controllers'),
    path('api/controllers/', controllers_data, name='controllers_data'),
    path('add_controller/', add_controller, name='add-controller'),
]
