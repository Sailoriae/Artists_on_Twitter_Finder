#!/usr/bin/python3
# coding: utf-8

import Pyro4
from datetime import datetime

try :
    from class_User_Request import User_Request
    from class_Limit_per_IP_Address import Limit_per_IP_Address
    from class_Pyro_Semaphore import Pyro_Semaphore
    from class_Pyro_Queue import Pyro_Queue
    from class_Threads_Register import Threads_Register
except ModuleNotFoundError :
    from .class_User_Request import User_Request
    from .class_Limit_per_IP_Address import Limit_per_IP_Address
    from .class_Pyro_Semaphore import Pyro_Semaphore
    from .class_Pyro_Queue import Pyro_Queue
    from .class_Threads_Register import Threads_Register


"""
Classe de gestion des requêtes utilisateurs dans notre système.
Instanciée une seule fois lors de l'unique instanciation de la mémoire
partagée, c'est à dire de la classe Shared_Memory.

Les requêtes sont identifiées par l'URL de l'illustration de requête.

Note : Pour les objets, on stocke en réalité l'URI qui mène à l'objet sur le
serveur Pyro, et pas l'objet directement (Car Pyro ne peut pas exécuter sur le
serveur les méthodes des sous-objets), et pas le Proxy vers l'objet (Car un
Proxy ne peut être utilisé que par un seul thread à la fois).
Les files d'attente contiennent donc des URI, c'est à dire des chaines de
caractères.
"""
@Pyro4.expose
class User_Requests_Pipeline :
    def __init__ ( self, root_shared_memory ) :
        self._root = root_shared_memory
        
        # Comme les objets dans la mémoire partagée sont identifiées par leur
        # URI, et donc uniques, on peut faire une liste principale qui contient
        # toutes les requêtes. C'est donc une liste de chaines !
        self._requests = []
        
        # Sémaphore d'accès à la liste précédente.
        self._requests_sem = self._root.register_obj( Pyro_Semaphore(), "user_requests_requests_sem" )
        
        # File d'attente à l'étape 1 du traitement : Link Finder.
        # Les objets queue.Queue sont prévus pour faire du multi-threading.
        self._step_1_link_finder_queue = self._root.register_obj( Pyro_Queue( convert_uri = True ), "user_requests_step_1_link_finder_queue" )
        
        # File d'attente à l'étape 2 du traitement : L'indexation des Tweets
        # des comptes Twitter de l'artiste, si nécessaire.
        self._step_2_tweets_indexer_queue = self._root.register_obj( Pyro_Queue( convert_uri = True ), "user_requests_step_2_tweets_indexer_queue" )
        
        # File d'attente à l'étape 3 du traitement : La recherche d'image
        # inversée.
        self._step_3_reverse_search_queue = self._root.register_obj( Pyro_Queue( convert_uri = True ), "user_requests_step_3_reverse_search_queue" )
        
        # Conteneur des adresses IP, associé à leur nombre de requêtes en cours
        # de traitement.
        self._limit_per_ip_addresses = self._root.register_obj( Limit_per_IP_Address(), "user_requests_limit_per_ip_addresses" )
        
        # Dictionnaire où les threads mettent leur requête en cours de
        # traitement, afin que leurs collecteurs d'erreurs mettent ces
        # requêtes en échec lors d'un plantage.
        # Les threads sont identifiés par la chaine suivante :
        # procédure_du_thread.__name__ + "_number" + str(thread_id)
        self._requests_in_thread = self._root.register_obj( Threads_Register(), "user_requests_requests_in_thread" )
        
        # Sémaphore du "if request.scan_requests == None" de la procédure de
        # thread "thread_step_2_tweets_indexer". Permet d'éviter des problèmes
        # en cas de lancement d'un scan.
        self._thread_step_2_tweets_indexer_sem = self._root.register_obj( Pyro_Semaphore(), "user_requests_thread_step_2_tweets_indexer_sem" )
    
    """
    Getters et setters pour Pyro.
    """
    @property
    def requests_sem( self ) : return Pyro4.Proxy( self._requests_sem )
    
    @property
    def step_1_link_finder_queue( self ) : return Pyro4.Proxy( self._step_1_link_finder_queue )
    
    @property
    def step_2_tweets_indexer_queue( self ) : return Pyro4.Proxy( self._step_2_tweets_indexer_queue )
    
    @property
    def step_3_reverse_search_queue( self ) : return Pyro4.Proxy( self._step_3_reverse_search_queue )
    
    @property
    def limit_per_ip_addresses( self ) : return Pyro4.Proxy( self._limit_per_ip_addresses )
    
    @property
    def requests_in_thread( self ) : return Pyro4.Proxy( self._requests_in_thread )
    
    @property
    def thread_step_2_tweets_indexer_sem( self ) : return Pyro4.Proxy( self._thread_step_2_tweets_indexer_sem )
    
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
        requests_sem = Pyro4.Proxy( self._requests_sem )
        requests_sem.acquire()
        for request_uri in self._requests :
            request = Pyro4.Proxy( request_uri )
            if request.input_url == illust_url :
                requests_sem.release()
                return request
        
        # Faire +1 au nombre de requêtes en cours de traitement pour cette
        # adresse IP. Si on ne peut pas, on retourne None.
        if not Pyro4.Proxy( self._limit_per_ip_addresses ).add_ip_address( ip_address ) :
            requests_sem.release()
            return None
        
        # Créer et ajouter l'objet User_Request à notre système.
        request = self._root.register_obj( User_Request( illust_url,
                                                         ip_address = ip_address ), None )
        self._requests.append( request ) # Passé par adresse car c'est un objet.
        requests_sem.release() # Seulement ici !
        
        # Les requêtes sont initialisée au status -1
        self.set_request_to_next_step( Pyro4.Proxy( request ) )
        
        # Retourner l'objet User_Request.
        return Pyro4.Proxy( request )
    
    """
    Obtenir l'objet User_Request d'une requête.
    
    @param illust_url L'illustration d'entrée.
    @return Un objet User_Request,
            Ou None si la requête est inconnue.
    """
    def get_request ( self, illust_url : str ) -> User_Request :
        requests_sem = Pyro4.Proxy( self._requests_sem )
        requests_sem.acquire()
        for request_uri in self._requests :
            request = Pyro4.Proxy( request_uri )
            if request.input_url == illust_url :
                requests_sem.release()
                return request
        requests_sem.release()
        
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
            Pyro4.Proxy( self._step_1_link_finder_queue ).put( request )
        
        if request.status == 2 :
            Pyro4.Proxy( self._step_2_tweets_indexer_queue ).put( request )
        
        if request.status == 4 :
            Pyro4.Proxy( self._step_3_reverse_search_queue ).put( request )
        
        if request.status == 6 :
            request.finished_date = datetime.now()
            if request.ip_address != None :
                Pyro4.Proxy( self._limit_per_ip_addresses ).remove_ip_address( request.ip_address )
