from django.contrib import admin
from .models import Venue, Event, Registration, Feedback ,Profile, NotificationLog

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'location')
    search_fields = ('name', 'location')
    list_filter = ('capacity',)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'event_type', 'department',
        'date_time', 'duration_hours',
        'venue', 'approved', 'registrations_count'
    )
    list_filter = ('event_type', 'approved', 'department', 'venue')
    search_fields = ('name', 'department')
    ordering = ('date_time',)
    filter_horizontal = ('coordinators',)
    readonly_fields = ('created_at',)
    list_select_related = ('venue',)

    def registrations_count(self, obj):
        return obj.registrations.count()

    registrations_count.short_description = "Registrations"

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'timestamp')
    search_fields = ('event__name', 'user__username')
    list_filter = ('timestamp',)
    readonly_fields = ('timestamp',)
    list_select_related = ('event', 'user')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'rating', 'submitted_at')
    search_fields = ('event__name', 'user__username')
    list_filter = ('rating', 'submitted_at')
    readonly_fields = ('submitted_at',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'parent_email')
    search_fields = ('user__username', 'parent_email', 'role')

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('subject', 'to_emails', 'status', 'created_at')
    readonly_fields = ('created_at',)
    search_fields = ('subject', 'to_emails')
    ordering = ('-created_at',)