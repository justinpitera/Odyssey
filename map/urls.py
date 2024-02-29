from django.urls import path
from .views import aircraft_data, aircraft_map, waypoints_view, waypoint_coordinates, airports_view

urlpatterns = [
    path('', aircraft_map, name='map'),
    path('api/aircraft/telemetry', aircraft_data, name='aircraft_telemetry'),
    path('api/waypoints/', waypoints_view, name='waypoints'),
    path('api/waypoint-coordinates/<str:name>/', waypoint_coordinates, name='waypoint_coordinates'),
    path('api/airports/', airports_view, name='airports'),
]
