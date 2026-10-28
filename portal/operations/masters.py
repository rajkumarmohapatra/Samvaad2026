"""Explicit allowlist of non-personal configuration masters."""
from django import forms
from django.core.exceptions import ValidationError
from .models import Event, Edition, Unit, EditionUnit, ParticipantCategory, TribeReference

MASTERS = {
    'tribes': (TribeReference, 'Tribes', ['national_code','unique_code','name','sub_tribe','sub_code','state','active']),
    'categories': (ParticipantCategory, 'Participant categories', ['name','active']),
    'units': (Unit, 'Streams, teams & programs', ['name','kind','active']),
    'events': (Event, 'Events', ['name','active']),
    'editions': (Edition, 'Event editions', ['event','year','title','starts','ends','closed','helpdesk_contact']),
    'edition-units': (EditionUnit, 'Edition stream & team assignments', ['edition','unit','display_name','active']),
}

class MasterForm(forms.ModelForm):
    def clean(self):
        data = super().clean()
        for key, value in list(data.items()):
            if isinstance(value, str):
                data[key] = value.strip()
                if self.fields[key].required and not data[key]:
                    self.add_error(key, 'Enter a value; spaces alone are not allowed.')
        if self._meta.model is TribeReference:
            code = data.get('unique_code')
            if code and TribeReference.objects.filter(unique_code=code).exclude(pk=self.instance.pk).exists():
                self.add_error('unique_code', 'This reference code already exists. Edit the existing record.')
            if data.get('name', '').casefold() == 'omitted' and data.get('active'):
                self.add_error('active', 'Omitted source entries must remain inactive.')
        return data
