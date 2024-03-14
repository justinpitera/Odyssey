from django.db import models

class Airport(models.Model):
    ident = models.CharField(max_length=10, unique=True)
    type = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    latitude_deg = models.FloatField()
    longitude_deg = models.FloatField()
    elevation_ft = models.IntegerField(null=True, blank=True)
    continent = models.CharField(max_length=2)
    iso_country = models.CharField(max_length=2)
    iso_region = models.CharField(max_length=7)

    def __str__(self):
        return f"{self.name} ({self.ident})"


from django.db import models

class Airport(models.Model):
    ident = models.CharField(max_length=10, unique=True)
    type = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    latitude_deg = models.FloatField()
    longitude_deg = models.FloatField()
    elevation_ft = models.IntegerField(null=True, blank=True)
    continent = models.CharField(max_length=2)
    iso_country = models.CharField(max_length=2)
    iso_region = models.CharField(max_length=7)

    def __str__(self):
        return f"{self.name} ({self.ident})"
    




class Controller(models.Model):
    ident = models.CharField(max_length=4)
    latitude_deg = models.FloatField()
    longitude_deg = models.FloatField()
    frequency = models.FloatField(default=0, null=True, blank=True)
    type = models.CharField(max_length=3)
    division = models.CharField(max_length=10, null=True, blank=True)
    vatsim_id = models.IntegerField()
    airport = models.ForeignKey(Airport, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    is_online = models.BooleanField(default=False)
    geoname = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.name = '{}_{}'.format(self.ident, self.type)
        super(Controller, self).save(*args, **kwargs)

class Waypoint(models.Model):
    ident = models.CharField(max_length=10)
    latitude_deg = models.FloatField()
    longitude_deg = models.FloatField()

    def __str__(self):
        return f"{self.name} ({self.ident})"

class VATSIMFlight(models.Model):
    vatsim_id = models.IntegerField()
    callsign = models.CharField(max_length=10)
    departure = models.CharField(max_length=4)
    arrival = models.CharField(max_length=4)
    aircraft = models.CharField(max_length=255)
    cruise_speed = models.IntegerField()
    altitude = models.IntegerField()
    route = models.TextField()
    
    def __str__(self):
        return f"{self.callsign} ({self.vatsim_id})"
class Airline(models.Model):
    name = models.CharField(max_length=255)
    icao = models.CharField(max_length=4, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.icao})"