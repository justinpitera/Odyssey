from django.urls import path
from .views import *

urlpatterns = [
    path('', schedule, name='schedule'),
    path('create/', create_flight, name='create_flight'),
    path('flight', flight, name='flight'),
    path('generate_schedule/<int:user_id>/', generate_schedule, name='generate-schedule'),
    path('api/flight/<int:flight_id>/update_altitude/', update_altitude, name='update-altitude'),
    path('api/flight/<int:flight_id>/update_landing_rate/', update_landing_rate, name='update-landing-rate'),
    
    path('generate_and_store_flight_plan/<int:flight_id>', generate_and_store_flight_plan, name='generate_and_store_flight_plan'),
]

