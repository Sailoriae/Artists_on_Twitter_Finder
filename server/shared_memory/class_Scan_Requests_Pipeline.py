#!/usr/bin/python3
# coding: utf-8

import Pyro4
import datetime

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
        # URI, et donc uniques, on peut faire une liste principale qui contient
        # toutes les requêtes. C'est donc une liste de chaines !
        self._requests = []
        
        # Sémaphore d'accès à la liste précédente.
        self._requests_sem = self._root.register_obj( Pyro_Semaphore(), "scan_requests_requests_sem" )
        
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
        requests_sem = Pyro4.Proxy( self._requests_sem )
        queues_sem = Pyro4.Proxy( self._queues_sem )
        
        requests_sem.acquire()
        queues_sem.acquire()
        
        # Vérifier d'abord qu'on n'est pas déjà en train de traiter ce compte.
        for request_uri in self._requests :
            request = Pyro4.Proxy( request_uri )
            if request.account_id == account_id :
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
        self._requests.append( request ) # Passé par URI car c'est un objet.
        
        request = Pyro4.Proxy( request )
        
        # Comme le traitement des requêtes de scan est parallélisé, on peut
        # mettre la requêtes dans toutes les files d'attente
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
        requests_sem = Pyro4.Proxy( self._requests_sem )
        requests_sem.acquire()
        for request_uri in self._requests :
            request = Pyro4.Proxy( request_uri )
            if request.account_id == account_id :
                requests_sem.release()
                return request
        requests_sem.release()
        
        return None
    
    """
    Délester les anciennes requêtes.
    """
    def shed_requests ( self ) :
        # On prend la date actuelle
        now = datetime.datetime.now()
        
        # On bloque l'accès la liste des requêtes
        Pyro4.Proxy( self._requests_sem ).acquire()
        
        # On filtre la liste des requêtes de scan
        new_requests_list = []
        to_unregister_list = []
        
        for request_uri in self._requests :
            request = Pyro4.Proxy( request_uri )
            
            # Si la requête est terminée, il faut vérifier qu'on puisse la garder
            if request.finished_date != None :
                
                # Si la date de fin est à moins de 24h de maintenant, on garde
                # cette requête
                if now - request.finished_date < datetime.timedelta( hours = 24 ) :
                    new_requests_list.append( request_uri )
                
                else : # On désenregistre la requête
                    to_unregister_list.append( request_uri )
            
            # Sinon, on la garde forcément
            else :
                new_requests_list.append( request_uri )
        
        # On installe la nouvelle liste
        self._requests = new_requests_list
        
        # On désenregistre les requêtes à désenregistrer
        # Mais normalement le garbadge collector l'a fait avant nous
        # Oui : Pyro4 désenregistre les objets que le garbadge collector a viré
        for uri in to_unregister_list :
            try :
                self._root.unregister_obj( uri )
            except Pyro4.errors.DaemonError : # Déjà désenregistré
                pass
        
        # On débloque l'accès à la liste des requêtes
        Pyro4.Proxy( self._requests_sem ).release()
