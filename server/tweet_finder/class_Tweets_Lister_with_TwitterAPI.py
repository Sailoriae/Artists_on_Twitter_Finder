#!/usr/bin/python3
# coding: utf-8

from time import time

try :
    from database import SQLite_or_MySQL
    from twitter import TweepyAbtraction
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .database import SQLite_or_MySQL
    from .twitter import TweepyAbtraction

# Ajouter le répertoire parent au PATH pour pouvoir importer les paramètres
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))
import parameters as param


"""
Classe permettant de lister les Tweets d'un compte Twitter avec l'API publique
de Twitter via la librairie Tweepy.
"""
class Tweets_Lister_with_TwitterAPI :
    def __init__( self, DEBUG : bool = False ) :
        self.DEBUG = DEBUG
        self.bdd = SQLite_or_MySQL()
        self.twitter = TweepyAbtraction( param.API_KEY,
                                         param.API_SECRET,
                                         param.OAUTH_TOKEN,
                                         param.OAUTH_TOKEN_SECRET )
    
    """
    Lister les Tweets du compte Twitter @account_name.
    Si le compte est déjà dans la base de données, cette fonction liste à
    partir de l'ID du Tweet indexé de ce compte le plus récent, stocké dans la
    base.
    
    @param queue Objet queue.Queue() pour y stocker les Tweets trouvés.
                 Un Tweet est représenté par un objet "Tweepy.Status".
                 Lorsque le listage sera terminé, "None" sera ajouté.
    
    @return L'ID du Tweet le plus récent, à enregistrer dans la base lorsque
            l'indexation sera terminée.
            Ou None si le compte est introuvable.
    """
    def list_TwitterAPI_tweets ( self, account_name, queue ) :
        account_id = self.twitter.get_account_id( account_name )
        if account_id == None :
            print( "[List TwiAPI] Compte @" + account_name + " introuvable !" )
            return None
        
        if self.DEBUG :
            print( "[List TwiAPI] Listage des Tweets de @" + account_name + "." )
            start = time()
        
        since_tweet_id = self.bdd.get_account_last_scan_with_TwitterAPI( account_id )
        last_tweet_id = None
        count = 0
        
        # Lister tous les Tweets depuis celui enregistré dans la base
        for tweet in self.twitter.get_account_tweets( account_id, since_tweet_id ) :
            # Le premier tweet est forcément le plus récent
            if last_tweet_id == None :
                last_tweet_id = tweet.id
            
            queue.put( tweet )
        
        if self.DEBUG :
            print( "[List TwitterAPI] Il a fallu", time() - start, "secondes pour lister", count, "Tweets de @" + account_name + "." )
        
        # Indiquer qu'on a fini le listage
        queue.put( None )
        
        # Retourner l'ID du Tweet trouvé le plus récent, ou celui enregistré
        # dans la base de données si aucun Tweet n'a été trouvé
        if last_tweet_id == None :
            return self.bdd.get_account_last_scan_with_TwitterAPI( account_id )
        else :
            return last_tweet_id
