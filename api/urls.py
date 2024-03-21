from django.urls import path
from .views import *

urlpatterns = [
    path('app_closed/', AppClosedNotification.as_view(), name='app-closed-notification'),
    path('app_opened/', AppOpenedNotification.as_view(), name='app-opened-notification'),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('validate_login/', validate_user_login, name='validate_login'),
    path('update_current_altitude/', update_current_altitude, name='update_current_altitude'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('flight/activate/', activate_flight, name='activate-flight'),
    path('flight/deactivate/', deactivate_flight, name='deactivate-flight'),
    path('flight/active/update_telemetry/', update_active_flight_telemetry, name='update_active_flight_telemetry'),
]