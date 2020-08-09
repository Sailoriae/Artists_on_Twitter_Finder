#!/usr/bin/python3
# coding: utf-8

import Pyro4
from time import time

try :
    from class_Pyro_Queue import Pyro_Queue
    from class_Common_Tweet_IDs_List import Common_Tweet_IDs_List
    from class_Pyro_GOT3_Tweet import Pyro_GOT3_Tweet
except ModuleNotFoundError :
    from .class_Pyro_Queue import Pyro_Queue
    from .class_Common_Tweet_IDs_List import Common_Tweet_IDs_List
    from .class_Pyro_GOT3_Tweet import Pyro_GOT3_Tweet


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
        self._unfounded_account = False
        
        # Si jamais un thread de traitement a planté avec la requête, le
        # collecteur d'erreur l'indiquera ici
        self._has_failed = False
        
        # File d'attente pour mettre les Tweets trouvés par GetOldTweets3
        self._GetOldTweets3_tweets_queue = self._root.register_obj( Pyro_Queue(), None )
        
        # Résultat de la fonction
        # Tweets_Lister_with_GetOldTweets3.list_GOT3_tweets() (Etape A)
        # Contient la date du Tweet trouvé par GOT3 le plus récent
        self._GetOldTweets3_last_tweet_date = None
        
        # File d'attente pour mettre les Tweets trouvés par Tweepy
        self._TwitterAPI_tweets_queue = self._root.register_obj( Pyro_Queue(), None )
        
        # Résultat de la fonction
        # Tweets_Lister_with_TwitterAPI.list_TwitterAPI_tweets() (Etape B)
        # Contient l'ID du Tweet trouvé par l'API Twitter le plus récent
        self._TwitterAPI_last_tweet_id = None
        
        # Deux variables de début de traitement de la requête
        self._started_GOT3_listing = False
        self._started_TwitterAPI_listing = False
        
        # Cache pour les deux indexeurs (Etapes C et D)
        # Permet de savoir quand la requête a été vue pour la dernière fois,
        # afin de ne pas trop itérer dessus
        self._last_seen_GOT3_indexer = 0
        self._last_seen_TwitterAPI_indexer = 0
        
        # Cache pour les deux indexeurs (Etape C et D)
        # Permet de savoir si l'autre est en train ou a déjà traiter un Tweet,
        # sans avoir à faire un appel à la base de données
        self._indexing_tweets = self._root.register_obj( Common_Tweet_IDs_List(), None )
        
        # Deux variables de fin du traitement de la requête
        self._finished_GOT3_indexing = False
        self._finished_TwitterAPI_indexing = False
        
        # Date de début de la procédure
        self._start = time()
        
        # Date de fin de la procédure
        self._finished_date = None
    
    """
    Getters et setters pour Pyro.
    """
    @property
    def account_id( self ) : return self._account_id
    
    @property
    def account_name( self ) : return self._account_name
    
    @property
    def is_prioritary( self ) : return self._is_prioritary
    @is_prioritary.setter
    def is_prioritary( self, value ) : self._is_prioritary = value
    
    @property
    def unfounded_account( self ) : return self._unfounded_account
    @unfounded_account.setter
    def unfounded_account( self, value ) : self._unfounded_account = value
    
    @property
    def has_failed( self ) : return self._has_failed
    @has_failed.setter
    def has_failed( self, value ) : self._has_failed = value
    
    @property
    def GetOldTweets3_last_tweet_date( self ) : return self._GetOldTweets3_last_tweet_date
    @GetOldTweets3_last_tweet_date.setter
    def GetOldTweets3_last_tweet_date( self, value ) : self._GetOldTweets3_last_tweet_date = value
    
    @property
    def TwitterAPI_tweets_queue( self ) : return Pyro4.Proxy( self._TwitterAPI_tweets_queue )
    
    @property
    def TwitterAPI_last_tweet_id( self ) : return self._TwitterAPI_last_tweet_id
    @TwitterAPI_last_tweet_id.setter
    def TwitterAPI_last_tweet_id( self, value ) : self._TwitterAPI_last_tweet_id = value
    
    @property
    def started_GOT3_listing( self ) : return self._started_GOT3_listing
    @started_GOT3_listing.setter
    def started_GOT3_listing( self, value ) : self._started_GOT3_listing = value
    
    @property
    def started_TwitterAPI_listing( self ) : return self._started_TwitterAPI_listing
    @started_TwitterAPI_listing.setter
    def started_TwitterAPI_listing( self, value ) : self._started_TwitterAPI_listing = value
    
    @property
    def last_seen_GOT3_indexer( self ) : return self._last_seen_GOT3_indexer
    @last_seen_GOT3_indexer.setter
    def last_seen_GOT3_indexer( self, value ) : self._last_seen_GOT3_indexer = value
    
    @property
    def last_seen_TwitterAPI_indexer( self ) : return self._last_seen_TwitterAPI_indexer
    @last_seen_TwitterAPI_indexer.setter
    def last_seen_TwitterAPI_indexer( self, value ) : self._last_seen_TwitterAPI_indexer = value
    
    @property
    def indexing_tweets( self ) : return Pyro4.Proxy( self._indexing_tweets )
    @indexing_tweets.setter
    def indexing_tweets( self, value ) : self._indexing_tweets = value
    
    @property
    def finished_GOT3_indexing( self ) : return self._finished_GOT3_indexing
    @finished_GOT3_indexing.setter
    def finished_GOT3_indexing( self, value ) : self._finished_GOT3_indexing = value
    
    @property
    def finished_TwitterAPI_indexing( self ) : return self._finished_TwitterAPI_indexing
    @finished_TwitterAPI_indexing.setter
    def finished_TwitterAPI_indexing( self, value ) : self._finished_TwitterAPI_indexing = value
    
    @property
    def start( self ) : return self._start
    
    @property
    def finished_date( self ) : return self._finished_date
    @finished_date.setter
    def finished_date( self, value ) : self._finished_date = value
    
    """
    get() et put() pour la file des Tweets trouvés par GOT3, car ils ne peuvent
    pas être sérialisés !
    """
    def GetOldTweets3_tweets_queue_put ( self, tweet_id, author_id, images_urls, hashtags ) :
        tweet = Pyro_GOT3_Tweet( tweet_id, author_id, images_urls, hashtags )
        uri = self._root.register_obj( tweet, None )
        
        Pyro4.Proxy( self._GetOldTweets3_tweets_queue ).put( uri )
    
    def GetOldTweets3_tweets_queue_get ( self, block = True ) :
        uri = Pyro4.Proxy( self._GetOldTweets3_tweets_queue ).get( block = block )
        
        return Pyro4.Proxy( uri )
