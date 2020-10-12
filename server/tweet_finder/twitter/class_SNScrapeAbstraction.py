#!/usr/bin/python3
# coding: utf-8

"""
NOTE TRES IMPORTANTE
On n'utilise plus GetOldTweets3, car il ne fonctionne plus
SNScrape est son remplaçant
Il utilise l'API utilisée par l'UI web https://twitter.com/search
https://api.twitter.com/2/search/adaptive.json
"""
import snscrape.modules.twitter
import re


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
Couche d'abstraction à la librairie SNScrape.

Permet d'utiliser sur l'API de recherche de Twitter avec la librairie SNScrape.
Gère les limites de l'API Twitter et attend d'être débloqué en cas de bloquage.
"""
class SNScrapeAbstraction :
    def __init__ ( self, auth_token ) :
        self.auth_token = auth_token
    
    """
    Faire une recherche avec SNScrape sur l'API utilisée par l'UI web :
    https://twitter.com/search
    Cette API est la suivante :
    https://api.twitter.com/2/search/adaptive.json
    
    @param query Recherche à effectuer. Tous les Tweets retournés par cette
                 recherche seront retournés !
    @param output_function Fonction où mettre les JSON des Tweets.
    
    @return Un tuple contenant :
            - La date Tweet trouvé le plus récent,
            - Le nombre de Tweet trouvés.
    """
    def search( self, query : str, output_function = print ) :
        scraper = snscrape.modules.twitter.TwitterSearchScraper( query, retries = 10 )
        # Peut réessayer 10 fois, car il fait des attentes exponentielles
        # La somme de toutes ces attentes sera donc la suivante (en secondes):
        # 2**0 + 2**1 + 2**2 + 2**3 + 2**4 + 2**5 + 2**6 + 2**7 + 2**8 + 2**9
        # Ce qui fait 17 minutes > 15 minutes pour se débloquer d'une HTTP 429
        # Et on passe 10 en argument car il faut qu'il fasse un dernier essai
        # après l'attente 2**9
        
        
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
                self._apiHeaders["x-csrf-token"] = self._guestToken
                self._apiHeaders["x-twitter-auth-type"] = "OAuth2Session"
                return
            raise snscrape.base.ScraperException('Unable to find ct0 token')
        scraper._ensure_guest_token = ensure_guest_token
        
        # Hack : Pour que celui ci-dessus fonctionne lors d'une 429
        def unset_guest_token ( self = scraper ) :
            self._guestToken = None
            del self._session.cookies['ct0']
            del self._apiHeaders['x-csrf-token']
            del self._apiHeaders["x-twitter-auth-type"]
        scraper._unset_guest_token = unset_guest_token
        
        # Deep-copy de la fonction tweet_to_tweet
        tweet_to_tweet_old = copy_func( scraper._tweet_to_tweet )
        
        # Hack : Comme SNScraper ne nous donne pas le JSON original des Tweets,
        # on remplace sa fonction pour le faire nous-même
        def tweet_to_tweet_new  ( tweet, obj ) :
            output_function( tweet )
            
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
        
        return first_tweet_date, count
