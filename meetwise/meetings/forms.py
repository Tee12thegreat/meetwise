from django import forms
from django.contrib.auth.models import User
from .models import Meeting, MeetingMinutes


class MeetingForm(forms.ModelForm):
    attendees = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    scheduled_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    class Meta:
        model = Meeting
        fields = ['title', 'description', 'scheduled_at', 'duration_minutes', 'agenda', 'attendees']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Meeting title'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Brief description...'}),
            'agenda': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Agenda items (one per line)'}),
            'duration_minutes': forms.NumberInput(attrs={'min': 15, 'max': 480, 'step': 15}),
        }


class MinutesForm(forms.ModelForm):
    class Meta:
        model = MeetingMinutes
        fields = ['content', 'action_items', 'decisions']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 8, 'placeholder': 'Meeting notes and discussion summary...'}),
            'action_items': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Action items (one per line)\ne.g. John - Review proposal by Friday'}),
            'decisions': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Key decisions made during this meeting...'}),
        }
