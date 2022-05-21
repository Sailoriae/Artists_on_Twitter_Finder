#!/usr/bin/python3
# coding: utf-8

import snscrape.modules.twitter

# Vérifier que SNSCrape est à une version supérieure à la 0.4.0
from snscrape.version import __version__
from pkg_resources import parse_version as version
if version( __version__ ) < version( "0.4.0" ) :
    raise ModuleNotFoundError( "La version de la librairie SNScrape doit être supérieure à la 0.4.0 !" )


"""
Modifier un peu SNSCrape pour qu'il fasse exactement ce qu'on veut.
SNScrape utilise l'API utilisée par l'UI web pour le moteur de recherche :
https://api.twitter.com/2/search/adaptive.json
"""
class TwitterSearchScraper ( snscrape.modules.twitter.TwitterSearchScraper ) :
    def __init__ ( self, *args, **kwargs ) :
        super().__init__(*args, **kwargs)
        
        self._output_function = None
    
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
    
    # Override : On n'utilise pas de guest_token
    def _ensure_guest_token ( self, url = None ) : pass
    def _unset_guest_token ( self ) : pass
    
    # Override : Comme SNScraper ne nous donne pas le JSON original des Tweets,
    # on remplace sa fonction pour le faire nous-même
    def _tweet_to_tweet ( self, tweet, obj ) :
        if self._output_function != None :
            self._output_function( tweet )
        
        # On appel quand même sa fonction et on retourne ce qu'elle doit
        # normalement retourner
        return super()._tweet_to_tweet( tweet, obj )
    
    # Setter de la fonction d'output pour l'override juste ci-dessus
    def set_output_function ( self, output_function ) :
        self._output_function = output_function
    
    # Override : "This request requires a matching csrf cookie and header."
    def _check_api_response ( self, r ) :
        # Toujours synchroniser le header "x-csrf-token avec le cookie "ct0"
        # L'objet "_session" est MàJ automatiquement à chaque requête, en
        # fonction des headers de réponse "set-cookie"
        self._apiHeaders['x-csrf-token'] = self._session.cookies['ct0']
        
        return super()._check_api_response( r )


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
        scraper = TwitterSearchScraper( query, retries = 10 )
        # Peut réessayer 10 fois, car il fait des attentes exponentielles
        # La somme de toutes ces attentes sera donc la suivante (en secondes):
        # 2**0 + 2**1 + 2**2 + 2**3 + 2**4 + 2**5 + 2**6 + 2**7 + 2**8 + 2**9
        # Ce qui fait 17 minutes > 15 minutes pour se débloquer d'une HTTP 429
        # Et on passe 10 en argument car il faut qu'il fasse un dernier essai
        # après l'attente 2**9
        
        # Passer le token d'authentification
        scraper.set_auth_token( self.auth_token )
        
        # Donner la fonction d'output
        scraper.set_output_function( output_function )
        
        # Lancer la recherche / Obtenir les Tweets
        # Sont dans l'ordre chronologique, car SNScrape met le paramètre
        # "tweet_search_mode" à "live" (Onglet "Récent" sur l'UI web)
        count = 0
        first_tweet_date = None # Le premier Tweet est forcément le plus récent
        for tweet in scraper.get_items() :
            count += 1
            if first_tweet_date == None :
                first_tweet_date = tweet.date
        
        # Retourner
        return first_tweet_date, count
