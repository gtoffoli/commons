# 261007-GT: added with Gemini - see "\Users\giovanni\OneDrive\Server\contabo02\AI - filtro di Logging con Rate Limiting.txt"

import logging
from django.db import OperationalError
from django.core.cache import cache

class ConnectionSlotShortageFilter(logging.Filter):
    def filter(self, record):
        # Verifica se l'errore è legato a PostgreSQL e alla connessione al DB
        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            exc_name = exc_type.__name__

            if issubclass(exc_type, OperationalError):
                err_msg = str(exc_value).lower()
                # Cattura il messaggio specifico che stai riscontrando
                if "remaining connection slots" in err_msg:
                    # Chiave di cache unica per questo tipo di errore
                    cache_key = "connection slots"
                    # Se la chiave esiste, blocca l'invio dell'email
                    if cache.get(cache_key):
                        return False
                    # Imposta un blocco di 5 minuti (300 secondi) prima della prossima email
                    cache.set(cache_key, True, timeout=300)
