#!/usr/bin/python3
# coding: utf-8

import Pyro4
from time import time

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendemment (Notemment pour des
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

from shared_memory.class_Pyro_Queue import Pyro_Queue
from shared_memory.class_Common_Tweet_IDs_List import Common_Tweet_IDs_List
from shared_memory.open_proxy import open_proxy


"""
Classe représentant une indexation (Nouvelle ou mise à jour) d'un ID de compte
Twitter dans la base de données. Cet objet est le même durant tout le processus
de traitement.

Une requête est identifiée par l'ID du compte Twitter.

Note : Pour les objets, on stocke en réalité l'URI qui mène à l'objet sur le
serveur Pyro, et pas l'objet directement (Car Pyro ne peut pas exécuter sur le
serveur les méthodes des sous-objets), et pas le Proxy vers l'objet (Car un
Proxy ne peut être utilisé que par un seul thread à la fois).
"""
@Pyro4.expose
class Scan_Request :
    # Type de requête, pour la reconnaitre plus facilement dans le collecteur
    # d'erreurs
    _request_type = "scan"
    
    """
    @param account_id L'ID du compte Twitter à indexer / scanner. Ne sert qu'à
                      identifier.
    @param acount_name Le nom du compte Twitter à indexer / scanner. Attention,
                       c'est lui qui est revérifié et scanné !
    @param is_prioritary Est ce que cette requête est prioritaire ?
    """
    def __init__ ( self, root_shared_memory,
                         account_id : int,
                         acount_name : str,
                         is_prioritary : bool = False ) :
        self._root = root_shared_memory
        
        self._account_id = account_id
        self._account_name = acount_name
        self._is_prioritary = is_prioritary
        
        # Si le compte est introuvable
        self._unfound_account = False
        
        # Si jamais un thread de traitement a planté avec la requête, le
        # collecteur d'erreur l'indiquera ici
        self._has_failed = False
        
        # File d'attente pour mettre les Tweets trouvés par l'API de recherche
        self._SearchAPI_tweets_queue = self._root.register_obj( Pyro_Queue() )
        
        # Résultat de la fonction
        # Tweets_Lister_with_SearchAPI.list_SearchAPI_tweets() (Etape A)
        # Contient la date du Tweet trouvé par l'API de recherche le plus récent
        self._SearchAPI_last_tweet_date = None
        
        # File d'attente pour mettre les Tweets trouvés par l'API de timeline
        self._TimelineAPI_tweets_queue = self._root.register_obj( Pyro_Queue() )
        
        # Résultat de la fonction
        # Tweets_Lister_with_TimelineAPI.list_TimelineAPI_tweets() (Etape B)
        # Contient l'ID du Tweet trouvé par l'API de timeline le plus récent
        self._TimelineAPI_last_tweet_id = None
        
        # Deux variables de début de traitement de la requête
        # Permet de savoir si, lors d'un éventuel passage de la requête en
        # prioritaire, on doit démonter les files des étapes A et B ou pas
        self._started_SearchAPI_listing = False
        self._started_TimelineAPI_listing = False
        
        # Cache pour les deux listeurs (Etapes A et B)
        # ID dans la liste params.TWITTER_API_KEYS des tokens bloqués par
        # ce compte
        self._blocks_list = []
        
        # Cache pour les deux indexeurs (Etapes C et D)
        # Permet de savoir quand la requête a été vue pour la dernière fois,
        # afin de ne pas trop itérer dessus
        self._last_seen_SearchAPI_indexer = 0
        self._last_seen_TimelineAPI_indexer = 0
        
        # Cache pour les deux indexeurs (Etape C et D)
        # Permet de savoir si l'autre est en train ou a déjà traiter un Tweet,
        # sans avoir à faire un appel à la base de données
        self._indexing_tweets = self._root.register_obj( Common_Tweet_IDs_List() )
        
        # Cache pour les deux indexeurs (Etape C et D)
        # Savoir si la requête est dans l'un des deux ou pas
        # Permet de savoir si, lors d'un éventuel passage de la requête en
        # prioritaire, on doit démonter les files des étapes C et D ou pas
        self._is_in_SearchAPI_indexing = False
        self._is_in_TimelineAPI_indexing = False
        
        # Deux variables de fin du traitement de la requête
        self._finished_SearchAPI_indexing = False
        self._finished_TimelineAPI_indexing = False
        
        # Date de début de la procédure
        self._start = time()
        
        # Date de fin de la procédure
        self._finished_date = None
    
    """
    Getters et setters pour Pyro.
    """
    @property
    def request_type( self ) : return self._request_type
    
    @property
    def account_id( self ) : return self._account_id
    
    @property
    def account_name( self ) : return self._account_name
    
    @property
    def is_prioritary( self ) : return self._is_prioritary
    @is_prioritary.setter
    def is_prioritary( self, value ) : self._is_prioritary = value
    
    @property
    def unfound_account( self ) : return self._unfound_account
    @unfound_account.setter
    def unfound_account( self, value ) : self._unfound_account = value
    
    @property
    def has_failed( self ) : return self._has_failed
    @has_failed.setter
    def has_failed( self, value ) : self._has_failed = value
    
    @property
    def SearchAPI_tweets_queue( self ) : return open_proxy( self._SearchAPI_tweets_queue )
    @property # Pour end_request()
    def SearchAPI_tweets_queue_uri( self ) : return self._SearchAPI_tweets_queue
    @SearchAPI_tweets_queue_uri.setter # Pour end_request()
    def SearchAPI_tweets_queue_uri( self, value ) : self._SearchAPI_tweets_queue = value
    
    @property
    def SearchAPI_last_tweet_date( self ) : return self._SearchAPI_last_tweet_date
    @SearchAPI_last_tweet_date.setter
    def SearchAPI_last_tweet_date( self, value ) : self._SearchAPI_last_tweet_date = value
    
    @property
    def TimelineAPI_tweets_queue( self ) : return open_proxy( self._TimelineAPI_tweets_queue )
    @property # Pour end_request()
    def TimelineAPI_tweets_queue_uri( self ) : return self._TimelineAPI_tweets_queue
    @TimelineAPI_tweets_queue_uri.setter # Pour end_request()
    def TimelineAPI_tweets_queue_uri( self, value ) : self._TimelineAPI_tweets_queue = value
    
    @property
    def TimelineAPI_last_tweet_id( self ) : return self._TimelineAPI_last_tweet_id
    @TimelineAPI_last_tweet_id.setter
    def TimelineAPI_last_tweet_id( self, value ) : self._TimelineAPI_last_tweet_id = value
    
    @property
    def started_SearchAPI_listing( self ) : return self._started_SearchAPI_listing
    @started_SearchAPI_listing.setter
    def started_SearchAPI_listing( self, value ) : self._started_SearchAPI_listing = value
    
    @property
    def started_TimelineAPI_listing( self ) : return self._started_TimelineAPI_listing
    @started_TimelineAPI_listing.setter
    def started_TimelineAPI_listing( self, value ) : self._started_TimelineAPI_listing = value
    
    @property
    def blocks_list( self ) : return self._blocks_list
    @blocks_list.setter
    def blocks_list( self, value ) : self._blocks_list = value
    
    @property
    def last_seen_SearchAPI_indexer( self ) : return self._last_seen_SearchAPI_indexer
    @last_seen_SearchAPI_indexer.setter
    def last_seen_SearchAPI_indexer( self, value ) : self._last_seen_SearchAPI_indexer = value
    
    @property
    def last_seen_TimelineAPI_indexer( self ) : return self._last_seen_TimelineAPI_indexer
    @last_seen_TimelineAPI_indexer.setter
    def last_seen_TimelineAPI_indexer( self, value ) : self._last_seen_TimelineAPI_indexer = value
    
    @property
    def indexing_tweets( self ) : return open_proxy( self._indexing_tweets )
    @property # Pour end_request()
    def indexing_tweets_uri( self ) : return self._indexing_tweets
    @indexing_tweets_uri.setter # Pour end_request()
    def indexing_tweets_uri( self, value ) : self._indexing_tweets = value
    
    @property
    def is_in_SearchAPI_indexing( self ) : return self._is_in_SearchAPI_indexing
    @is_in_SearchAPI_indexing.setter
    def is_in_SearchAPI_indexing( self, value ) : self._is_in_SearchAPI_indexing = value
    
    @property
    def is_in_TimelineAPI_indexing( self ) : return self._is_in_TimelineAPI_indexing
    @is_in_TimelineAPI_indexing.setter
    def is_in_TimelineAPI_indexing( self, value ) : self._is_in_TimelineAPI_indexing = value
    
    @property
    def finished_SearchAPI_indexing( self ) : return self._finished_SearchAPI_indexing
    @finished_SearchAPI_indexing.setter
    def finished_SearchAPI_indexing( self, value ) : self._finished_SearchAPI_indexing = value
    
    @property
    def finished_TimelineAPI_indexing( self ) : return self._finished_TimelineAPI_indexing
    @finished_TimelineAPI_indexing.setter
    def finished_TimelineAPI_indexing( self, value ) : self._finished_TimelineAPI_indexing = value
    
    @property
    def start( self ) : return self._start
    
    @property
    def finished_date( self ) : return self._finished_date
    @finished_date.setter
    def finished_date( self, value ) : self._finished_date = value
