from django.apps import AppConfig

class MainAppConfig(AppConfig):
    name = 'main'

    def ready(self):
        import fg.apps.main.models.signals
