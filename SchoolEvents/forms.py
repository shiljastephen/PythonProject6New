from django import forms
from .models import Event, Feedback
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    parent_email = forms.EmailField(required=False, help_text="Parent's email (if you are a student)")

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'parent_email', 'password1', 'password2')

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'name', 'event_type', 'department', 'date_time',
            'duration_hours', 'material', 'venue', 'coordinators',
            'target_groups', 'registration_required', 'resources'
        ]
        widgets = {
            'date_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'   # FIXED
            ),
            'resources': forms.Textarea(attrs={'rows': 3}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_time'].input_formats = ['%Y-%m-%dT%H:%M']

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'comments']  # FIXED (removed comma)
