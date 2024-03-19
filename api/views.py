from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from api.models import ApplicationStatus
from rest_framework_simplejwt.views import TokenObtainPairView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from django.views.decorators.http import require_http_methods

from schedule.models import Flight
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import datetime
from django.contrib.auth import authenticate

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    pass
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)


        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Calculate expires_in for the access token
        access_token = self.get_token(self.user)
        expires_in = access_token['exp'] - int(datetime.datetime.utcnow().timestamp())
        data['expires_in'] = expires_in



        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@permission_classes([IsAuthenticated]) 
class AppClosedNotification(APIView):

    def post(self, request, format=None):
        user = request.user
        app_status, created = ApplicationStatus.objects.get_or_create(user=user)
        app_status.is_closed = True
        app_status.save()

        return Response({"message": "Application status updated for user: " + user.username}, status=status.HTTP_200_OK)

@permission_classes([IsAuthenticated]) 
class AppOpenedNotification(APIView):

    def post(self, request, format=None):
        user = request.user
        app_status, created = ApplicationStatus.objects.get_or_create(user=user)
        app_status.is_closed = False 
        app_status.save()

        return Response({"message": "Application status updated to opened for user: " + user.username}, status=status.HTTP_200_OK)


@api_view(['POST'])  # Specify that this view should accept POST requests only
@permission_classes([IsAuthenticated])  # Ensure the user is authenticated
async def update_user_flight_hours(request, new_hours):
    if not request.user.is_staff:
        return JsonResponse({"error": "You do not have permission to update flight hours."}, status=403)

    # Use the authenticated user directly
    user = request.user

    try:
        # Since new_hours is now directly passed as a parameter, just convert it to an integer
        if str(new_hours).isdigit():
            user.profile.hours = int(new_hours)  # Assuming you have a profile model related to your User model that stores hours
            await sync_to_async(user.profile.save)()
            return JsonResponse({"success": f"Flight hours updated successfully for {user.username}."})
        else:
            return JsonResponse({"error": "Invalid input. Please enter a valid number of flight hours."}, status=400)
    except Exception as e:  # A more generic catch to simplify, but consider catching specific exceptions as needed
        return JsonResponse({"error": "An error occurred while updating flight hours."}, status=500)
    

    
@api_view(['PATCH'])
@login_required
def activate_flight(request):
    flight = Flight.objects.filter(user=request.user).order_by('departure_time').first()
    
    if not flight:
        return Response({'error': 'No flights found for the user'}, status=status.HTTP_404_NOT_FOUND)
    flight.is_active = True
    flight.save()
    
    return Response({'status': f'Flight {flight.flight_number} activated successfully'}, status=status.HTTP_200_OK)





@api_view(['PATCH'])
@login_required
def deactivate_flight(request):
    flight = Flight.objects.filter(user=request.user).order_by('departure_time').first()
    
    if not flight:
        return Response({'error': 'No flights found for the user'}, status=status.HTTP_404_NOT_FOUND)
    flight.is_active = False
    flight.save()
    
    return Response({'status': f'Flight {flight.flight_number} deactivated successfully'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_current_altitude(request):
    user = request.user
    altitude = request.POST.get('altitude', None)

    if altitude is None:
        return JsonResponse({'error': 'Missing altitude parameter'}, status=400)

    try:
        altitude = int(altitude)
    except ValueError:
        return JsonResponse({'error': 'Invalid altitude value'}, status=400)

    try:
        flight = Flight.objects.filter(user=user).order_by('departure_time').first()
        
        if flight is None:
            return JsonResponse({'error': 'No flights available for this user'}, status=404)

        flight.current_altitude = altitude
        flight.save()

        return JsonResponse({'success': True, 'current_altitude': altitude})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]  # Allows access to anyone, since this is for refreshing tokens

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh', None)

        if refresh_token is None:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Attempt to create a new token using the refresh token
            refresh = RefreshToken(refresh_token)
            data = {'access': str(refresh.access_token)}

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def validate_user_login(request):
    # Extract username and password from the request data
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Attempt to authenticate the user
    user = authenticate(username=username, password=password)

    if user is not None:
        # The credentials are valid
        return Response({'success': True, 'message': 'User authenticated successfully.'}, status=status.HTTP_200_OK)
    else:
        # Authentication failed
        return Response({'success': False, 'message': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)
    


@api_view(['PUT'])  # Changed to accept PUT requests
@permission_classes([IsAuthenticated])
def update_active_flight_telemetry(request):
    # Find the active flight for the current user
    flight = get_object_or_404(Flight, user=request.user, is_active=True)

    # Update fields from request data if they exist
    telemetry_fields = ['aircraft_vertical_speed', 'aircraft_longitude', 'aircraft_latitude', 'aircraft_heading', 'aircraft_ground_speed','current_altitude']
    for field in telemetry_fields:
        if field in request.data:
            setattr(flight, field, request.data[field])
    
    flight.save()
    return Response({'message': 'Flight telemetry updated successfully'})



