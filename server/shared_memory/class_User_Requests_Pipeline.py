#!/usr/bin/python3
# coding: utf-8

import Pyro4
import threading
import datetime
import json

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

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param
from app.user_pipeline import generate_user_request_json


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
        # URI, et donc uniques, on peut faire le dictionnaire de correspondance
        # suivant :
        # Clé : URL de requête -> Valeur : URI de l'objet User_Request.
        self._requests = {}
        
        # Sémaphore d'accès au dictionnaire précédent.
        self._requests_sem = threading.Semaphore()
        
        # File d'attente à l'étape 1 du traitement : Link Finder.
        # Les objets queue.Queue sont prévus pour faire du multi-threading.
        self._step_1_link_finder_queue = self._root.register_obj( Pyro_Queue( convert_uri = True ), "user_requests_step_1_link_finder_queue" )
        
        # File d'attente à l'étape 2 du traitement : L'indexation des Tweets
        # des comptes Twitter de l'artiste, si nécessaire.
        self._step_2_tweets_indexer_queue = self._root.register_obj( Pyro_Queue( convert_uri = True ), "user_requests_step_2_tweets_indexer_queue" )
        
        # File d'attente à l'étape 3 du traitement : La recherche d'image
        # inversée.
        self._step_3_reverse_search_queue = self._root.register_obj( Pyro_Queue( convert_uri = True ), "user_requests_step_3_reverse_search_queue" )
        
        # File d'attente à l'étape 3 du traitement : Le filtrage des résultats.
        self._step_4_filter_results_queue = self._root.register_obj( Pyro_Queue( convert_uri = True ), "user_requests_step_4_filter_results_queue" )
        
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
        
        # Compteur du nombre de requêtes en cours de traitement dans le
        # pipeline.
        self._pending_requests_count = 0
    
    """
    Getters et setters pour Pyro.
    """
    @property
    def step_1_link_finder_queue( self ) : return Pyro4.Proxy( self._step_1_link_finder_queue )
    
    @property
    def step_2_tweets_indexer_queue( self ) : return Pyro4.Proxy( self._step_2_tweets_indexer_queue )
    
    @property
    def step_3_reverse_search_queue( self ) : return Pyro4.Proxy( self._step_3_reverse_search_queue )
    
    @property
    def step_4_filter_results_queue( self ) : return Pyro4.Proxy( self._step_4_filter_results_queue )
    
    @property
    def limit_per_ip_addresses( self ) : return Pyro4.Proxy( self._limit_per_ip_addresses )
    
    @property
    def requests_in_thread( self ) : return Pyro4.Proxy( self._requests_in_thread )
    
    @property
    def thread_step_2_tweets_indexer_sem( self ) : return Pyro4.Proxy( self._thread_step_2_tweets_indexer_sem )
    
    @property
    def pending_requests_count( self ) : return self._pending_requests_count
    
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
        self._requests_sem.acquire()
        for key in self._requests :
            if key == illust_url :
                self._requests_sem.release()
                return Pyro4.Proxy( self._requests[key] )
        
        # Faire +1 au nombre de requêtes en cours de traitement pour cette
        # adresse IP. Si on ne peut pas, on retourne None.
        # C'est l'objet "Limit_per_IP_Address" qui vérifie que l'IP est dans la
        # liste "UNLIMITED_IP_ADDRESSES".
        if ip_address != None :
            if not Pyro4.Proxy( self._limit_per_ip_addresses ).add_ip_address( ip_address ) :
                self._requests_sem.release()
                return None
        
        # Créer et ajouter l'objet User_Request à notre système.
        request = self._root.register_obj( User_Request( illust_url,
                                                         ip_address = ip_address ), None )
        self._requests[ illust_url ] = request # On passe ici l'URI de l'objet.
        self._pending_requests_count += 1 # Augmenter le compteur du nombre de requêtes en cours de traitement
        
        self._requests_sem.release() # Seulement ici !
        
        # Les requêtes sont initialisée au status -1
        self.set_request_to_next_step( Pyro4.Proxy( request ) )
        
        # Retourner l'objet User_Request.
        return Pyro4.Proxy( request )
    
    """
    Lancer une recherche inversée d'image.
    Si account_name ou account_id ne sont pas indiqués, la recherche se fera
    dans toute la base de données.
    
    @param image_url URL de l'image à rechercher. Sert à identifier la requête !
    @param account_name Nom du compte Twitter sur lequel rechercher.
    @param account_id ID du compte Twitter sur lequel rechercher.
    """
    def launch_reverse_search_only ( self, image_url : str,
                                           account_name : str = None,
                                           account_id : int = None ) -> User_Request :
        self._requests_sem.acquire()
        
        # Créer et ajouter l'objet User_Request à notre système.
        request = self._root.register_obj( User_Request( image_url ), None )
        self._requests[ image_url ] = request
        self._pending_requests_count += 1 # Augmenter le compteur du nombre de requêtes en cours de traitement
        
        self._requests_sem.release()
        
        # Modifier cet objet si nécessaire
        request = Pyro4.Proxy( request )
        request.image_url = image_url
        if account_name != None and account_id != None :
            request.twitter_accounts_with_id += [ (account_name,account_id) ]
        
        request.status = 3
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
        self._requests_sem.acquire()
        for key in self._requests :
            if key == illust_url :
                self._requests_sem.release()
                return Pyro4.Proxy( self._requests[key] )
        self._requests_sem.release()
        
        return None
    
    """
    Passer la requête à l'étape suivante.
    A utiliser uniquement à la fin et au début d'une itération d'un thread de
    traitement. Et utilise obligatoirement cette méthode pour modifier le
    status d'une requête.
    """
    def set_request_to_next_step ( self, request : User_Request, force_end : bool = False ) :
        if force_end :
            request.status = 8
        elif request.status < 8 :
            request.status += 1
        
        if request.status == 0 :
            Pyro4.Proxy( self._step_1_link_finder_queue ).put( request )
        
        if request.status == 2 :
            Pyro4.Proxy( self._step_2_tweets_indexer_queue ).put( request )
        
        if request.status == 4 :
            Pyro4.Proxy( self._step_3_reverse_search_queue ).put( request )
        
        if request.status == 6 :
            Pyro4.Proxy( self._step_4_filter_results_queue ).put( request )
        
        if request.status == 8 :
            request.finished_date = datetime.datetime.now()
            
            # Supprimer l'image mise en cache afin de gagner de la mémoire
            request.query_image_as_bytes = None
            
            # Descendre le compteur de requêtes en cours de traitement dans le
            # pipeline
            self._requests_sem.acquire()
            self._pending_requests_count -= 1
            self._requests_sem.release()
            
            if request.ip_address != None :
                Pyro4.Proxy( self._limit_per_ip_addresses ).remove_ip_address( request.ip_address )
            
            # Journaliser / Logger, uniquement si il n'y a pas eu d'erreur ou
            # de problème lors du traitement
            if param.ENABLE_LOGGING :
                if request.problem == None :
                    response_dict = generate_user_request_json( request )
                    response_dict["input"] = request.input_url
                    response_dict["ip_address"] = request.ip_address
                    file = open( "results.log", "a" )
                    file.write( json.dumps( response_dict ) + " " + "\n" )
                    file.close()
    
    """
    Délester les anciennes requêtes.
    """
    def shed_requests ( self ) :
        # On prend la date actuelle
        now = datetime.datetime.now()
        
        # On bloque l'accès la liste des requêtes
        self._requests_sem.acquire()
        
        # On filtre le dictionnaire des requêtes utilisateurs
        new_requests_dict = {}
        to_unregister_list = []
        
        for key in self._requests :
            request_uri = self._requests[key]
            request = Pyro4.Proxy( request_uri )
            
            # Si la requête est terminée, il faut vérifier qu'on puisse la garder
            if request.finished_date != None :
                
                # Si la date de fin est à moins de 3 heures de maintenant, on
                # peut peut-être garder cette requête
                if now - request.finished_date < datetime.timedelta( hours = 3 ) :
                    # Si la requête s'est terminée en erreur
                    if request.problem != None :
                        # Si l'URL de requête est invalide ou le site n'est pas
                        # supporté, on garde la requête 10 minutes
                        if request.problem in [ "NOT_AN_URL",
                                                "INVALID_URL",
                                                "UNSUPPORTED_WEBSITE"] :
                            if now - request.finished_date < datetime.timedelta( minutes = 10 ) :
                                new_requests_dict[ key ] = request_uri
                            
                            else : # On désenregistre la requête
                                to_unregister_list.append( request_uri )
                        
                        # Sinon, on la garde 1 heure
                        else :
                            if now - request.finished_date < datetime.timedelta( hours = 1 ) :
                                new_requests_dict[ key ] = request_uri
                            
                            else : # On désenregistre la requête
                                to_unregister_list.append( request_uri )
                    
                    # Si la requête ne s'est pas terminée en erreur, on la
                    # garde 3 heures
                    else :
                        new_requests_dict[ key ] = request_uri
                
                else : # On désenregistre la requête
                    to_unregister_list.append( request_uri )
            
            # Sinon, on la garde forcément
            else :
                new_requests_dict[ key ] = request_uri
        
        # On installe la nouvelle liste
        self._requests = new_requests_dict
        
        # On désenregistre les requêtes à désenregistrer
        # Mais normalement le garbadge collector l'a fait avant nous
        # Oui : Pyro4 désenregistre les objets que le garbadge collector a viré
        for uri in to_unregister_list :
            self._root.unregister_obj( uri )
        
        # On débloque l'accès à la liste des requêtes
        self._requests_sem.release()
