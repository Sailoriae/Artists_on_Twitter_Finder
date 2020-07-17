#!/usr/bin/python3
# coding: utf-8

import threading
import queue
from typing import List

try :
    from class_Request import Request
except ModuleNotFoundError :
    from .class_Request import Request

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param
from tweet_finder.twitter import TweepyAbtraction


"""
MEMOIRE PARTAGEE ENTRE TOUS LES THEADS.
Classe contenant l'ensemble des requêtes dans le système.
A INITIALISER UNE SEULE FOIS !

Les objets sont passés par adresse en Python.
Donc ils peuvent être en même temps dans dans la liste "requests" en en même
temps dans les différentes files d'attente (Objets queue.Queue) !

De plus, l'objet queue.Queue() est safe pour le multi-threads.
"""
class Pipeline :
    def __init__ ( self ) :
        # Variable pour éteindre tout le système
        self.keep_service_alive = True
        
        # Liste des requêtes qui vont passer par toute la procédure
        # C'est à dire les requêtes données par via l'API web ou la commande
        # "request" de la CLI.
        self.requests = []
        
        # Sémaphore pour l'accès à la liste "request"
        self.requests_sem = threading.Semaphore()
        
        
        # Dictionnaire où les threads mettent leur requête en cours de
        # traitement, afin que leurs collecteurs d'erreurs mettent ces
        # requêtes en échec lors d'un plantage
        # Les threads sont identifiés par la chaine suivante :
        # procédure_du_thread.__name__ + "_number" + str(thread_id)
        self.requests_in_thread = {}
        
        
        # ETAPE 1, code de status de la requête : 1
        # File d'attente de Link Finder
        # Code de status de la requête : 0
        self.step_1_link_finder_queue = queue.Queue()
        
        # ETAPE 2, code de status de la requête : 3
        # File d'attente de listage des tweets d'un compte Twitter
        # Code de status de la requête : 2
        # Pour l'indexation GetOldTweets3
        self.step_2_GOT3_list_account_tweets_queue = queue.Queue()
        
        # ETAPE 3, code de status de la requête : 5
        # File d'attente d'indexation des tweets d'un compte Twitter
        # Code de status de la requête : 4
        # Avec GetOldTweets3
        self.step_3_GOT3_index_account_tweets_queue = queue.Queue()
        
        # ETAPE 4, code de status de la requête : 7
        # File d'attente d'indexation des tweets d'un compte Twitter
        # Code de status de la requête : 6
        # Avec l'API Twitter publique
        self.step_4_TwitterAPI_index_account_tweets_queue = queue.Queue()
        
        # ETAPE 5, code de status de la requête : 9
        # File d'attente de la recherche d'image inversée
        # Code de status de la requête : 8
        self.step_5_reverse_search_queue = queue.Queue()
        
        
        # Liste des ID de comptes Twitter en cours d'indexation
        # Dans l'un des 3 threads de l'indexation :
        # - thread_step_2_GOT3_list_account_tweets
        # - thread_step_3_GOT3_index_account_tweets
        # - thread_step_4_TwitterAPI_index_account_tweets
        #
        # C'est un thread "thread_step_2_GOT3_list_account_tweets"
        # qui met l'ID dans cette liste, et un thread
        # "thread_step_4_TwitterAPI_index_account_tweets" qui le
        # retire
        self.currently_indexing = []
        
        # Sémaphore d'accès à la liste précédente
        self.currently_indexing_sem = threading.Semaphore()
        
        
        # Initialisation de notre couche d'abstraction à l'API Twitter
        self.twitter = TweepyAbtraction( param.API_KEY,
                                         param.API_SECRET,
                                         param.OAUTH_TOKEN,
                                         param.OAUTH_TOKEN_SECRET )
        
        
        # Dictionnaire contenant le nombre de requêtes en cours de traitement
        # par addresse IP
        self.dict_of_ip_addresses = {}
        
        # Sémaphore d'accès au dictionnaire précédente
        self.dict_of_ip_addresses_sem = threading.Semaphore()
    
    """
    Lancement de la procédure complète pour une URL d'illustration.
    Les requêtes sont idendifiées par l'URL de l'illustration d'entrée.
    
    @param illust_url L'illustration d'entrée.
    @param ip_address L'addresse IP qui a demandé cette requête à enregistrer.
                      Enregistrée avec la requête uniquement dans le cas de
                      création d'une nouvelle requête.
                      (OPTIONNEL)
    @return L'objet Request créé.
            Ou l'objet Request déjà existant.
            Ou None si l'addresse IP passée en paramètre a atteint son nombre
            maximum de requêtes en cours de traitement.
    """
    def launch_full_process ( self, illust_url : str, ip_address : str = None ) :
        # Vérifier d'abord qu'on n'est pas déjà en train de traiter cette illustration
        self.requests_sem.acquire()
        for request in self.requests :
            if request.input_url == illust_url :
                self.requests_sem.release()
                return request
        
        if not self.add_ip_address( ip_address ) :
            self.requests_sem.release()
            return None
        
        request = Request( illust_url, self, do_link_finder = True,
                                             do_indexing = True,
                                             do_reverse_search = True,
                                             ip_address = ip_address )
        self.requests.append( request ) # Passé par adresse car c'est un objet
        
        self.requests_sem.release() # Seulement ici !
        
        self.step_1_link_finder_queue.put( request ) # Passé par addresse car c'est un objet
        
        return request
    
    """
    Lancer uniquement l'étape de scan d'un compte Twitter.
    Fait les 3 threads suivants :
    - "thread_step_2_GOT3_list_account_tweets"
    - "thread_step_3_GOT3_index_account_tweets"
    - "thread_step_4_TwitterAPI_index_account_tweets"
    
    @return True si le compte Twitter existe.
            False si le compte est inexistant.
    """
    def launch_index_or_update_only ( self, account_name = None, account_id = None ) :
        if account_id == None :
            account_id = self.twitter.get_account_id( account_name )
        elif account_name == None :
            account_name = self.twitter.get_account_id( account_id, invert_mode = True )
        
        # Si le compte est invalide
        if account_id == None or account_name == None :
            return False
        
        # On crée une requête de MàJ avec ce compte Twitter
        request = Request( None, self, do_indexing = True )
        
        # On ajoute le compte Twitter
        request.twitter_accounts.append( account_name )
        request.twitter_accounts_with_id.append( (account_name, account_id) ) 
        
        # On met le compte Twitter dans la file d'attente du premier thread
        # de scan
        self.step_2_GOT3_list_account_tweets_queue.put( request )
    
    """
    Passer la requête à l'étape suivante.
    """
    def set_request_to_next_step ( self, request : Request ) :
        if request.status < 10 :
            request.status += 1
        
        if request.status == 0 and request.do_link_finder :
            self.step_1_link_finder_queue.put( request )
        
        if request.status == 2 and request.do_indexing :
            self.step_2_GOT3_list_account_tweets_queue.put( request )
        
        if request.status == 4 and request.do_indexing :
            self.step_3_GOT3_index_account_tweets_queue.put( request )
        
        if request.status == 6 and request.do_indexing :
            self.step_4_TwitterAPI_index_account_tweets_queue.put( request )
        
        if request.status == 8 and request.do_reverse_search :
            self.step_5_reverse_search_queue.put( request )
    
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
    Vérifier qu'un compte Twitter est en cours d'indexation ou non.
    @param twitter_account_ID L'ID du compte twitter.
    @return True ou False
    """
    def check_is_indexing ( self, twitter_account_ID : int ) -> bool :
        self.currently_indexing_sem.acquire()
        
        for account_id in self.currently_indexing :
            if account_id == twitter_account_ID :
                self.currently_indexing_sem.release()
                return True
        
        self.currently_indexing_sem.release()
        return False
    
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
    
    """
    Ajouter +1 au nombre de requête en cours de traitement pour une addresse IP.
    
    @param ip_address L'addresse IP à ajouter
    @return True si on a pu faire +1
            False si l'addresse IP a atteint son nombre maximum de requêtes en
            cours de traitement.
    """
    def add_ip_address ( self, ip_address : str ) -> bool :
        if ip_address in param.UNLIMITED_IP_ADDRESSES :
            return True
        
        self.dict_of_ip_addresses_sem.acquire()
        try :
            current_count = self.dict_of_ip_addresses[ ip_address ]
        except KeyError :
            self.dict_of_ip_addresses[ ip_address ] = 1
            self.dict_of_ip_addresses_sem.release()
            return True
        
        else :
            if current_count < param.MAX_PENDING_REQUESTS_PER_IP_ADDRESS :
                self.dict_of_ip_addresses[ ip_address ] = current_count + 1
                self.dict_of_ip_addresses_sem.release()
                return True
            else :
                self.dict_of_ip_addresses_sem.release()
                return False
    
    """
    Supprimer une addresse IP à la liste des addresses IP qui ont une requête
    en cours de traitement.
    Si l'addresse est en plusieurs exemplaire, elle sera supprimée qu'une seule
    fois.
    
    @param ip_address L'addresse IP à supprimer
    """
    def remove_ip_address ( self, ip_address : str ) :
        self.dict_of_ip_addresses_sem.acquire()
        try :
            current_count = self.dict_of_ip_addresses[ ip_address ]
        except KeyError :
            pass
        else :
            self.dict_of_ip_addresses[ ip_address ] = current_count - 1
        self.dict_of_ip_addresses_sem.release()
