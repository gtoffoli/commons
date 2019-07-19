
from django.apps import AppConfig

class CommonsConfig(AppConfig):
    name = 'commons'

    def ready(self):
        import commons.signal_handlers
        # print ('imported signal_handlers')
