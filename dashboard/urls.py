from django.urls import path
from .views import *

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('update_hours/', update_flight_hours_view, name='update_hours'),
    path('update_hours/<int:user_id>/<int:new_hours>', update_user_flight_hours, name='update_user_flight_hours'),
    path('make_staff/<int:user_id>/', make_user_staff, name='make_staff'),
    path('roadmap/', roadmap, name='roadmap'),
    
]