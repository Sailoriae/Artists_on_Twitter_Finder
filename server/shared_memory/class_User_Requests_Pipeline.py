#!/usr/bin/python3
# coding: utf-8

import Pyro5.server
import threading
from time import time
import json

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendamment (Notamment pour des
# tests), il faut que son répertoire de travail soit ce même répertoire
if __name__ == "__main__" :
    from os.path import abspath as get_abspath
    from os.path import dirname as get_dirname
    from os import chdir as change_wdir
    from os import getcwd as get_wdir
    from sys import path
    change_wdir(get_dirname(get_abspath(__file__)))
    change_wdir( ".." )
    path.append(get_wdir())

from shared_memory.class_User_Request import User_Request
from shared_memory.class_Limit_per_IP_Address import Limit_per_IP_Address
from shared_memory.class_Pyro_Semaphore import Pyro_Semaphore
from shared_memory.class_Pyro_Queue import Pyro_Queue
from shared_memory.open_proxy import open_proxy
import parameters as param
from threads.http_server.generate_json import generate_user_request_json


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
        
        # Même principe que le dictionnaire précédent, mais on sépare les
        # recherches directes / dans toute la BDD.
        self._direct_requests = {}
        
        # Sémaphore d'accès au dictionnaire précédent.
        self._direct_requests_sem = threading.Semaphore()
        
        # File d'attente à l'étape 1 du traitement : Link Finder.
        # Les objets queue.Queue sont prévus pour faire du multi-threading.
        self._step_1_link_finder_queue_obj = Pyro_Queue( convert_uri = True )
        self._step_1_link_finder_queue = self._root.register_obj( self._step_1_link_finder_queue_obj )
        
        # File d'attente à l'étape 2 du traitement : L'indexation des Tweets
        # des comptes Twitter de l'artiste, si nécessaire.
        self._step_2_tweets_indexer_queue_obj = Pyro_Queue( convert_uri = True )
        self._step_2_tweets_indexer_queue = self._root.register_obj( self._step_2_tweets_indexer_queue_obj )
        
        # File d'attente à l'étape 3 du traitement : La recherche d'image
        # inversée.
        self._step_3_reverse_search_queue_obj = Pyro_Queue( convert_uri = True )
        self._step_3_reverse_search_queue = self._root.register_obj( self._step_3_reverse_search_queue_obj )
        
        # Conteneur des adresses IP, associé à leur nombre de requêtes en cours
        # de traitement.
        self._limit_per_ip_addresses_obj = Limit_per_IP_Address()
        self._limit_per_ip_addresses = self._root.register_obj( self._limit_per_ip_addresses_obj )
        
        # Sémaphore du "if request.scan_requests == None" de la procédure de
        # thread "thread_step_2_tweets_indexer". Permet d'éviter des problèmes
        # en cas de lancement d'un scan.
        self._thread_step_2_tweets_indexer_sem_obj = Pyro_Semaphore()
        self._thread_step_2_tweets_indexer_sem = self._root.register_obj( self._thread_step_2_tweets_indexer_sem_obj )
        
        # Compteur du nombre de requêtes en cours de traitement dans le
        # pipeline.
        self._processing_requests_count = 0
    
    """
    Getters et setters pour Pyro.
    """
    @Pyro5.server.expose
    @property
    def step_1_link_finder_queue( self ) : return open_proxy( self._step_1_link_finder_queue )
    
    @Pyro5.server.expose
    @property
    def step_2_tweets_indexer_queue( self ) : return open_proxy( self._step_2_tweets_indexer_queue )
    
    @Pyro5.server.expose
    @property
    def step_3_reverse_search_queue( self ) : return open_proxy( self._step_3_reverse_search_queue )
    
    @Pyro5.server.expose
    @property
    def limit_per_ip_addresses( self ) : return open_proxy( self._limit_per_ip_addresses )
    
    @Pyro5.server.expose
    @property
    def thread_step_2_tweets_indexer_sem( self ) : return open_proxy( self._thread_step_2_tweets_indexer_sem )
    
    @Pyro5.server.expose
    @property
    def processing_requests_count( self ) : return self._processing_requests_count
    
    # Obtenir le nombre de requêtes en mémoire
    @Pyro5.server.expose
    def get_size( self ) :
        # Pas besoin de prendre le sémaphore, le GIL Pyhton fait son job
        return len( self._requests ) + len( self._direct_requests )
    
    """
    Lancer la recherche des Tweets de l'artiste contenant l'illustration dont
    l'URL est passé en paramètre.
    Crée une nouvelle requête si cette illustration n'est pas déjà en cours de
    traitement.
    
    Cette fonction permet aussi d'obtenir une requête si elle est déjà lancée.
    
    Les requêtes sont délestées par le thread "remove_finished_requests" 24h
    après la fin de son traitement.
    
    @param illust_url L'URL de l'illustration.
    @param ip_address L'adresse IP qui a émis cette requête. Elle sera
                      enregistrée avec la requête. (OPTIONNEL)
    
    @return L'objet User_Request créé.
            Ou l'objet User_Request déjà existant.
            Ou None si l'adresse IP passée en paramètre a atteint son nombre
            maximum de requêtes en cours de traitement. La requête n'a donc pas
            été lancée.
    
    Cette fonction permet ainsi d'obtenir une requête si il en existe déjà une
    pour l'entrée "image_url".
    """
    @Pyro5.server.expose
    def launch_request ( self, illust_url : str,
                               ip_address : str = None ) -> User_Request :
        # Vérifier d'abord qu'on n'est pas déjà en train de traiter cette
        # illustration.
        self._requests_sem.acquire()
        for key in self._requests :
            if key == illust_url :
                self._requests_sem.release()
                return open_proxy( self._requests[key] )
        
        # Faire +1 au nombre de requêtes en cours de traitement pour cette
        # adresse IP. Si on ne peut pas, on retourne None.
        # C'est l'objet "Limit_per_IP_Address" qui vérifie que l'IP est dans la
        # liste "UNLIMITED_IP_ADDRESSES".
        if ip_address != None :
            if not self._limit_per_ip_addresses_obj.add_ip_address( ip_address ) :
                self._requests_sem.release()
                return None
        
        # Créer et ajouter l'objet User_Request à notre système.
        request = self._root.register_obj( User_Request( illust_url,
                                                         ip_address = ip_address ) )
        self._requests[ illust_url ] = request # On passe ici l'URI de l'objet.
        self._processing_requests_count += 1 # Augmenter le compteur du nombre de requêtes en cours de traitement
        
        self._requests_sem.release() # Seulement ici !
        
        # Se connecter à l'objet de la requête
        request = open_proxy( request )
        
        # Les requêtes sont initialisée au status -1
        self.set_request_to_next_step( request )
        
        # Retourner l'objet User_Request.
        return request
    
    """
    Lancer une recherche "directe", c'est à dire qu'elle fait seulement l'étape
    de recherche inversée. L'entrée est donc une URL menant à une image.
    Si account_name ou account_id ne sont pas indiqués, la recherche se fera
    dans toute la base de données.
    
    Les requêtes de ce type ont leur attribut "is_direct" à "True".
    
    @param image_url URL de l'image à rechercher. Sert à identifier la requête !
    @param account_name Nom du compte Twitter sur lequel rechercher. Son ID
                        sera recherché par la recherche par image (Etape 3).
    @param binary_image Image binaire. L'URL de l'image ne sert alors plus que
                        d'identifiant pour retrouver la requête.
    @param ip_address L'adresse IP qui a émis cette requête. Elle sera
                      enregistrée avec la requête.
    @param do_not_launch Ne pas lancer une nouvelle requête, et retourner
                         "None" si aucune requête n'a été trouvée.
    
    @return L'objet User_Request créé.
            Ou l'objet User_Request déjà existant.
            Ou None si l'adresse IP passée a atteint son nombre maximum de
            requêtes en cours de traitement (Et que do_not_launch=False).
    
    Cette fonction permet ainsi d'obtenir une requête si il en existe déjà une
    pour l'entrée "image_url" et le compte "account_name".
    """
    @Pyro5.server.expose
    def launch_direct_request ( self, image_url : str,
                                      account_name : str = None,
                                      binary_image : bytes = None,
                                      ip_address : str = None,
                                      do_not_launch : bool = False ) -> User_Request :
        # Vérifier d'abord qu'on n'est pas déjà en train de traiter cette
        # image d'entrée.
        self._direct_requests_sem.acquire()
        for key in self._direct_requests :
            if key == image_url :
                # On vérifie que cette requête directe recherche sur le même
                # compte Twitter que celle qu'on veut créer.
                request = self._root.get_obj( self._direct_requests[key] )
                same_request = True
                for req_account_name, req_account_id in request.twitter_accounts_with_id :
                    if req_account_name != account_name :
                        same_request = False
                if same_request :
                    self._direct_requests_sem.release()
                    return open_proxy( self._direct_requests[key] )
        
        if do_not_launch : return None
        
        # Faire +1 au nombre de requêtes en cours de traitement pour cette
        # adresse IP. Si on ne peut pas, on retourne None.
        if ip_address != None :
            if not self._limit_per_ip_addresses_obj.add_ip_address( ip_address ) :
                self._requests_sem.release()
                return None
        
        # Créer et ajouter l'objet User_Request à notre système.
        request = self._root.register_obj( User_Request( image_url,
                                                         ip_address = ip_address,
                                                         is_direct = True,
                                                         binary_image = binary_image ) )
        self._direct_requests[ image_url ] = request
        self._processing_requests_count += 1 # Augmenter le compteur du nombre de requêtes en cours de traitement
        
        self._direct_requests_sem.release()
        
        # Modifier cet objet pour qu'il soit une requête directe
        request = open_proxy( request )
        if account_name != None :
            request.twitter_accounts_with_id += [ (account_name, None) ]
        request.status = 3
        self.set_request_to_next_step( request )
        
        # Retourner l'objet User_Request.
        return request
    
    """
    Passer la requête à l'étape suivante.
    A utiliser uniquement à la fin et au début d'une itération d'un thread de
    traitement. Et utilise obligatoirement cette méthode pour modifier le
    status d'une requête.
    """
    @Pyro5.server.expose
    def set_request_to_next_step ( self, request : User_Request, force_end : bool = False ) :
        if force_end :
            request.status = 6
        elif request.status < 6 :
            request.status += 1
        
        if request.status == 0 :
            self._step_1_link_finder_queue_obj.put( request )
        
        if request.status == 2 :
            self._step_2_tweets_indexer_queue_obj.put( request )
        
        if request.status == 4 :
            self._step_3_reverse_search_queue_obj.put( request )
        
        if request.status == 6 :
            request.finished_date = time()
            
            # Descendre le compteur de requêtes en cours de traitement dans le
            # pipeline
            # Pas besoin de prendre le sémaphore, le GIL fait son travail
            self._processing_requests_count -= 1
            
            if request.ip_address != None :
                self._limit_per_ip_addresses_obj.remove_ip_address( request.ip_address )
            
            # Journaliser / Logger, uniquement si il n'y a pas eu d'erreur ou
            # de problème lors du traitement
            if param.ENABLE_LOGGING :
                if request.problem == None :
                    response_dict = generate_user_request_json( request )
                    response_dict["input"] = request.input_url
                    response_dict["ip_address"] = request.ip_address
                    file = open( "results.log", "a" )
                    file.write( json.dumps( response_dict ) + "\n" )
                    file.close()
    
    """
    Délester les anciennes requêtes.
    """
    @Pyro5.server.expose
    def shed_requests ( self ) :
        # On doit le faire deux fois, pour nos deux dictionnaires de requêtes
        self._shed_requests( direct_requests = False )
        self._shed_requests( direct_requests = True )
    
    # Méthode privée
    def _shed_requests ( self, direct_requests : bool = False ) :
        # On prend la date actuelle
        now = time()
        
        # On bloque l'accès la liste des requêtes
        if direct_requests : self._direct_requests_sem.acquire()
        else : self._requests_sem.acquire()
        
        # On filtre le dictionnaire des requêtes utilisateurs
        new_requests_dict = {}
        to_unregister_list = []
        
        if direct_requests : requests_list = self._direct_requests
        else : requests_list = self._requests
        for key in requests_list :
            request_uri = requests_list[key]
            request = self._root.get_obj( request_uri )
            
            # Si la requête est terminée, il faut vérifier qu'on puisse la garder
            if request.finished_date != None :
                
                # Si la date de fin est à moins de 3 heures de maintenant, on
                # peut peut-être garder cette requête
                if now - request.finished_date < 3*3600 :
                    # Si la requête s'est terminée en erreur
                    if request.problem != None :
                        # Si l'URL de requête est invalide ou le site n'est pas
                        # supporté (Erreur de l'utilisateur), on garde la
                        # requête 10 minutes
                        if ( request.problem in [ "NOT_AN_URL",
                                                  "NOT_AN_ARTWORK_PAGE",
                                                  "UNSUPPORTED_WEBSITE"] or
                             direct_requests and request.problem in [ "ERROR_DURING_REVERSE_SEARCH" ] ) :
                            if now - request.finished_date < 10*60 :
                                new_requests_dict[ key ] = request_uri
                            
                            else : # On désenregistre la requête
                                to_unregister_list.append( request_uri )
                        
                        # Sinon, on la garde 1 heure
                        else :
                            if now - request.finished_date < 3600 :
                                new_requests_dict[ key ] = request_uri
                            
                            else : # On désenregistre la requête
                                to_unregister_list.append( request_uri )
                    
                    # Si la requête ne s'est pas terminée en erreur, on la
                    # garde 3 heures
                    else :
                        new_requests_dict[ key ] = request_uri
                
                else : # On désenregistre la requête
                    to_unregister_list.append( request_uri )
            
            # Sinon, son traitement n'est pas fini, on la garde forcément
            else :
                new_requests_dict[ key ] = request_uri
        
        # On installe la nouvelle liste
        if direct_requests : self._direct_requests = new_requests_dict
        else : self._requests = new_requests_dict
        
        # On débloque l'accès à la liste des requêtes
        if direct_requests : self._direct_requests_sem.release()
        else : self._requests_sem.release()
        
        # On désenregistre les requêtes à désenregistrer
        for uri in to_unregister_list :
            self._root.unregister_obj( uri )
