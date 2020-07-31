#!/usr/bin/python3
# coding: utf-8

from queue import Queue

# Ajouter le répertoire parent du répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

from tweet_finder import Common_Tweet_IDs_List


"""
Classe représentant une indexation (Nouvelle ou mise à jour) d'un ID de compte
Twitter dans la base de données. Cet objet est le même durant tout le processus
de traitement.

Une requête est identifiée par l'ID du compte Twitter.
"""
class Scan_Request :
    """
    @param account_id L'ID du compte Twitter à indexer / scanner. Ne sert qu'à
                      identifier.
    @param acount_name Le nom du compte Twitter à indexer / scanner. Attention,
                       c'est lui qui est revérifié et scanné !
    @param is_prioritary Est ce que cette requête est prioritaire ?
    """
    def __init__ ( self, account_id : int,
                         acount_name : str,
                         is_prioritary : bool = False ) :
        self.account_id = account_id
        self.account_name = acount_name
        self.is_prioritary = is_prioritary
        
        # Si jamais un thread de traitement a planté avec la requête, le
        # collecteur d'erreur l'indiquera ici
        self.has_failed = False
        
        # File d'attente pour mettre les Tweets trouvés par GetOldTweets3
        self.GetOldTweets3_tweets_queue = Queue()
        
        # Résultat de la fonction
        # Tweets_Lister_with_GetOldTweets3.list_GOT3_tweets() (Etape A)
        # Contient la date du Tweet trouvé par GOT3 le plus récent
        self.GetOldTweets3_last_tweet_date = None
        
        # File d'attente pour mettre les Tweets trouvés par Tweepy
        self.TwitterAPI_tweets_queue = Queue()
        
        # Résultat de la fonction
        # Tweets_Lister_with_TwitterAPI.list_TwitterAPI_tweets() (Etape B)
        # Contient l'ID du Tweet trouvé par l'API Twitter le plus récent
        self.TwitterAPI_last_tweet_id = None
        
        # Deux variables de début de traitement de la requête
        self.started_GOT3_listing = False
        self.started_TwitterAPI_listing = False
        
        # Cache pour les deux indexeurs (Etapes C et D)
        # Permet de savoir quand la requête a été vue pour la dernière fois,
        # afin de ne pas trop itérer dessus
        self.last_seen_GOT3_indexer = 0
        self.last_seen_TwitterAPI_indexer = 0
        
        # Cache pour les deux indexeurs (Etape C et D)
        # Permet de savoir si l'autre est en train ou a déjà traiter un Tweet,
        # sans avoir à faire un appel à la base de données
        self.indexing_tweets = Common_Tweet_IDs_List()
        
        # Deux variables de fin du traitement de la requête
        self.finished_GOT3_indexing = False
        self.finished_TwitterAPI_indexing = False
        
        # Date de fin de la procédure
        self.finished_date = None
