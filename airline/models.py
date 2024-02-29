from django.db import models

class Airline(models.Model):
    name = models.CharField(max_length=255, unique=True)
    iata_code = models.CharField(max_length=2, unique=True, blank=True, null=True)
    icao_code = models.CharField(max_length=3, unique=True, blank=True, null=True) 
    country = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='airline_logos/', blank=True, null=True) 

    def __str__(self):
        return self.name
