from django import forms
from .models import Flight

class FlightForm(forms.ModelForm):
    class Meta:
        model = Flight
        fields = ['user','flight_number', 'departure', 'destination', 'departure_time', 'aircraft', 'capacity', 'price', 'available_seats', 'current_altitude','target_altitude','landing_rate','is_active','completed']
        widgets = {
            'departure_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super(FlightForm, self).__init__(*args, **kwargs)
        self.fields['departure_time'].input_formats = ('%Y-%m-%dT%H:%M',)
