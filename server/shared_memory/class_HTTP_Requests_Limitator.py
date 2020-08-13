#!/usr/bin/python3
# coding: utf-8

import Pyro4
from time import time
from threading import Semaphore


"""
Objet permettant de limiter les requêtes HTTP sur le serveur HTTP / l'API à une
seule requête par seconde. Sinon, l'API renvoit une erreur HTTP 429.
"""
@Pyro4.expose
class HTTP_Requests_Limitator :
    def __init__ ( self ) :
        # Dictionnaire faisant correspondre un adresse IP à la date de la
        # dernière requête
        self._time_per_ip_address = {}
        
        # Sémaphore d'accès au dictionnaire précédent
        self._sem = Semaphore()
    
    """
    @param ip_address L'adresse IP du client.
    @return True si le client n'a pas envoyé de requête depuis une seconde, on
            peut donc lui répondre.
            False si il faut lui envoyer une erreur HTTP 429.
    """
    def can_request ( self, ip_address ) :
        self._sem.acquire()
        now = time()
        try :
            if now - self._time_per_ip_address[ ip_address ] > 1 :
                to_return = True
            else :
                to_return = False
        except KeyError :
            to_return = True
        if to_return : # Ne pas enregistrer la date lors d'une 429, sinon on bloque trop l'utilisateur
            self._time_per_ip_address[ ip_address ] = now
        self._sem.release()
        return to_return
    
    """
    Vider le dictionnaire de cet objet.
    """
    def reset ( self ) :
        self._sem.acquire()
        self._time_per_ip_address = {}
        self._sem.release()
