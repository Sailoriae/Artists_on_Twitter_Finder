#!/usr/bin/python3
# coding: utf-8

import snscrape.modules.twitter
from secrets import token_hex

# Vérifier que SNSCrape est à une version supérieure à la 0.4.0
from snscrape.version import __version__
from pkg_resources import parse_version as version
if version( __version__ ) < version( "0.4.0" ) :
    raise ModuleNotFoundError( "La version de la librairie SNScrape doit être supérieure à la 0.4.0 !" )

# Vérifier que SNScrape a les dernières fonctionnalités requises
try :
    from snscrape.modules.twitter import _TwitterAPIType
except ImportError :
    raise ModuleNotFoundError( "Merci de mettre à jour la librairie SNScrape !" )


"""
Modifier un peu SNSCrape pour qu'il fasse exactement ce qu'on veut.
SNScrape utilise l'API utilisée par l'UI web pour le moteur de recherche :
https://api.twitter.com/2/search/adaptive.json
"""
class TwitterAPIScraper ( snscrape.modules.twitter._TwitterAPIScraper ) :
    # Donner en douce à SNScraper le token pour s'authentifier comme le serait
    # un utilisateur sur l'UI web
    # Permet de recevoir les Tweets marqués sensibles
    def set_auth_token ( self, auth_token ) :
        self._session.cookies.set("auth_token",
                                  auth_token,
                                  domain = '.twitter.com',
                                  path = '/',
                                  secure = True,
                                  expires = None)
        
        # Pré-générer le CSRF-Token afin d'économiser une requête
        # C'est ce qu'ils font dans Gallery-DL
        # https://github.com/mikf/gallery-dl/blob/master/gallery_dl/extractor/twitter.py
        # Tester en mettant "retries" à 0, sans ce code on a une 403
        self._session.cookies.set("ct0",
                                  token_hex(16),
                                  domain = '.twitter.com',
                                  path = '/',
                                  secure = True,
                                  expires = None)
        self._apiHeaders['x-csrf-token'] = self._session.cookies['ct0']
    
    # Override : On n'utilise pas de guest_token
    def _ensure_guest_token ( self, url = None ) : pass
    def _unset_guest_token ( self ) : pass
    
    # Override : Comme SNScraper ne nous donne pas le JSON original des Tweets,
    # on l'insére en douce dans les objets Tweet qu'il retourne
    def _make_tweet ( self, *args, **kwargs ) :
        tweet = super()._make_tweet( *args, **kwargs )
        tweet._json = args[0]
        return tweet
    
    # Même chose, mais pour les versions antérieures à la 0.4.4 (Non-comprise)
    def _tweet_to_tweet ( self, tweet, obj ) :
        to_return = super()._tweet_to_tweet( tweet, obj )
        if not hasattr( to_return, "_json" ) :
            to_return._json = tweet
        return to_return
    
    # Override : "This request requires a matching csrf cookie and header."
    def _check_api_response ( self, r ) :
        # Toujours synchroniser le header "x-csrf-token avec le cookie "ct0"
        # L'objet "_session" est MàJ automatiquement à chaque requête, en
        # fonction des headers de réponse "set-cookie"
        self._apiHeaders['x-csrf-token'] = self._session.cookies['ct0']
        
        return super()._check_api_response( r )

# API de recherche
class TwitterSearchScraper ( TwitterAPIScraper, snscrape.modules.twitter.TwitterSearchScraper ) :
    pass

# API de timeline
class TwitterProfileScraper ( TwitterAPIScraper, snscrape.modules.twitter.TwitterProfileScraper ) :
    pass

class TwitterTweetScraper ( TwitterAPIScraper, snscrape.modules.twitter.TwitterTweetScraper ) :
    pass


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
    
    @return Un itérateur d'objets Tweet de la librairie SNScrape (Ils ont un
            attribut "_json" contenant ce que retourne l'API).
    """
    def search( self, query : str, RETRIES = 10 ) :
        scraper = TwitterSearchScraper( query, retries = RETRIES )
        # Peut réessayer 10 fois, car il fait des attentes exponentielles
        # La somme de toutes ces attentes sera donc la suivante (en secondes):
        # 2**0 + 2**1 + 2**2 + 2**3 + 2**4 + 2**5 + 2**6 + 2**7 + 2**8 + 2**9
        # Ce qui fait 17 minutes > 15 minutes pour se débloquer d'une HTTP 429
        # Et on passe 10 en argument car il faut qu'il fasse un dernier essai
        # après l'attente 2**9
        
        # Passer le token d'authentification
        scraper.set_auth_token( self.auth_token )
        
        # Lancer la recherche / Obtenir les Tweets
        # Sont dans l'ordre chronologique, car SNScrape met le paramètre
        # "tweet_search_mode" à "live" (Onglet "Récent" sur l'UI web)
        last_tweet_id = None
        for tweet in scraper.get_items() :
            # On vérifie que les IDs de Tweets soient décroissants
            if last_tweet_id != None and tweet.id > last_tweet_id :
                raise Exception( "Les IDs de Tweets sont censés être décroissants dans une recherche" ) # Doit tomber dans le collecteur d'erreurs
            last_tweet_id = tweet.id
            
            yield tweet
    
    """
    Obtenir les Tweets d'un compte avec SNScrape sur l'API utilisée par l'UI
    web. Cela ne débloque pas la limite des 3.200 Tweets, mais cela permet
    d'utiliser l'API v2 sans être limité par le "Tweet Cap".
    C'est une nouvelle limitation qui s'applique à l'application entière (Donc
    tous ses utilisateurs), et qui tuera les applications tierces comme Twidere
    le jour où ils arrêteront l'API v1.1 !
    
    @param account_id L'ID ou le nom du compte Twitter (SNScrape différencie en
                      fonction du type, int ou str, y faire attention).
    @param since_tweet_id ID du Tweet où s'arrêter (Les IDs de Tweets sont par
                          ordre décroissant lorsqu'on remonte un compte).
    
    @return Un itérateur d'objets Tweet de la librairie SNScrape (Ils ont un
            attribut "_json" contenant ce que retourne l'API).
    """
    def user_tweets( self, account_id : int, since_tweet_id : int = None, RETRIES = 10 ) :
        scraper = TwitterProfileScraper( account_id, retries = RETRIES )
        scraper.set_auth_token( self.auth_token )
        last_tweet_id = None
        first_tweet_passed = False
        for tweet in scraper.get_items() :
            # On vérifie que les IDs de Tweets soient décroissants
            # Le premier Tweet peut être le Tweet épinglé, on le passe
            if last_tweet_id != None and tweet.id > last_tweet_id :
                # Note : Les retweets ont des ID différents du tweet d'origine
                raise Exception( "Les IDs de Tweets sont censés être décroissants sur un compte" ) # Doit tomber dans le collecteur d'erreurs
            if first_tweet_passed : last_tweet_id = tweet.id
            
            # On retourne avant de décider de s'arrêter
            yield tweet
            
            # Les IDs de Tweets sont décroissants, donc si on est en dessous du
            # Tweet de départ, on peut arrêter (Au cas où il ait été supprimé)
            # Attention au premier Tweet qui peut être le Tweet épinglé !
            if first_tweet_passed and since_tweet_id and tweet.id <= since_tweet_id :
                break
            
            first_tweet_passed = True
    
    """
    Obtenir plusieurs Tweets.
    Attention : Très lent, et très rate-limité !
    
    @param tweet_id Liste d'ID de Tweets.
    
    @return Un itérateur d'objets Tweet de la librairie SNScrape (Ils ont un
            attribut "_json" contenant ce que retourne l'API).
    """
    def get_tweets( self, tweets_ids, RETRIES = 10 ) :
        for tweet_id in tweets_ids :
            scraper = TwitterTweetScraper( tweet_id, retries = RETRIES )
            scraper.set_auth_token( self.auth_token )
            for tweet in scraper.get_items() :
                yield tweet
