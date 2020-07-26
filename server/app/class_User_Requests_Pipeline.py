#!/usr/bin/python3
# coding: utf-8

import queue
import threading
from datetime import datetime

try :
    from class_User_Request import User_Request
    from class_Limit_per_IP_Address import Limit_per_IP_Address
except ModuleNotFoundError :
    from .class_User_Request import User_Request
    from .class_Limit_per_IP_Address import Limit_per_IP_Address


"""
Classe de gestion des requêtes utilisateurs dans notre système.
Instanciée une seule fois lors de l'unique instanciation de la mémoire
partagée, c'est à dire de la classe Shared_Memory.

Les requêtes sont identifiées par l'URL de l'illustration de requête.
"""
class User_Requests_Pipeline :
    def __init__ ( self ) :
        # Comme les objets sont passés par adresse en Python, on peut faire une
        # liste principale qui contient toutes les requêtes.
        self.requests = []
        
        # Sémaphore d'accès à la liste précédente.
        self.requests_sem = threading.Semaphore()
        
        # File d'attente à l'étape 1 du traitement : Link Finder.
        # Les objets queue.Queue sont prévus pour faire du multi-threading.
        self.step_1_link_finder_queue = queue.Queue()
        
        # File d'attente à l'étape 2 du traitement : L'indexation des Tweets
        # des comptes Twitter de l'artiste, si nécessaire.
        self.step_2_tweets_indexer_queue = queue.Queue()
        
        # File d'attente à l'étape 3 du traitement : La recherche d'image
        # inversée.
        self.step_3_reverse_search_queue = queue.Queue()
        
        # Conteneur des adresses IP, associé à leur nombre de requêtes en cours
        # de traitement.
        self.limit_per_ip_addresses = Limit_per_IP_Address()
        
        # Dictionnaire où les threads mettent leur requête en cours de
        # traitement, afin que leurs collecteurs d'erreurs mettent ces
        # requêtes en échec lors d'un plantage.
        # Les threads sont identifiés par la chaine suivante :
        # procédure_du_thread.__name__ + "_number" + str(thread_id)
        self.requests_in_thread = {}
    
    """
    Lancer la recherche des Tweets de l'artiste contenant l'illustration dont
    l'URL est passé en paramètre.
    Crée une nouvelle requête si cette illustration n'est pas déjà en cours de
    traitement.
    
    Les requêtes sont délestées par le thread "remove_finished_requests" 24h
    après la fin de son traitement.
    
    @param illust_url L'URL de l'illustration.
    @param ip_address L'adresse IP qui a émis cette requête. Elle sera
                      enregistrée avec la requête. (OPTIONNEL)
    
    @return L'objet User_Request créé.
            Ou l'objet User_Request déjà existant.
            Ou None si l'addresse IP passée en paramètre a atteint son nombre
            maximum de requêtes en cours de traitement. La requête n'a donc pas
            été lancée.
    """
    def launch_request ( self, illust_url : str,
                               ip_address : str = None ) -> User_Request :
        # Vérifier d'abord qu'on n'est pas déjà en train de traiter cette
        # illustration.
        self.requests_sem.acquire()
        for request in self.requests :
            if request.input_url == illust_url :
                self.requests_sem.release()
                return request
        
        # Faire +1 au nombre de requêtes en cours de traitement pour cette
        # adresse IP. Si on ne peut pas, on retourne None.
        if not self.limit_per_ip_addresses.add_ip_address( ip_address ) :
            self.requests_sem.release()
            return None
        
        # Créer et ajouter l'objet User_Request à notre système.
        request = User_Request( illust_url,
                                ip_address = ip_address )
        self.requests.append( request ) # Passé par adresse car c'est un objet.
        self.requests_sem.release() # Seulement ici !
        
        # Les requêtes sont initialisée au status -1
        self.set_request_to_next_step( request )
        
        # Retourner l'objet User_Request.
        return request
    
    """
    Obtenir l'objet User_Request d'une requête.
    
    @param illust_url L'illustration d'entrée.
    @return Un objet User_Request,
            Ou None si la requête est inconnue.
    """
    def get_request ( self, illust_url : str ) -> User_Request :
        self.requests_sem.acquire()
        for request in self.requests :
            if request.input_url == illust_url :
                self.requests_sem.release()
                return request
        self.requests_sem.release()
        
        return None
    
    """
    Passer la requête à l'étape suivante.
    A utiliser uniquement à la fin et au début d'une itération d'un thread de
    traitement. Et utilise obligatoirement cette méthode pour modifier le
    status d'une requête.
    """
    def set_request_to_next_step ( self, request : User_Request, force_end : bool = False ) :
        if force_end :
            request.status = 6
        elif request.status < 6 :
            request.status += 1
        
        if request.status == 0 :
            self.step_1_link_finder_queue.put( request )
        
        if request.status == 2 :
            self.step_2_tweets_indexer_queue.put( request )
        
        if request.status == 4 :
            self.step_3_reverse_search_queue.put( request )
        
        if request.status == 6 :
            request.finished_date = datetime.now()
            if request.ip_address != None :
                self.limit_per_ip_addresses.remove_ip_address( request.ip_address )
