from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta


EVENT_TYPES = [
    ("workshop", "Workshop"),
    ("seminar", "Seminar"),
    ("cultural_fest", "Cultural Fest"),
    ("sports_event", "Sports Event"),
    ("club_event", "Club Event"),
    ("exam", "Exam-related Event"),
]
ROLES = [
    ('student', 'Student'),
    ('teacher', 'Teacher'),
]

class Venue(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Minimum 1"
    )
    location = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Event(models.Model):
    name = models.CharField(max_length=255)
    event_type = models.CharField(choices=EVENT_TYPES, max_length=50)
    department = models.CharField(max_length=100)
    date_time = models.DateTimeField()
    duration_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[
            MinValueValidator(0.2),
            MaxValueValidator(8)
        ]
    )
    material = models.FileField(upload_to='event_materials/', blank=True, null=True)
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True)
    coordinators = models.ManyToManyField(User, related_name="coordinated_events")
    target_groups = models.CharField(
        max_length=200,
        help_text="Example: Students, Teachers, Parents"
    )
    registration_required = models.BooleanField(default=True)
    resources = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_events"
    )
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('venue', 'date_time')
        ordering = ['date_time']

    def __str__(self):
        return self.name

    @property
    def end_time(self):
        return self.date_time + timedelta(hours=float(self.duration_hours))

class Registration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')

    def __str__(self):
        return f"{self.user.username} → {self.event.name}"

class Feedback(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating between 1 and 5"
    )
    comments = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Feedback by {self.user.username} ({self.rating}/5)"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLES, default='student')
    parent_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

class NotificationLog(models.Model):
    to_emails = models.TextField(help_text="Comma-separated recipient emails")
    subject = models.CharField(max_length=255)
    body = models.TextField()
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='sent')
    error = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} → {self.to_emails}"