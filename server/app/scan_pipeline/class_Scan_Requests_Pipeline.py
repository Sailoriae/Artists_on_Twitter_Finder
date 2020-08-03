#!/usr/bin/python3
# coding: utf-8

import queue
import threading

try :
    from class_Scan_Request import Scan_Request
    from remove_account_id_from_queue import remove_account_id_from_queue
except ModuleNotFoundError :
    from .class_Scan_Request import Scan_Request
    from .remove_account_id_from_queue import remove_account_id_from_queue


"""
Classe de gestion des requêtes d'indexation (Nouvelle ou mise à jour) comptes
Twitter dans la base de données.
Instanciée une seule fois lors de l'unique instanciation de la mémoire
partagée, c'est à dire de la classe Shared_Memory.

Les requêtes sont identifiées par l'ID du compte Twitter.

Attention : Ce pipeline de traitement est parallélisé, et non étapes par
étapes !
"""
class Scan_Requests_Pipeline :
    def __init__ ( self ) :
        # Comme les objets sont passés par adresse en Python, on peut faire une
        # liste principale qui contient toutes les requêtes.
        self.requests = []
        
        # Sémaphore d'accès à la liste précédente.
        self.requests_sem = threading.Semaphore()
        
        # File d'attente à l'étape A du traitement : Listage des Tweets avec
        # GetOldTweets3.
        # Les objets queue.Queue sont prévus pour faire du multi-threading.
        self.step_A_GOT3_list_account_tweets_prior_queue = queue.Queue()
        
        # Version non-prioritaire de la file d'attente précédente.
        self.step_A_GOT3_list_account_tweets_queue = queue.Queue()
        
        # File d'attente à l'étape B du traitement : Listage des Tweets avec
        # l'API publique Twitter.
        self.step_B_TwitterAPI_list_account_tweets_prior_queue = queue.Queue()
        
        # Version non-prioritaire de la file d'attente précédente.
        self.step_B_TwitterAPI_list_account_tweets_queue = queue.Queue()
        
        # File d'attente à l'étape C du traitement : Indexation des Tweets
        # trouvés par le listage des Tweets avec GetOldTweets3.
        self.step_C_GOT3_index_account_tweets_prior_queue = queue.Queue()
        
        # Version non-prioritaire de la file d'attente précédente.
        self.step_C_GOT3_index_account_tweets_queue = queue.Queue()
        
        # File d'attente à l'étape D du traitement : Indexation des Tweets
        # trouvés par le listage des Tweets avec l'API publique Twitter.
        self.step_D_TwitterAPI_index_account_tweets_prior_queue = queue.Queue()
        
        # Version non-prioritaire de la file d'attente précédente.
        self.step_D_TwitterAPI_index_account_tweets_queue = queue.Queue()
        
        # Bloquer toutes les files d'attentes. Permet de passer une requête
        # en prioritaire sans avoir de problème.
        self.queues_sem = threading.Semaphore()
        
        # Dictionnaire où les threads mettent leur requête en cours de
        # traitement, afin que leurs collecteurs d'erreurs mettent ces
        # requêtes en échec lors d'un plantage.
        # Les threads sont identifiés par la chaine suivante :
        # procédure_du_thread.__name__ + "_number" + str(thread_id)
        self.requests_in_thread = {}
    
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
        self.requests_sem.acquire()
        self.queues_sem.acquire()
        
        # Vérifier d'abord qu'on n'est pas déjà en train de traiter ce compte.
        for request in self.requests :
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
                        self.step_A_GOT3_list_account_tweets_queue = remove_account_id_from_queue(
                            self.step_A_GOT3_list_account_tweets_queue,
                            account_id )
                        
                        # On met la requête dans la file d'attente prioritaire.
                        self.step_A_GOT3_list_account_tweets_queue.put( request )
                    
                    # Si est dans une file d'attente de listage des Tweets avec
                    # Twitter API, on la sort, pour la mettre dans la même
                    # file d'attente, mais prioritaire.
                    if request.started_TwitterAPI_listing :
                        # On doit démonter et remonter la file en enlevant la
                        # requête.
                        self.step_B_TwitterAPI_list_account_tweets_queue = remove_account_id_from_queue(
                            self.step_B_TwitterAPI_list_account_tweets_queue,
                            account_id )
                        
                        # On met la requête dans la file d'attente prioritaire.
                        self.step_B_TwitterAPI_list_account_tweets_queue.put( request )
                    
                    # Comme les deux autres files d'attentes sont rapides à
                    # dérouler (Et surtout sont ralenties par les deux
                    # premières), il n'y a pas besoin de bouger les requêtes,
                    # ça se fera tout seul avec le "request.is_prioritary".
                
                self.queues_sem.release()
                self.requests_sem.release()
                return request
        
        # Créer et ajouter l'objet Scan_Request à notre système.
        request = Scan_Request( account_id,
                                account_name,
                                is_prioritary = is_prioritary )
        self.requests.append( request ) # Passé par adresse car c'est un objet.
        
        
        # Comme le traitement des requêtes de scan est parallélisé, on peut
        # mettre la requêtes dans toutes les files d'attente
        if is_prioritary :
            self.step_A_GOT3_list_account_tweets_prior_queue.put( request )
            self.step_B_TwitterAPI_list_account_tweets_prior_queue.put( request )
            self.step_C_GOT3_index_account_tweets_prior_queue.put( request )
            self.step_D_TwitterAPI_index_account_tweets_prior_queue.put( request )
        else :
            self.step_A_GOT3_list_account_tweets_queue.put( request )
            self.step_B_TwitterAPI_list_account_tweets_queue.put( request )
            self.step_C_GOT3_index_account_tweets_queue.put( request )
            self.step_D_TwitterAPI_index_account_tweets_queue.put( request )
        
        self.queues_sem.release()
        self.requests_sem.release()
        
        # Retourner l'objet Scan_Request.
        return request
    
    """
    Obtenir l'objet Scan_Request d'une requête.
    
    @param account_id L'ID du compte Twitter.
    @return Un objet Scan_Request,
            Ou None si la requête est inconnue.
    """
    def get_request ( self, account_id : str ) -> Scan_Request :
        self.requests_sem.acquire()
        for request in self.requests :
            if request.account_id == account_id :
                self.requests_sem.release()
                return request
        self.requests_sem.release()
        
        return None