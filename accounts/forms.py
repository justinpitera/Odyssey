from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

CONTINENT_CHOICES = [
    ('AF', 'Africa'),
    ('AS', 'Asia'),
    ('EU', 'Europe'),
    ('NA', 'North America'),
    ('OC', 'Oceania'),
    ('SA', 'South America'),
]

class UserCreationForm(UserCreationForm):
    region = forms.ChoiceField(choices=CONTINENT_CHOICES)
    rank = forms.CharField(widget=forms.HiddenInput(), initial='Cadet')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email', 'region', 'rank')
