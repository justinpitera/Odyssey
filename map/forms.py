from django import forms
from .models import Airport, Controller

class ControllerForm(forms.ModelForm):
    airport_ident = forms.CharField(required=False, label='Airport Ident Code')

    class Meta:
        model = Controller
        fields = ['ident', 'latitude_deg', 'longitude_deg', 'frequency', 'type', 'division', 'vatsim_id', 'airport_ident', 'name']
        exclude = ['airport'] 

    def clean_airport_ident(self):
        ident = self.cleaned_data.get('airport_ident')
        if ident:
            try:
                airport = Airport.objects.get(ident=ident)
                return airport
            except Airport.DoesNotExist:
                raise forms.ValidationError(f"No airport found with ident code '{ident}'")
        return None

    def save(self, commit=True):
        instance = super(ControllerForm, self).save(commit=False)
        instance.airport = self.cleaned_data.get('airport_ident') 
        if commit:
            instance.save()
        return instance