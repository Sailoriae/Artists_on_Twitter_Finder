#!/usr/bin/python3
# coding: utf-8

import threading
import queue
from typing import List

try :
    from class_Request import Request
except ModuleNotFoundError :
    from .class_Request import Request


"""
MEMOIRE PARTAGEE ENTRE TOUS LES THEADS.
Classe contenant l'ensemble des requêtes dans le système.
A INITIALISER UNE SEULE FOIS !

Les objets sont passés par adresse en Python.
Donc ils peuvent être en même temps dans dans la liste "requests" en en même temps
dans les différentes files d'attente (Objets queue.Queue) !

De plus, l'objet queue.Queue() est safe pour le multi-threads.
"""
class Pipeline :
    def __init__ ( self ) :
        # Variable pour éteindre le service
        self.keep_service_alive = True
        
        # Liste des requêtes effectuées sur notre système
        self.requests = []
        
        # Sémaphore pour l'accès à la liste request
        self.requests_sem = threading.Semaphore()
        
        # ETAPE 1, code de status de la requête : 1
        # File d'attente de Link Finder
        self.link_finder_queue = queue.Queue()
        
        # ETAPE 2, PARTIE 1/2, code de status de la requête : 3
        # File d'attente de listage des tweets d'un compte Twitter
        self.list_account_tweets_queue = queue.Queue()
        
        # ETAPE 2, PARTIE 2/2, code de status de la requête : 5
        # File d'attente d'indexation des tweets d'un compte Twitter
        self.index_twitter_account_queue = queue.Queue()
        
        # ETAPE 3, code de status de la requête : 7
        # File d'attente de la recherche d'image inversée
        self.reverse_search_queue = queue.Queue()
        
        
        # Liste des ID de comptes Twitter en cours de listage
        # Dans un thread list_account_tweets_thread_main()
        self.currently_listing = []
        
        # Sémaphore d'accès à la liste précédente
        self.currently_listing_sem = threading.Semaphore()
        
        
        # Liste des ID de comptes Twitter en cours d'indexation
        # Dans un thread index_twitter_account_thread_main()
        self.currently_indexing = []
        
        # Sémaphore d'accès à la liste précédente
        self.currently_indexing_sem = threading.Semaphore()
    
    """
    Lancement de la procédure complète pour une URL d'illustration.
    @param illust_url L'illustration d'entrée.
    @return L'objet Request créé.
    """
    def launch_full_process ( self, illust_url : str ) :
        # Vérifier d'abord qu'on n'est pas déjà en train de traiter cette illustration
        self.requests_sem.acquire()
        for request in self.requests :
            if request.input_url == illust_url :
                self.requests_sem.release()
                return
        
        request = Request( illust_url, full_pipeline = True )
        self.requests.append( request ) # Passé par adresse car c'est un objet
        
        self.requests_sem.release() # Seulement ici !
        
        self.link_finder_queue.put( request ) # Passé par addresse car c'est un objet
        
        return request
    
    """
    Obtenir l'objet d'une requête.
    @param illust_url L'illustration d'entrée.
    @return Un objet Request,
            Ou None si la requête est inconnue.
    """
    def get_request ( self, illust_url : str ) -> Request :
        self.requests_sem.acquire()
        for request in self.requests :
            if request.input_url == illust_url :
                self.requests_sem.release()
                return request
        self.requests_sem.release()
        
        return None
    
    """
    Dire qu'on est en train de lister les tweets de ces IDs de comptes Twitter.
    
    @param twitter_account_IDs Liste d'IDs de comptes Twitter
    @return False si aucun des IDs de la liste était en cours de listage.
            True si au moins un ID était déjà en cours de listage ! Les autres
            IDs n'ont pas étés marqués comme en cours de listage, il ne faut
            pas continuer avec cette liste !
    """
    def is_listing ( self, twitter_account_IDs : List[int] ) -> bool :
        self.currently_listing_sem.acquire()
        
        IDs_to_add = []
        
        for account_id in twitter_account_IDs :
            # Vérifier que l'ID n'est pas déjà dans la liste
            if account_id in self.currently_listing :
                self.currently_listing_sem.release()
                return True
            else :
                IDs_to_add.append( account_id )
        
        self.currently_listing += IDs_to_add
        self.currently_listing_sem.release()
        
        return False
    
    """
    Dire qu'on est en train d'indexer les tweets de ces IDs de comptes Twitter.
    
    @param twitter_account_IDs Liste d'IDs de comptes Twitter
    @return False si aucun des IDs de la liste était en cours de indexation.
            True si au moins un ID était déjà en cours de indexation ! Les autres
            IDs n'ont pas étés marqués comme en cours de indexation, il ne faut
            pas continuer avec cette liste !
    """
    def is_indexing ( self, twitter_account_IDs : List[int] ) -> bool :
        self.currently_indexing_sem.acquire()
        
        IDs_to_add = []
        
        for account_id in twitter_account_IDs :
            # Vérifier que l'ID n'est pas déjà dans la liste
            if account_id in self.currently_indexing :
                self.currently_indexing_sem.release()
                return True
            else :
                IDs_to_add.append( account_id )
        
        self.currently_indexing += IDs_to_add
        self.currently_indexing_sem.release()
        
        return False
    
    """
    Dire qu'on a fini de lister les tweets de ces IDs de compte Twitter.
    
    @param twitter_account_IDs Liste d'IDs de comptes Twitter
    """
    def listing_done ( self, twitter_account_IDs : List[int] ) :
        self.currently_listing_sem.acquire()
        new_list = []
        for account_id in self.currently_listing :
            if not account_id in twitter_account_IDs :
                new_list.append( account_id )
        self.currently_listing = new_list
        self.currently_listing_sem.release()
    
    """
    Dire qu'on a fini d'indexer les tweets de ces IDs de compte Twitter.
    
    @param twitter_account_IDs Liste d'IDs de comptes Twitter
    """
    def indexing_done ( self, twitter_account_IDs : List[int] ) :
        self.currently_indexing_sem.acquire()
        new_list = []
        for account_id in self.currently_indexing :
            if not account_id in twitter_account_IDs :
                new_list.append( account_id )
        self.currently_indexing = new_list
        self.currently_indexing_sem.release()
