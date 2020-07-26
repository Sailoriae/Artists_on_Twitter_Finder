#!/usr/bin/python3
# coding: utf-8

import queue
import threading
import copy
from datetime import datetime

try :
    from class_Scan_Request import Scan_Request
except ModuleNotFoundError :
    from .class_Scan_Request import Scan_Request


"""
Classe de gestion des requêtes d'indexation (Nouvelle ou mise à jour) comptes
Twitter dans la base de données.
Instanciée une seule fois lors de l'unique instanciation de la mémoire
partagée, c'est à dire de la classe Shared_Memory.

Les requêtes sont identifiées par l'ID du compte Twitter.
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
        
        # File d'attente à l'étape B du traitement : Indexation des Tweets
        # avec GetOldTweets3.
        self.step_B_GOT3_index_account_tweets_prior_queue = queue.Queue()
        
        # Version non-prioritaire de la file d'attente précédente.
        self.step_B_GOT3_index_account_tweets_queue = queue.Queue()
        
        # File d'attente à l'étape C du traitement : Indexation des Tweets
        # avec l'API Twitter publique.
        self.step_C_TwitterAPI_index_account_tweets_prior_queue = queue.Queue()
        
        # Version non-prioritaire de la file d'attente précédente.
        self.step_C_TwitterAPI_index_account_tweets_queue = queue.Queue()
        
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
        # Vérifier d'abord qu'on n'est pas déjà en train de traiter ce compte.
        self.requests_sem.acquire()
        for request in self.requests :
            if request.account_id == account_id and not request.is_cancelled :
                # Si il faut passer la requête en proritaire.
                if is_prioritary and not request.is_prioritary :
                    self.queues_sem.acquire()
                    request.is_prioritary = True
                    
                    # Si est dans une file d'attente, on la sort, pour la
                    # la mettre dans la même file d'attente, mais prioritaire.
                    if request.status in [ 0, 2, 4 ] :
                        request_new = copy.copy( request ) # Pas besoin de faire un deepcopy()
                        request.is_cancelled = True
                        self.request.append( request_new )
                        request_new.status -= 1
                        self.set_request_to_next_step( request_new )
                    
                    self.queues_sem.release()
                
                self.requests_sem.release()
                return request
        
        # Créer et ajouter l'objet Scan_Request à notre système.
        request = Scan_Request( account_id,
                                account_name,
                                is_prioritary = is_prioritary )
        self.requests.append( request ) # Passé par adresse car c'est un objet.
        self.requests_sem.release() # Seulement ici !
        
        # Les requêtes sont initialisée au status -1
        self.set_request_to_next_step( request )
        
        # Retourner l'objet User_Request.
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
    
    """
    Passer la requête à l'étape suivante.
    A utiliser uniquement à la fin et au début d'une itération d'un thread de
    traitement. Et utilise obligatoirement cette méthode pour modifier le
    status d'une requête.
    """
    def set_request_to_next_step ( self, request : Scan_Request, force_end : bool = False ) :
        self.queues_sem.acquire()
        
        if force_end :
            request.status = 6
        elif request.status < 6 :
            request.status += 1
        
        if request.is_prioritary :
            if request.status == 0 :
                self.step_A_GOT3_list_account_tweets_prior_queue.put( request )
            
            if request.status == 2 :
                self.step_B_GOT3_index_account_tweets_prior_queue.put( request )
            
            if request.status == 4 :
                self.step_C_TwitterAPI_index_account_tweets_prior_queue.put( request )
        
        else :
            if request.status == 0 :
                self.step_A_GOT3_list_account_tweets_queue.put( request )
            
            if request.status == 2 :
                self.step_B_GOT3_index_account_tweets_queue.put( request )
            
            if request.status == 4 :
                self.step_C_TwitterAPI_index_account_tweets_queue.put( request )
        
        if request.status == 6 :
            request.finished_date = datetime.now()
        
        self.queues_sem.release()
