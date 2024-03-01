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
