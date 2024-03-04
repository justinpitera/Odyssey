from django.apps import AppConfig


class MapConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'map'

    def ready(self):
        from . import scheduler  # Import the module where you defined the scheduler
        scheduler.start_scheduler()  # Start the scheduler