from django.urls import path
from .views import (
    aircraft_data,
    aircraft_map,
    waypoints_view,
    waypoint_coordinates,
    airports_view,
    search_airports,
    import_airports_from_csv,
    fetch_vatsim_data,
    fetch_controller_division,
    search_vatsim,
    update_vatsim_controllers,
    controllers_data,
    add_controller,
    is_online,
    construct_route,
    import_waypoints_data,
)

urlpatterns = [
    path('', aircraft_map, name='map'),
    path('api/aircraft/telemetry', aircraft_data, name='aircraft_telemetry'),
    path('api/waypoints/', waypoints_view, name='waypoints'),
    path('api/waypoint-coordinates/<str:name>/', waypoint_coordinates, name='waypoint_coordinates'),
    path('api/airports/', airports_view, name='airports'),
    path('api/search-airports/', search_airports, name='search-airports'),
    path('api/import-airports/', import_airports_from_csv, name='import-airports'),
    path('api/vatsim-data/', fetch_vatsim_data, name='fetch-vatsim-data'),
    path('api/search_vatsim', search_vatsim, name='search_airport'),  
    path('api/fetch_controller_division/<int:id>', fetch_controller_division, name='fetch_controller_divisions'),
    path('api/update_vatsim_controllers', update_vatsim_controllers, name='update_vatsim_controllers'),
    path('api/controllers/', controllers_data, name='controllers_data'),
    path('add_controller/', add_controller, name='add-controller'),
    path('api/is_online/<int:vatsim_id>', is_online, name='is_online'),
    path('api/construct_route/<int:vatsim_id>', construct_route, name='construct_route'),
    path('api/important_waypoints_data', import_waypoints_data, name='import_waypoints_data'),

]
