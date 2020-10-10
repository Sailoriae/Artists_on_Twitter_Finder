#!/usr/bin/python3
# coding: utf-8

from time import time

try :
    from database import SQLite_or_MySQL
    from twitter import TweepyAbstraction, SNScrapeAbstraction
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .database import SQLite_or_MySQL
    from .twitter import TweepyAbstraction, SNScrapeAbstraction

# Ajouter le répertoire parent au PATH pour pouvoir importer les paramètres
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))
import parameters as param


class Unfounded_Account_on_Lister_with_SearchAPI ( Exception ) :
    pass


"""
Classe permettant de lister les Tweets d'un compte Twitter avec l'API
de recherche de Twittern, via la librairie SNScrape.
"""
class Tweets_Lister_with_SearchAPI :
    def __init__( self, auth_token, DEBUG : bool = False, ENABLE_METRICS : bool = False ) :
        self.DEBUG = DEBUG
        self.ENABLE_METRICS = ENABLE_METRICS
        self.bdd = SQLite_or_MySQL()
        self.snscrape = SNScrapeAbstraction( auth_token )
        self.twitter = TweepyAbstraction( param.API_KEY,
                                         param.API_SECRET,
                                         param.OAUTH_TOKEN,
                                         param.OAUTH_TOKEN_SECRET )
    
    """
    Lister les Tweets du compte Twitter @account_name.
    Si le compte est déjà dans la base de données, cette fonction liste à
    partir de la date du Tweet indexé de ce compte le plus récent, stockée dans
    la base.
    
    @param queue_put Fonction à appeler pour mettre les Tweets trouvés.
                     Lorsque le listage sera terminé, "None" sera ajouté.
    @param account_id ID du compte, vérifié récemment !
    
    @return La date du Tweet le plus récent, à enregistrer dans la base lorsque
            l'indexation sera terminée.
            Ou None si aucun Tweet n'a jamais été trouvé (Donc enregistrement
            "NULL" pour ce compte dans la base de données si le compte était
            déjà dans la base.
    
    Peut émettre une exception "Unfounded_Account_on_Lister_with_TimelineAPI" si
    le compte est introuvable.
    """
    def list_searchAPI_tweets ( self, account_name, queue_put, account_id = None, add_step_A_time = None ) :
        if account_id == None :
            account_id = self.twitter.get_account_id( account_name )
        if account_id == None :
            print( "[List SearchAPI] Compte @" + account_name + " introuvable !" )
            raise Unfounded_Account_on_Lister_with_SearchAPI
        
        if self.DEBUG :
            print( "[List SearchAPI] Listage des Tweets de @" + account_name + "." )
        if self.DEBUG or self.ENABLE_METRICS :
            start = time()
        
        since_date = self.bdd.get_account_SearchAPI_last_tweet_date( account_id )
        
        
        # Fonction de converstion vers la fonction queue_put()
        # Permet de filtre les Tweets sans images, et de les formater pour la
        # fonction queue_put()
        def output_function ( tweet_json ) :
            # Si il y a le champs "retweeted_status" dans le JSON
            if "retweeted_status" in tweet_json : # Le Tweet est un RT
                print( "[List SearchAPI] RT trouvé ! La recherche a donc renvoyé un RT, c'est pas normal !" )
                return
            
            tweet_id = tweet_json['id_str'] # ID du Tweet
            user_id = tweet_json['user_id_str'] # ID de l'auteur du Tweet
            # Super méga important, ne pas prendre celui trouvé par la fonction
            # list_searchAPI_tweets() !!!
            # Permet en cas de problème de ne pas faire n'importe quoi dans la BDD
            
            images = [] # Liste des URLs des images dans ce Tweet
            try :
                for tweet_media in tweet_json["extended_entities"]["media"] :
                    if tweet_media["type"] == "photo" :
                        images.append( tweet_media["media_url_https"] )
            except KeyError : # Tweet sans média
                return # Sinon ça ne sert à rien
            
            hashtags = [] # Liste des hashtags dans ce Tweet
            try :
                for hashtag in tweet_json["entities"]["hashtags"] :
                    hashtags.append( "#" + hashtag["text"] )
            except KeyError :
                pass
            
            if len(images) > 0 : # Sinon ça ne sert à rien
                queue_put( tweet_id, user_id, images, hashtags )
        
        
        # Note : Plus besoin de faire de bidouille avec "filter:safe"
        # On met le "@" à cause de @KIYOSATO_0928 qui renvoyait des erreurs 400
        query = "from:@" + account_name + " filter:media"
        if since_date != None :
            query += " since:" + since_date
        
        # Lancer la recherche
        first_tweet_date, count = self.snscrape.search( query, output_function )
        
        
        if self.DEBUG or self.ENABLE_METRICS :
            print( "[List SearchAPI] Il a fallu", time() - start, "secondes pour lister", count, "Tweets de @" + account_name + "." )
            if add_step_A_time != None :
                if count > 0 :
                    add_step_A_time( (time() - start) / count )
        
        # Indiquer qu'on a fini le listage
        queue_put( None, None, None, None )
        
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
    engine = Tweets_Lister_with_SearchAPI( param.TWITTER_AUTH_TOKENS[0], DEBUG = True )
    engine.list_searchAPI_tweets( "rikatantan2nd", print )
