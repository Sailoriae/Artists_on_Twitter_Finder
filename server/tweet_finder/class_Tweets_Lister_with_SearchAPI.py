#!/usr/bin/python3
# coding: utf-8

from time import time

try :
    from database import SQLite_or_MySQL
    from twitter import TweepyAbstraction, SNScrapeAbstraction
    from analyse_tweet_json import analyse_tweet_json
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .database import SQLite_or_MySQL
    from .twitter import TweepyAbstraction, SNScrapeAbstraction
    from .analyse_tweet_json import analyse_tweet_json


class Unfounded_Account_on_Lister_with_SearchAPI ( Exception ) :
    pass
class Blocked_by_User_with_SearchAPI ( Exception ) :
    pass


"""
Classe permettant de lister les Tweets d'un compte Twitter avec l'API
de recherche de Twitter, via la librairie SNScrape.
"""
class Tweets_Lister_with_SearchAPI :
    def __init__( self, api_key, api_secret, oauth_token, oauth_token_secret, auth_token,
                        DEBUG : bool = False, ENABLE_METRICS : bool = False ) :
        self.DEBUG = DEBUG
        self.ENABLE_METRICS = ENABLE_METRICS
        self.bdd = SQLite_or_MySQL()
        self.snscrape = SNScrapeAbstraction( auth_token )
        self.twitter = TweepyAbstraction( api_key,
                                          api_secret,
                                          oauth_token,
                                          oauth_token_secret )
    
    """
    Lister les Tweets du compte Twitter @account_name.
    Si le compte est déjà dans la base de données, cette fonction liste à
    partir de la date du Tweet indexé de ce compte le plus récent, stockée dans
    la base.
    
    Seuls les tweets avec des image(s) seront ajoutés dans la file queue, sous
    la forme d'un dictionnaire.
    Plus d'informations sur ce dictionnaire dans la fonction suivante :
    fonction analyse_tweet_json()
    On ne met pas le JSON complet renvoyé par l'API afin de gagner de la
    mémoire vive.
    
    @param queue Objet queue.Queue() pour y stocker les Tweets trouvés.
                 Un Tweet est représenté par le dictionnaire retourné par la
                 fonction analyse_tweet_json().
    @param account_id ID du compte, vérifié récemment !
    
    @return La date du Tweet le plus récent, à enregistrer dans la base lorsque
            l'indexation sera terminée.
            Ou None si aucun Tweet n'a jamais été trouvé (Donc enregistrement
            "NULL" pour ce compte dans la base de données si le compte était
            déjà dans la base.
    
    Peut émettre une exception "Unfounded_Account_on_Lister_with_TimelineAPI" si
    le compte est introuvable.
    Peut émettre des "Blocked_by_User_with_SearchAPI" si le compte nous bloque.
    """
    def list_searchAPI_tweets ( self, account_name, queue, account_id = None, add_step_A_time = None ) :
        if account_id == None :
            account_id = self.twitter.get_account_id( account_name ) # TOUJOURS AVEC CETTE API
        if account_id == None :
            print( f"[List SearchAPI] Compte @{account_name} introuvable !" )
            raise Unfounded_Account_on_Lister_with_SearchAPI
        
        if self.twitter.blocks_me( account_id ) :
            print( f"[List SearchAPI] Le compte @{account_name} nous bloque, impossible de le scanner !" )
            raise Blocked_by_User_with_SearchAPI
        
        if self.DEBUG :
            print( f"[List SearchAPI] Listage des Tweets de @{account_name}." )
        if self.DEBUG or self.ENABLE_METRICS :
            start = time()
        
        since_date = self.bdd.get_account_SearchAPI_last_tweet_date( account_id )
        
        
        # Fonction de converstion vers la fonction queue.put()
        # Permet de filtre les Tweets sans images, et de les formater pour la
        # fonction queue_put()
        def output_function ( tweet_json ) :
            tweet_dict = analyse_tweet_json( tweet_json )
            if tweet_dict != None :
                # Re-filtrer au cas où
                if int( tweet_dict["user_id"] ) == int ( account_id ) :
                    queue.put( tweet_dict )
        
        # Note : Plus besoin de faire de bidouille avec "filter:safe"
        # On met le "@" à cause de @KIYOSATO_0928 qui renvoyait des erreurs 400
        # Laisser "-filter:retweets", ça ne supprime pas les Tweets citant
        query = f"from:@{account_name} filter:media -filter:retweets"
        if since_date != None :
            query += " since:" + since_date
        
        # Lancer la recherche
        first_tweet_date, count = self.snscrape.search( query, output_function )
        
        
        if self.DEBUG or self.ENABLE_METRICS :
            print( f"[List SearchAPI] Il a fallu {time() - start} secondes pour lister {count} Tweets de @{account_name}." )
            if add_step_A_time != None :
                if count > 0 :
                    add_step_A_time( (time() - start) / count )
        
        # Indiquer qu'on a fini le listage
        queue.put( None )
        
        # Retourner la date du Tweet trouvé le plus récent, ou celui enregistré
        # dans la base de données si aucun Tweet n'a été trouvé
        # La BDD peut retourner None si elle ne connait pas le Tweet (Donc aucun
        # Tweet n'est enregistré pour ce compte), c'est pas grave
        if count > 0 :
            return first_tweet_date.strftime('%Y-%m-%d')
        else :
            return self.bdd.get_account_SearchAPI_last_tweet_date( account_id )


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
    
    engine = Tweets_Lister_with_SearchAPI( param.API_KEY,
                                           param.API_SECRET,
                                           param.TWITTER_API_KEYS[0]["OAUTH_TOKEN"],
                                           param.TWITTER_API_KEYS[0]["OAUTH_TOKEN_SECRET"],
                                           param.TWITTER_API_KEYS[0]["AUTH_TOKEN"],
                                           DEBUG = True )
    engine.list_searchAPI_tweets( "rikatantan2nd", test )
