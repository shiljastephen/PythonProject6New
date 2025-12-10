from django.apps import AppConfig

class SchoolEventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'SchoolEvents'

    def ready(self):
        import SchoolEvents.signals

