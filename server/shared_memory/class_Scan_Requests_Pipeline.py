#!/usr/bin/python3
# coding: utf-8

import Pyro4
import threading
import datetime
from time import time

try :
    from class_Scan_Request import Scan_Request
    from remove_account_id_from_queue import remove_account_id_from_queue
    from class_Pyro_Semaphore import Pyro_Semaphore
    from class_Pyro_Queue import Pyro_Queue
    from open_proxy import open_proxy
except ModuleNotFoundError :
    from .class_Scan_Request import Scan_Request
    from .remove_account_id_from_queue import remove_account_id_from_queue
    from .class_Pyro_Semaphore import Pyro_Semaphore
    from .class_Pyro_Queue import Pyro_Queue
    from .open_proxy import open_proxy


"""
Classe de gestion des requêtes d'indexation (Nouvelle ou mise à jour) comptes
Twitter dans la base de données.
Instanciée une seule fois lors de l'unique instanciation de la mémoire
partagée, c'est à dire de la classe Shared_Memory.

Les requêtes sont identifiées par l'ID du compte Twitter.

Attention : Ce pipeline de traitement est parallélisé, et non étapes par
étapes !

Note : Pour les objets, on stocke en réalité l'URI qui mène à l'objet sur le
serveur Pyro, et pas l'objet directement (Car Pyro ne peut pas exécuter sur le
serveur les méthodes des sous-objets), et pas le Proxy vers l'objet (Car un
Proxy ne peut être utilisé que par un seul thread à la fois).
Les files d'attente contiennent donc des URI, c'est à dire des chaines de
caractères.
"""
@Pyro4.expose
class Scan_Requests_Pipeline :
    def __init__ ( self, root_shared_memory ) :
        self._root = root_shared_memory
        
        # Comme les objets dans la mémoire partagée sont identifiées par leur
        # URI, et donc uniques, on peut faire le dictionnaire de correspondance
        # suivant :
        # Clé : URL de requête -> Valeur : URI de l'objet Scan_Request.
        self._requests = {}
        
        # Sémaphore d'accès au dictionnaire précédent.
        self._requests_sem = threading.Semaphore()
        
        # File d'attente à l'étape A du traitement : Listage des Tweets avec
        # l'API de recherche.
        # Les objets queue.Queue sont prévus pour faire du multi-threading.
        self._step_A_SearchAPI_list_account_tweets_prior_queue_obj = Pyro_Queue( convert_uri = True )
        self._step_A_SearchAPI_list_account_tweets_prior_queue = self._root.register_obj( self._step_A_SearchAPI_list_account_tweets_prior_queue_obj )
        
        # Version non-prioritaire de la file d'attente précédente.
        self._step_A_SearchAPI_list_account_tweets_queue_obj = Pyro_Queue( convert_uri = True )
        self._step_A_SearchAPI_list_account_tweets_queue = self._root.register_obj( self._step_A_SearchAPI_list_account_tweets_queue_obj )
        
        # File d'attente à l'étape B du traitement : Listage des Tweets avec
        # l'API de timeline.
        self._step_B_TimelineAPI_list_account_tweets_prior_queue_obj = Pyro_Queue( convert_uri = True )
        self._step_B_TimelineAPI_list_account_tweets_prior_queue = self._root.register_obj( self._step_B_TimelineAPI_list_account_tweets_prior_queue_obj )
        
        # Version non-prioritaire de la file d'attente précédente.
        self._step_B_TimelineAPI_list_account_tweets_queue_obj = Pyro_Queue( convert_uri = True )
        self._step_B_TimelineAPI_list_account_tweets_queue = self._root.register_obj( self._step_B_TimelineAPI_list_account_tweets_queue_obj )
        
        # File d'attente à l'étape C du traitement : Indexation des Tweets
        # trouvés par le listage des Tweets avec l'API de recherche.
        self._step_C_SearchAPI_index_account_tweets_prior_queue_obj = Pyro_Queue( convert_uri = True )
        self._step_C_SearchAPI_index_account_tweets_prior_queue = self._root.register_obj( self._step_C_SearchAPI_index_account_tweets_prior_queue_obj )
        
        # Version non-prioritaire de la file d'attente précédente.
        self._step_C_SearchAPI_index_account_tweets_queue_obj = Pyro_Queue( convert_uri = True )
        self._step_C_SearchAPI_index_account_tweets_queue = self._root.register_obj( self._step_C_SearchAPI_index_account_tweets_queue_obj )
        
        # File d'attente à l'étape D du traitement : Indexation des Tweets
        # trouvés par le listage des Tweets avec l'API de timeline.
        self._step_D_TimelineAPI_index_account_tweets_prior_queue_obj = Pyro_Queue( convert_uri = True )
        self._step_D_TimelineAPI_index_account_tweets_prior_queue = self._root.register_obj( self._step_D_TimelineAPI_index_account_tweets_prior_queue_obj )
        
        # Version non-prioritaire de la file d'attente précédente.
        self._step_D_TimelineAPI_index_account_tweets_queue_obj = Pyro_Queue( convert_uri = True )
        self._step_D_TimelineAPI_index_account_tweets_queue = self._root.register_obj( self._step_D_TimelineAPI_index_account_tweets_queue_obj )
        
        # Bloquer toutes les files d'attentes. Permet de passer une requête
        # en prioritaire sans avoir de problème.
        self._queues_sem_obj = Pyro_Semaphore()
        self._queues_sem = self._root.register_obj( self._queues_sem_obj )
        
        # Compteur du nombre de requêtes en cours de traitement dans le
        # pipeline.
        self._processing_requests_count = 0
    
    """
    Getters et setters pour Pyro.
    """
    @property
    def step_A_SearchAPI_list_account_tweets_prior_queue( self ) : return open_proxy( self._step_A_SearchAPI_list_account_tweets_prior_queue )
    
    @property
    def step_A_SearchAPI_list_account_tweets_queue( self ) : return open_proxy( self._step_A_SearchAPI_list_account_tweets_queue )
    
    @property
    def step_B_TimelineAPI_list_account_tweets_prior_queue( self ) : return open_proxy( self._step_B_TimelineAPI_list_account_tweets_prior_queue )
    
    @property
    def step_B_TimelineAPI_list_account_tweets_queue( self ) : return open_proxy( self._step_B_TimelineAPI_list_account_tweets_queue )
    
    @property
    def step_C_SearchAPI_index_account_tweets_prior_queue( self ) : return open_proxy( self._step_C_SearchAPI_index_account_tweets_prior_queue )
    
    @property
    def step_C_SearchAPI_index_account_tweets_queue( self ) : return open_proxy( self._step_C_SearchAPI_index_account_tweets_queue )
    
    @property
    def step_D_TimelineAPI_index_account_tweets_prior_queue( self ) : return open_proxy( self._step_D_TimelineAPI_index_account_tweets_prior_queue )
    
    @property
    def step_D_TimelineAPI_index_account_tweets_queue( self ) : return open_proxy( self._step_D_TimelineAPI_index_account_tweets_queue )
    
    @property
    def queues_sem( self ) : return open_proxy( self._queues_sem )
    
    @property
    def processing_requests_count( self ) : return self._processing_requests_count
    
    # Obtenir le nombre de requêtes en mémoire
    def get_size( self ) :
        # Pas besoin de prendre le sémaphore, le GIL Pyhton fait son job
        return len( self._requests )
    
    """
    Lancer l'indexation ou la mise à jour de l'indexation d'un compte Twitter
    dans la base de données.
    Crée une nouvelle requête si ce compte n'est pas déjà en cours de scan.
    Si le compte était déjà en cours de scan (Ou en file d'attente), il est mis
    en prioritaire si il ne l'était pas déjà et que c'est demandé ici.
    
    Une requête déjà existante peut être terminée ! Ainsi, cela permet de ne
    pas réindexer directement le compte Twitter.
    Les requêtes sont délestées par le thread "remove_finished_requests" 24h
    après la fin de son traitement, permettant de rescanner le compte Twitter.
    
    @param account_id L'ID du compte Twitter. Ne sert qu'à identifier.
    @param account_name Le nom du compte Twitter. Attention, c'est lui qui est
                        revérifié et scanné !
    @param is_prioritary Est ce que cette requête est prioritaire ?
    @param force_launch Forcer relancement de la requête. On ne peut pas forcer
                        certaines étapes indépendemment, cela serait trop
                        dangereux (Aller voir "shed_requests()").
                        ATTENTION : Un relancement implique que la nouvelle
                        requête sera non-prioritaire.
                        LES REQUETES UTILISATEURS STOCKENT LES URI DE LEUR
                        REQUETE DE SCAN ASSOCIEE. Il n'y a donc pas de problème
                        à avoir un doublon.
    
    @return L'objet Scan_Request créé.
            Ou l'objet Scan_Request déjà existant.
            Ou None si aucun ID de compte n'a été passé et qu'il n'existe pas.
    """
    def launch_request ( self, account_id : int,
                               account_name : str,
                               is_prioritary : bool = False,
                               force_launch : bool = False ) -> Scan_Request :
        account_id = int(account_id) # Sécurité, pour unifier
        is_prioritary = is_prioritary and not force_launch
        
        requests_sem = self._requests_sem
        queues_sem = self._queues_sem_obj
        
        requests_sem.acquire()
        queues_sem.acquire()
        
        # Si il faut forcer le relancement, on bloque la boucle "for" suivante.
        # Evite de faire un gros "if".
        if force_launch : requests_dict = {}
        else : requests_dict = self._requests
        
        # Vérifier d'abord qu'on n'est pas déjà en train de traiter ce compte.
        for key in requests_dict :
            if key == account_id :
                request = open_proxy( self._requests[key] )
                
                # Si il faut passer la requête en proritaire.
                if is_prioritary and not request.is_prioritary :
                    request.is_prioritary = True
                    
                    # Si est dans une file d'attente de listage des Tweets avec
                    # l'API de recherche, on la sort, pour la mettre dans la même
                    # file d'attente, mais prioritaire.
                    if not request.started_SearchAPI_listing :
                        # On doit démonter et remonter la file en enlevant la
                        # requête.
                        remove_account_id_from_queue(
                            self._step_A_SearchAPI_list_account_tweets_queue,
                            account_id )
                        
                        # On met la requête dans la file d'attente prioritaire.
                        open_proxy( self._step_A_SearchAPI_list_account_tweets_prior_queue ).put( request )
                    
                    # Si est dans une file d'attente de listage des Tweets avec
                    # l'API de timeline, on la sort, pour la mettre dans la même
                    # file d'attente, mais prioritaire.
                    if not request.started_TimelineAPI_listing :
                        # On doit démonter et remonter la file en enlevant la
                        # requête.
                        remove_account_id_from_queue(
                            self._step_B_TimelineAPI_list_account_tweets_queue,
                            account_id )
                        
                        # On met la requête dans la file d'attente prioritaire.
                        open_proxy( self._step_B_TimelineAPI_list_account_tweets_prior_queue ).put( request )
                    
                    # Si est dans une file d'attente d'indexation des Tweets avec
                    # l'API de recherche, on la sort, pour la mettre dans la même
                    # file d'attente, mais prioritaire.
                    if not request.is_in_SearchAPI_indexing :
                        # On doit démonter et remonter la file en enlevant la
                        # requête.
                        remove_account_id_from_queue(
                            self._step_C_SearchAPI_index_account_tweets_queue,
                            account_id )
                        
                        # On met la requête dans la file d'attente prioritaire.
                        open_proxy( self._step_C_SearchAPI_index_account_tweets_prior_queue ).put( request )
                    
                    # Si est dans une file d'attente d'indexation des Tweets avec
                    # l'API de timeline, on la sort, pour la mettre dans la même
                    # file d'attente, mais prioritaire.
                    if not request.is_in_TimelineAPI_indexing :
                        # On doit démonter et remonter la file en enlevant la
                        # requête.
                        remove_account_id_from_queue(
                            self._step_D_TimelineAPI_index_account_tweets_queue,
                            account_id )
                        
                        # On met la requête dans la file d'attente prioritaire.
                        open_proxy( self.step_D_TimelineAPI_index_account_tweets_prior_queue ).put( request )
                
                queues_sem.release()
                requests_sem.release()
                return request
        
        # Créer et ajouter l'objet Scan_Request à notre système.
        request = self._root.register_obj( Scan_Request( self._root,
                                                         account_id,
                                                         account_name,
                                                         is_prioritary = is_prioritary ) )
        self._processing_requests_count += 1 # Augmenter le compteur du nombre de requêtes en cours de traitement
        self._requests[ account_id ] = request # On passe ici l'URI de l'objet.
        
        request = open_proxy( request )
        
        # Comme le traitement des requêtes de scan est parallélisé, on peut
        # mettre la requêtes dans toutes les files d'attente.
        if is_prioritary :
            self._step_A_SearchAPI_list_account_tweets_prior_queue_obj.put( request )
            self._step_B_TimelineAPI_list_account_tweets_prior_queue_obj.put( request )
            self._step_C_SearchAPI_index_account_tweets_prior_queue_obj.put( request )
            self._step_D_TimelineAPI_index_account_tweets_prior_queue_obj.put( request )
        else :
            self._step_A_SearchAPI_list_account_tweets_queue_obj.put( request )
            self._step_B_TimelineAPI_list_account_tweets_queue_obj.put( request )
            self._step_C_SearchAPI_index_account_tweets_queue_obj.put( request )
            self._step_D_TimelineAPI_index_account_tweets_queue_obj.put( request )
        
        queues_sem.release()
        requests_sem.release()
        
        # Retourner l'objet Scan_Request.
        return request
    
    """
    Obtenir l'objet Scan_Request d'une requête.
    
    @param account_id L'ID du compte Twitter.
    @return Un objet Scan_Request,
            Ou None si la requête est inconnue.
    """
    def get_request ( self, account_id : int ) -> Scan_Request :
        account_id = int(account_id) # Sécurité, pour unifier
        
        self._requests_sem.acquire()
        for key in self._requests :
            if key == account_id :
                self._requests_sem.release()
                return open_proxy( self._requests[key] )
        self._requests_sem.release()
        
        return None
    
    """
    Marquer une requête comme terminée.
    @param Un objet Scan_Request.
    @param get_stats Le résultat de la méthode "get_stats()" de l'objet
                     "SQLite_or_MySQL". Car Pyro est multithreadé, donc on ne
                     peut pas avoir notre propre accès à la BDD !
    """
    def end_request ( self, request : Scan_Request, get_stats = None ) :
        self._requests_sem.acquire()
        
        # Si la requête n'a pas déjà été marquée comme terminée (Car il y a
        # deux threads, C et D, qui peut appeler cette méthode)
        if request.finished_date == None :
            # On indique la date de fin du scan
            request.finished_date = datetime.datetime.now()
            
            # On fais -1 au compteur du nombre de requêtes en cours de traitement
            self._processing_requests_count -= 1
            
            # On peut lacher le sémaphore, tant pis pour les statistiques, car
            # Python nous garantie qu'il n'y aura pas deux écritures en même temps
            self._requests_sem.release()
            
            # On peut Màj les statistiques mises en cache dans l'objet Shared_Memory
            if get_stats != None :
                self._root.tweets_count, self._root.accounts_count = get_stats
            
            # On peut supprimer l'objet Common_Tweet_IDs_List() pour gagner de la
            # mémoire vive
            self._root.unregister_obj( request.indexing_tweets_uri )
            request.indexing_tweets_uri = None
            
            # Idem, on peut supprimer les files d'attente internes
            self._root.unregister_obj( request.SearchAPI_tweets_queue_uri )
            request.SearchAPI_tweets_queue_uri = None
            self._root.unregister_obj( request.TimelineAPI_tweets_queue_uri )
            request.TimelineAPI_tweets_queue_uri = None
            
            # Enregistrer le temps complet pour traiter cette requête
            self._root.execution_metrics.add_scan_request_full_time( time() - request.start )
        
        else :
            self._requests_sem.release()
    
    """
    Délester les anciennes requêtes.
    """
    def shed_requests ( self ) :
        # On prend la date actuelle
        now = datetime.datetime.now()
        
        # On bloque l'accès la liste des requêtes
        self._requests_sem.acquire()
        
        # On filtre la liste des requêtes de scan
        new_requests_dict = {}
        to_unregister_list = []
        
        for key in self._requests :
            request_uri = self._requests[key]
            request = open_proxy( request_uri )
            
            # Si la requête est terminée, il faut vérifier qu'on puisse la garder
            if request.finished_date != None :
                
                # Si la date de fin est à moins de 24h de maintenant, on garde
                # cette requête
                if now - request.finished_date < datetime.timedelta( hours = 24 ) :
                    new_requests_dict[ key ] = request_uri
                
                else : # On désenregistre la requête
                    to_unregister_list.append( request_uri )
            
            # Sinon, son traitement n'est pas fini, on la garde forcément
            else :
                new_requests_dict[ key ] = request_uri
            
            request.release_proxy()
        
        # On installe la nouvelle liste
        self._requests = new_requests_dict
        
        # On débloque l'accès à la liste des requêtes
        self._requests_sem.release()
        
        # On désenregistre les requêtes à désenregistrer
        for uri in to_unregister_list :
            self._root.unregister_obj( uri )
