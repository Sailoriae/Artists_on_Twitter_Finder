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
    from class_Threads_Register import Threads_Register
except ModuleNotFoundError :
    from .class_Scan_Request import Scan_Request
    from .remove_account_id_from_queue import remove_account_id_from_queue
    from .class_Pyro_Semaphore import Pyro_Semaphore
    from .class_Pyro_Queue import Pyro_Queue
    from .class_Threads_Register import Threads_Register


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
        # GetOldTweets3.
        # Les objets queue.Queue sont prévus pour faire du multi-threading.
        self._step_A_GOT3_list_account_tweets_prior_queue = self._root.register_obj( Pyro_Queue( convert_uri = True ), "scan_requests_step_A_GOT3_list_account_tweets_prior_queue" )
        
        # Version non-prioritaire de la file d'attente précédente.
        self._step_A_GOT3_list_account_tweets_queue = self._root.register_obj( Pyro_Queue( convert_uri = True ), "scan_requests_step_A_GOT3_list_account_tweets_queue" )
        
        # File d'attente à l'étape B du traitement : Listage des Tweets avec
        # l'API publique Twitter.
        self._step_B_TwitterAPI_list_account_tweets_prior_queue = self._root.register_obj( Pyro_Queue( convert_uri = True ), "scan_requests_step_B_TwitterAPI_list_account_tweets_prior_queue" )
        
        # Version non-prioritaire de la file d'attente précédente.
        self._step_B_TwitterAPI_list_account_tweets_queue = self._root.register_obj( Pyro_Queue( convert_uri = True ), "scan_requests_step_B_TwitterAPI_list_account_tweets_queue" )
        
        # File d'attente à l'étape C du traitement : Indexation des Tweets
        # trouvés par le listage des Tweets avec GetOldTweets3.
        self._step_C_GOT3_index_account_tweets_prior_queue = self._root.register_obj( Pyro_Queue( convert_uri = True ), "scan_requests_step_C_GOT3_index_account_tweets_prior_queue" )
        
        # Version non-prioritaire de la file d'attente précédente.
        self._step_C_GOT3_index_account_tweets_queue = self._root.register_obj( Pyro_Queue( convert_uri = True ), "scan_requests_step_C_GOT3_index_account_tweets_queue" )
        
        # File d'attente à l'étape D du traitement : Indexation des Tweets
        # trouvés par le listage des Tweets avec l'API publique Twitter.
        self._step_D_TwitterAPI_index_account_tweets_prior_queue = self._root.register_obj( Pyro_Queue( convert_uri = True ), "scan_requests_step_D_TwitterAPI_index_account_tweets_prior_queue" )
        
        # Version non-prioritaire de la file d'attente précédente.
        self._step_D_TwitterAPI_index_account_tweets_queue = self._root.register_obj( Pyro_Queue( convert_uri = True ), "scan_requests_step_D_TwitterAPI_index_account_tweets_queue" )
        
        # Bloquer toutes les files d'attentes. Permet de passer une requête
        # en prioritaire sans avoir de problème.
        self._queues_sem = self._root.register_obj( Pyro_Semaphore(), "scan_requests_queues_sem" )
        
        # Dictionnaire où les threads mettent leur requête en cours de
        # traitement, afin que leurs collecteurs d'erreurs mettent ces
        # requêtes en échec lors d'un plantage.
        # Les threads sont identifiés par la chaine suivante :
        # procédure_du_thread.__name__ + "_number" + str(thread_id)
        self._requests_in_thread = self._root.register_obj( Threads_Register(), "scan_requests_requests_in_thread" )
        
        # Compteur du nombre de requêtes en cours de traitement dans le
        # pipeline.
        self._pending_requests_count = 0
    
    """
    Getters et setters pour Pyro.
    """
    @property
    def step_A_GOT3_list_account_tweets_prior_queue( self ) : return Pyro4.Proxy( self._step_A_GOT3_list_account_tweets_prior_queue )
    
    @property
    def step_A_GOT3_list_account_tweets_queue( self ) : return Pyro4.Proxy( self._step_A_GOT3_list_account_tweets_queue )
    
    @property
    def step_B_TwitterAPI_list_account_tweets_prior_queue( self ) : return Pyro4.Proxy( self._step_B_TwitterAPI_list_account_tweets_prior_queue )
    
    @property
    def step_B_TwitterAPI_list_account_tweets_queue( self ) : return Pyro4.Proxy( self._step_B_TwitterAPI_list_account_tweets_queue )
    
    @property
    def step_C_GOT3_index_account_tweets_prior_queue( self ) : return Pyro4.Proxy( self._step_C_GOT3_index_account_tweets_prior_queue )
    
    @property
    def step_C_GOT3_index_account_tweets_queue( self ) : return Pyro4.Proxy( self._step_C_GOT3_index_account_tweets_queue )
    
    @property
    def step_D_TwitterAPI_index_account_tweets_prior_queue( self ) : return Pyro4.Proxy( self._step_D_TwitterAPI_index_account_tweets_prior_queue )
    
    @property
    def step_D_TwitterAPI_index_account_tweets_queue( self ) : return Pyro4.Proxy( self._step_D_TwitterAPI_index_account_tweets_queue )
    
    @property
    def queues_sem( self ) : return Pyro4.Proxy( self._queues_sem )
    
    @property
    def requests_in_thread( self ) : return Pyro4.Proxy( self._requests_in_thread )
    
    @property
    def pending_requests_count( self ) : return self._pending_requests_count
    
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
    
    @return L'objet Scan_Request créé.
            Ou l'objet Scan_Request déjà existant.
            Ou None si aucun ID de compte n'a été passé et qu'il n'existe pas.
    """
    def launch_request ( self, account_id : int,
                               account_name : str,
                               is_prioritary : bool = False ) -> Scan_Request :
        requests_sem = self._requests_sem
        queues_sem = Pyro4.Proxy( self._queues_sem )
        
        requests_sem.acquire()
        queues_sem.acquire()
        
        # Vérifier d'abord qu'on n'est pas déjà en train de traiter ce compte.
        for key in self._requests :
            if key == account_id :
                request = Pyro4.Proxy( self._requests[key] )
                
                # Si il faut passer la requête en proritaire.
                if is_prioritary and not request.is_prioritary :
                    request.is_prioritary = True
                    
                    # Si est dans une file d'attente de listage des Tweets avec
                    # GetOldTweets3, on la sort, pour la mettre dans la même
                    # file d'attente, mais prioritaire.
                    if request.started_GOT3_listing :
                        # On doit démonter et remonter la file en enlevant la
                        # requête.
                        temp_queue = remove_account_id_from_queue(
                            Pyro4.Proxy( self._step_A_GOT3_list_account_tweets_queue ),
                            account_id )
                        
                        # Désenregistrer l'ancienne file
                        self._root.unregister_obj( self._step_A_GOT3_list_account_tweets_queue )
                        
                        # Enregistrer la nouvelle file
                        self._step_A_GOT3_list_account_tweets_queue = self._root.register_obj( temp_queue, "scan_requests_step_A_GOT3_list_account_tweets_queue" )
                        
                        # On met la requête dans la file d'attente prioritaire.
                        Pyro4.Proxy( self._step_A_GOT3_list_account_tweets_queue ).put( request )
                    
                    # Si est dans une file d'attente de listage des Tweets avec
                    # Twitter API, on la sort, pour la mettre dans la même
                    # file d'attente, mais prioritaire.
                    if request.started_TwitterAPI_listing :
                        # On doit démonter et remonter la file en enlevant la
                        # requête.
                        temp_queue = remove_account_id_from_queue(
                            Pyro4.Proxy( self._step_B_TwitterAPI_list_account_tweets_queue ),
                            account_id )
                        
                        # Désenregistrer l'ancienne file
                        self._root.unregister_obj( self._step_B_TwitterAPI_list_account_tweets_queue )
                        
                        # Enregistrer la nouvelle file
                        self._step_B_TwitterAPI_list_account_tweets_queue = self._root.register_obj( temp_queue, "scan_requests_step_B_TwitterAPI_list_account_tweets_queue" )
                        
                        # On met la requête dans la file d'attente prioritaire.
                        Pyro4.Proxy( self._step_B_TwitterAPI_list_account_tweets_queue ).put( request )
                    
                    # Comme les deux autres files d'attentes sont rapides à
                    # dérouler (Et surtout sont ralenties par les deux
                    # premières), il n'y a pas besoin de bouger les requêtes,
                    # ça se fera tout seul avec le "request.is_prioritary".
                
                queues_sem.release()
                requests_sem.release()
                return request
        
        # Créer et ajouter l'objet Scan_Request à notre système.
        request = self._root.register_obj( Scan_Request( self._root,
                                                         account_id,
                                                         account_name,
                                                         is_prioritary = is_prioritary ), None )
        self._pending_requests_count += 1 # Augmenter le compteur du nombre de requêtes en cours de traitement
        self._requests[ account_id ] = request # On passe ici l'URI de l'objet.
        
        request = Pyro4.Proxy( request )
        
        # Comme le traitement des requêtes de scan est parallélisé, on peut
        # mettre la requêtes dans toutes les files d'attente.
        if is_prioritary :
            Pyro4.Proxy( self._step_A_GOT3_list_account_tweets_prior_queue ).put( request )
            Pyro4.Proxy( self._step_B_TwitterAPI_list_account_tweets_prior_queue ).put( request )
            Pyro4.Proxy( self._step_C_GOT3_index_account_tweets_prior_queue ).put( request )
            Pyro4.Proxy( self._step_D_TwitterAPI_index_account_tweets_prior_queue ).put( request )
        else :
            Pyro4.Proxy( self._step_A_GOT3_list_account_tweets_queue ).put( request )
            Pyro4.Proxy( self._step_B_TwitterAPI_list_account_tweets_queue ).put( request )
            Pyro4.Proxy( self._step_C_GOT3_index_account_tweets_queue ).put( request )
            Pyro4.Proxy( self._step_D_TwitterAPI_index_account_tweets_queue ).put( request )
        
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
    def get_request ( self, account_id : str ) -> Scan_Request :
        self._requests_sem.acquire()
        for key in self._requests :
            if key == account_id :
                self._requests_sem.release()
                return Pyro4.Proxy( self._requests[key] )
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
            self._pending_requests_count -= 1
            
            # On peut lacher le sémaphore, tant pis pour les statistiques, car
            # Python nous garantie qu'il n'y aura pas deux écritures en même temps
            self._requests_sem.release()
            
            # On peut Màj les statistiques mises en cache dans l'objet Shared_Memory
            if get_stats != None :
                self._root.tweets_count, self._root.accounts_count = get_stats
            
            # On peut supprimer l'objet Common_Tweet_IDs_List() pour gagner de la
            # mémoire vive
            request.indexing_tweets = None
            
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
            request = Pyro4.Proxy( request_uri )
            
            # Si la requête est terminée, il faut vérifier qu'on puisse la garder
            if request.finished_date != None :
                
                # Si la date de fin est à moins de 24h de maintenant, on garde
                # cette requête
                if now - request.finished_date < datetime.timedelta( hours = 24 ) :
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
            try :
                self._root.unregister_obj( uri )
            except Pyro4.errors.DaemonError : # Déjà désenregistré
                pass
        
        # On débloque l'accès à la liste des requêtes
        self._requests_sem.release()
