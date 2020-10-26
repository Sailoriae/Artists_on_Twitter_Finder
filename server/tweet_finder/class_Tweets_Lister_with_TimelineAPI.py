#!/usr/bin/python3
# coding: utf-8

from time import time

try :
    from database import SQLite_or_MySQL
    from twitter import TweepyAbstraction
    from analyse_tweet_json import analyse_tweet_json
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .database import SQLite_or_MySQL
    from .twitter import TweepyAbstraction
    from .analyse_tweet_json import analyse_tweet_json


class Unfounded_Account_on_Lister_with_TimelineAPI ( Exception ) :
    pass
class Blocked_by_User_with_TimelineAPI ( Exception ) :
    pass


"""
Classe permettant de lister les Tweets d'un compte Twitter avec l'API
de timeline de Twitter, via la librairie Tweepy.
"""
class Tweets_Lister_with_TimelineAPI :
    def __init__( self, api_key, api_secret, oauth_token, oauth_token_secret,
                        DEBUG : bool = False, ENABLE_METRICS : bool = False ) :
        self.DEBUG = DEBUG
        self.ENABLE_METRICS = ENABLE_METRICS
        self.bdd = SQLite_or_MySQL()
        self.twitter = TweepyAbstraction( api_key,
                                          api_secret,
                                          oauth_token,
                                          oauth_token_secret )
    
    """
    Lister les Tweets du compte Twitter @account_name.
    Si le compte est déjà dans la base de données, cette fonction liste à
    partir de l'ID du Tweet indexé de ce compte le plus récent, stocké dans la
    base.
    
    Seuls les tweets avec des image(s) seront ajoutés dans la file queue, sous
    la forme d'un dictionnaire.
    Plus d'informations sur ce dictionnaire dans la fonction suivante :
    fonction analyse_tweet_json()
    On ne met pas le JSON complet renvoyé par l'API afin de gagner de la
    mémoire vive.
    
    Cette méthode utlise l'API de timeline, limitée aux 3200 premiers Tweets du
    compte, retweets compris !
    
    @param queue Objet queue.Queue() pour y stocker les Tweets trouvés.
                 Un Tweet est représenté par le dictionnaire retourné par la
                 fonction analyse_tweet_json().
                 Lorsque le listage sera terminé, "None" sera ajouté.
    @param account_id ID du compte, vérifié récemment !
    
    @return L'ID du Tweet le plus récent, à enregistrer dans la base lorsque
            l'indexation sera terminée.
            Ou None si aucun Tweet n'a jamais été trouvé (Donc enregistrement
            "NULL" pour ce compte dans la base de données si le compte était
            déjà dans la base.
    
    Peut émettre une exception "Unfounded_Account_on_Lister_with_TimelineAPI" si
    le compte est introuvable.
    Peut émettre des "Blocked_by_User_with_TimelineAPI" si le compte nous
    bloque.
    """
    def list_TimelineAPI_tweets ( self, account_name, queue, account_id = None, add_step_B_time = None ) :
        if account_id == None :
            account_id = self.twitter.get_account_id( account_name ) # TOUJOURS AVEC CETTE API
        if account_id == None :
            print( "[List TimelineAPI] Compte @" + account_name + " introuvable !" )
            raise Unfounded_Account_on_Lister_with_TimelineAPI
        
        if self.twitter.blocks_me( account_id ) :
            print( "[List TimelineAPI] Le compte @" + account_name + " nous bloque, impossible de le scanner !" )
            raise Blocked_by_User_with_TimelineAPI
        
        if self.DEBUG :
            print( "[List TimelineAPI] Listage des Tweets de @" + account_name + "." )
        if self.DEBUG or self.ENABLE_METRICS :
            start = time()
        
        since_tweet_id = self.bdd.get_account_TimelineAPI_last_tweet_id( account_id )
        last_tweet_id = None
        count = 0
        
        # Lister tous les Tweets depuis celui enregistré dans la base
        for tweet in self.twitter.get_account_tweets( account_id, since_tweet_id ) :
            # Le premier tweet est forcément le plus récent
            if last_tweet_id == None :
                last_tweet_id = tweet.id
            
            tweet_dict = analyse_tweet_json( tweet._json )
            if tweet_dict != None :
                queue.put( tweet_dict )
            count += 1
        
        if self.DEBUG or self.ENABLE_METRICS :
            print( "[List TimelineAPI] Il a fallu", time() - start, "secondes pour lister", count, "Tweets de @" + account_name + "." )
            if add_step_B_time != None :
                if count > 0 :
                    add_step_B_time( (time() - start) / count )
        
        # Indiquer qu'on a fini le listage
        queue.put( None )
        
        # Retourner l'ID du Tweet trouvé le plus récent, ou celui enregistré
        # dans la base de données si aucun Tweet n'a été trouvé
        # La BDD peut retourner None si elle ne connait pas le Tweet (Donc aucun
        # Tweet n'est enregistré pour ce compte), c'est pas grave
        if last_tweet_id == None :
            return self.bdd.get_account_TimelineAPI_last_tweet_id( account_id )
        else :
            return last_tweet_id


"""
Test du bon fonctionnement de cette classe
"""
if __name__ == '__main__' :
    # Ajouter le répertoire parent au PATH pour pouvoir importer les paramètres
    from sys import path as sys_path
    from os import path as os_path
    sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))
    import parameters as param
    
    class Test :
        def put( tweet ) : print( tweet )
    test = Test()
    
    engine = Tweets_Lister_with_TimelineAPI( param.API_KEY,
                                             param.API_SECRET,
                                             param.TWITTER_API_KEYS[0]["OAUTH_TOKEN"],
                                             param.TWITTER_API_KEYS[0]["OAUTH_TOKEN_SECRET"],
                                             DEBUG = True )
    engine.list_searchAPI_tweets( "rikatantan2nd", test )
