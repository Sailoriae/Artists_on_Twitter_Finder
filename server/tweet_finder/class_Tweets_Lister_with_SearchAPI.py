#!/usr/bin/python3
# coding: utf-8

from time import time

"""
NOTE TRES IMPORTANTE
On n'utilise plus GetOldTweets3, car il ne fonctionne plus
SNScrape est son remplaçant
Il utilise l'API utilisée par l'UI web https://twitter.com/search
https://api.twitter.com/2/search/adaptive.json
"""
import snscrape.modules.twitter
import re

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


class Unfounded_Account_on_Lister_with_SearchAPI ( Exception ) :
    pass


"""
Faire un deep-copy d'une fonction Python.
Source : https://stackoverflow.com/a/6528148
"""
import types
import functools
def copy_func(f):
    g = types.FunctionType(f.__code__, f.__globals__, name=f.__name__,
                           argdefs=f.__defaults__,
                           closure=f.__closure__)
    g = functools.update_wrapper(g, f)
    g.__kwdefaults__ = f.__kwdefaults__
    return g


"""
Classe permettant de lister les Tweets d'un compte Twitter avec l'API
de recherche de Twittern, via la librairie SNScrape.
"""
class Tweets_Lister_with_SearchAPI :
    def __init__( self, auth_token, DEBUG : bool = False, ENABLE_METRICS : bool = False ) :
        self.DEBUG = DEBUG
        self.ENABLE_METRICS = ENABLE_METRICS
        self.bdd = SQLite_or_MySQL()
        self.auth_token = auth_token
        self.twitter = TweepyAbtraction( param.API_KEY,
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
    
    @return La date du Tweet le plus récent, à enregistrer dans la base lorsque
            l'indexation sera terminée.
            Ou None si aucun Tweet n'a jamais été trouvé (Donc enregistrement
            "NULL" pour ce compte dans la base de données si le compte était
            déjà dans la base.
    
    Peut émettre une exception "Unfounded_Account_on_Lister_with_TimelineAPI" si
    le compte est introuvable.
    """
    def list_searchAPI_tweets ( self, account_name, queue_put, add_step_A_time = None ) :
        account_id = self.twitter.get_account_id( account_name )
        if account_id == None :
            print( "[List SearchAPI] Compte @" + account_name + " introuvable !" )
            raise Unfounded_Account_on_Lister_with_SearchAPI
        
        if self.DEBUG :
            print( "[List SearchAPI] Listage des Tweets de @" + account_name + "." )
        if self.DEBUG or self.ENABLE_METRICS :
            start = time()
        
        since_date = self.bdd.get_account_SearchAPI_last_tweet_date( account_id )
        
        
        # Note : Plus besoin de faire de bidouille avec "filter:safe"
        query = "from:" + account_name + " filter:media"
        if since_date != None :
            query += " since:" + since_date
        scraper = snscrape.modules.twitter.TwitterSearchScraper( query )
        
        
        # ====================================================================
        # MODIFIER SNSCRAPER POUR QU'IL PUISSE FAIRE EXACTEMENT CE QU'ON VEUT
        # ====================================================================
        
        # Hack : Donner en douce à SNScraper des tokens pour s'authentifier
        # comme le serait un utilisateur sur l'UI web
        # Permet de recevoir les Tweets marqués sensibles
        scraper._session.cookies.set("auth_token", 
                                     self.auth_token,
                                     domain = '.twitter.com',
                                     path = '/',
                                     secure = True,
                                     expires = None)
        
        # Hack : Remplacer l'obtention du guest token pour l'obtention du token
        # ct0, qui chante tout le temps
        def ensure_guest_token ( self = scraper, url = None ) :
            if self._guestToken is not None:
                return
            r = self._get(self._baseUrl if url is None else url, headers = {'User-Agent': self._userAgent})
            match = re.search(r'document\.cookie = decodeURIComponent\("ct0=(\d+); Max-Age=10800; Domain=\.twitter\.com; Path=/; Secure"\);', r.text)
            if match:
                self._guestToken = match.group(1)
            if 'ct0' in r.cookies:
                self._guestToken = r.cookies['ct0']
            if self._guestToken:
                self._session.cookies.set('ct0', self._guestToken, domain = '.twitter.com', path = '/', secure = True, expires = None)
                self._apiHeaders['x-csrf-token'] = self._guestToken
                self._apiHeaders["x-twitter-auth-type"] = "OAuth2Session"
                return
            raise snscrape.base.ScraperException('Unable to find ct0 token')
        scraper._ensure_guest_token = ensure_guest_token
        
        # Deep-copy de la fonction tweet_to_tweet
        tweet_to_tweet_old = copy_func( scraper._tweet_to_tweet )
        
        # Hack : Comme SNScraper ne récupére pas les URL des images et les
        # hashtags des Tweets, on remplace sa fonction pour le faire nous-même
        def tweet_to_tweet_new  ( tweet, obj ) :
            tweet_id = tweet['id_str'] # ID du Tweet
            
            images = [] # Liste des URLs des images dans ce Tweet
            try :
                for tweet_media in tweet["extended_entities"]["media"] :
                    if tweet_media["type"] == "photo" :
                        images.append( tweet_media["media_url_https"] )
            except KeyError : # Tweet sans média
                pass
            
            hashtags = [] # Liste des hashtags dans ce Tweet
            try :
                for hashtag in tweet["entities"]["hashtags"] :
                    hashtags.append( "#" + hashtag["text"] )
            except KeyError :
                pass
            
            if len(images) > 0 : # Sinon ça ne sert à rien
                queue_put( tweet_id, account_id, images, hashtags )
            
            # On appel quand même sa fonction et on retourne ce qu'elle doit
            # normalement retourner
            return tweet_to_tweet_old( scraper, tweet, obj )
        
        scraper._tweet_to_tweet = tweet_to_tweet_new
        
        
        # ====================================================================
        # LANCER LA RECHERCHE ET RETOURNER
        # ====================================================================
        
        # Obtenir les Tweets
        count = 0
        first_tweet_date = None # Le premier Tweet est forcément le plus récent
        for tweet in scraper.get_items() :
            count += 1
            if first_tweet_date == None :
                first_tweet_date = tweet.date
        
        
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
