from django.db import models

class Flight(models.Model):
    flight_number = models.CharField(max_length=10)
    departure = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    aircraft = models.CharField(max_length=100)
    capacity = models.IntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    available_seats = models.IntegerField()
    current_altitude = models.IntegerField(default=0)
    target_altitude = models.IntegerField(default=0)
    landing_rate = models.IntegerField(default=0)
    is_active = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='flights', null=True, blank=True)
    flight_plan = models.URLField(null=True, blank=True) # Simbrief flight plan URL

    # Aircraft telemetry data
    aircraft_vertical_speed = models.IntegerField(default=0)
    aircraft_longitude = models.DecimalField(max_digits=9, decimal_places=6, default=0)
    aircraft_latitude = models.DecimalField(max_digits=9, decimal_places=6, default=0)
    aircraft_heading = models.IntegerField(default=0)
    aircraft_ground_speed = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.flight_number} - {self.departure} to {self.destination}'