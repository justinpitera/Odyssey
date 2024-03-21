from django.urls import path
from .views import (
    aircraft_data,
    aircraft_map,
    airports_view,
    fetch_controller_division,
    update_vatsim_controllers,
    controllers_data,
    inbound_flights,
    airport_details,
    aircraft_card,
    get_local_time_from_ident,
    vatsim_flight_details,
    import_airline_data,
    fetch_vatsim_flight_data,
    user_location,
    which_network,
)
from map.ivaoUtility import fetch_ivao_network
from map.vatsimUtility import fetch_vatsim_data
from map.searchUtility import *
from map.routeUtility import construct_route

urlpatterns = [
    path('', aircraft_map, name='map'),
    path('api/aircraft/telemetry', aircraft_data, name='aircraft_telemetry'),
    path('api/airports/', airports_view, name='airports'),
    path('api/fetch_controller_division/<int:id>', fetch_controller_division, name='fetch_controller_divisions'),
    path('api/update_vatsim_controllers', update_vatsim_controllers, name='update_vatsim_controllers'),
    path('api/controllers/', controllers_data, name='controllers_data'),
    path('api/inbound_flights/', inbound_flights, name='inbound_flights'),
    path('api/airport_details/<str:airport_ident>/', airport_details, name='airport-details'),
    path('aircraft_card', aircraft_card, name='aircraft-card'),
    path('api/get_local_time_from_ident/<str:ident>/', get_local_time_from_ident, name='get_local_time_from_ident'),
    path('api/vatsim_flight_details/', vatsim_flight_details, name='vatsim_flight_details'),
    path('api/import_airline_data', import_airline_data, name='import_airline_data'),
    path('api/fetch_flight_data/', fetch_vatsim_flight_data, name='fetch_flight_data'),
    path('api/<str:type>-dataView/', user_location, name='user_location'),
    path('api/which_network/<str:network_id>', which_network, name='which_network'),
    path('api/ivao_network/', fetch_ivao_network, name='ivao_network'),
    path('api/vatsim_network/',fetch_vatsim_data, name='vatsim_network'),
    path('search_airports/', search_airports, name='search_airports'),
    path('api/construct_route/<int:network_id>/', construct_route, name='construct_route'),
]
