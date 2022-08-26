#!/usr/bin/python3
# coding: utf-8

import requests
from time import sleep, time
from json import JSONDecodeError


class Error_During_Server_Connection_Init ( Exception ) :
    pass

class Server_Connection_Not_Initialised ( Exception ) :
    def __init__ ( self ) :
        self.message = "La connexion au serveur n'a pas été initialisée correctement."
        super().__init__( self.message )

class Max_Processing_Requests_On_Server ( Exception ) :
    def __init__ ( self ) :
        self.message = "Nombre maximum de requêtes en cours de traitement atteint sur ce serveur pour cet adresse IP."
        super().__init__( self.message )

class Timeout_Reached ( Exception ) :
    def __init__ ( self, timeout ) :
        self.message = "Timeout de " + str(timeout) + " secondes atteint."
        super().__init__( self.message )


# Temps entre chaque requêtes, imposé par le serveur AOTF.
RATE_LIMIT_PERIOD = 1 # En secondes


"""
Classe de client à un serveur "Artists on Twitter Finder". Permet d'utiliser
son API.
"""
class AOTF_Client :
    """
    @param base_api_address Addresse de base de l'API du serveur à utiliser,
                            avec un "/" au bout ! Par exemple :
                            https://sub.domain.tld/api/
    @param ignore_check Sauter l'étape de vérification de la connexion au
                        serveur AOTF. Peut être mis sur True une fois le
                        débug du programme terminé.
    """
    def __init__ ( self,
                   base_api_address : str = "http://localhost:3301/",
                   ignore_check : bool = False ) :
        self._base_api_address : str = base_api_address
        self._ready : bool = True # Car on utilise get_request() pour gérer les 429
        self._cached_response : dict = None # Mise en cache de la réponse (Si fin de traitement), afin d'éviter une requête de plus
        self._cached_response_input_url : str = None # URL de requête correspondant à la réponse mise en cache
        self._last_request_timestamp : float = 0 # Timestamp de la dernière requête (Permet d'éviter les 429)
        
        # Test de contact avec le serveur
        if ignore_check : return
        
        try :
            response_json = self.get_request( "" )
        except JSONDecodeError :
            print( "Ce serveur ne renvoit pas de JSON." )
            self._ready = False
            raise Error_During_Server_Connection_Init( "Ce serveur ne renvoit pas de JSON." )
        except Exception :
            print( "Impossible de contacter le serveur !" )
            self._ready = False
            raise Error_During_Server_Connection_Init( "Impossible de contacter le serveur !" )
        
        try :
            if response_json[ "error" ] != "NO_URL_FIELD" :
                print( "Ceci n'est pas un serveur \"Artists on Twitter Finder\"." )
                self._ready = False
                raise Error_During_Server_Connection_Init( "Ceci n'est pas un serveur \"Artists on Twitter Finder\"." )
        except ( KeyError, TypeError ) :
            print( "Ceci n'est pas un serveur \"Artists on Twitter Finder\"." )
            self._ready = False
            raise Error_During_Server_Connection_Init( "Ceci n'est pas un serveur \"Artists on Twitter Finder\"." )
        
        print( "Connexion à \"Artists on Twitter Finder\" réussie !" )
    
    """
    Obtenir le résultat JSON d'un appel sur l'API.
    @param illust_url URL d'une illustration sur l'un des sites supportés par
                      le serveur.
    @return Le JSON renvoyé par l'API. Un JSON s'utilise comme un dictionnaire
            Python. Voir la documentation de l'API HTTP d'AOTF pour plus
            d'informations sur le contenu de ce JSON.
    """
    def get_request ( self, illust_url : str ) -> dict :
        if not self._ready :
            print( "La connexion au serveur n'a pas été initialisée correctement." )
            raise Server_Connection_Not_Initialised
        if illust_url == self._cached_response_input_url :
            return self._cached_response
        while True :
            cooldown_time = RATE_LIMIT_PERIOD - time() + self._last_request_timestamp
            if cooldown_time > 0 :
                sleep( cooldown_time )
            response = requests.get( self._base_api_address + "query?url=" + illust_url )
            self._last_request_timestamp = time()
            if response.status_code == 429 : # Peut arriver si plusieurs exécutions en parallèle
                sleep( RATE_LIMIT_PERIOD )
            else :
                response = response.json()
                if response["error"] == "YOUR_IP_HAS_MAX_PROCESSING_REQUESTS" :
                    raise Max_Processing_Requests_On_Server
                    break
                else :
                    # Mettre en cache lorsque le traitement est terminé
                    if response["status"] == None or response["status"] == "END" :
                        self._cached_response = response
                        self._cached_response_input_url = illust_url
                    return response
    
    """
    Obtenir la liste des comptes Twitter de l'artiste de cette illustration
    trouvés par le serveur.
    @param illust_url URL d'une illustration sur l'un des sites supportés par
                      le serveur.
    @param timeout En seconde, le temps de traitement maximal du serveur.
                   Emet une erreur Timeout_Reached si atteint.
                   (OPTIONNEL)
    @return Liste de dictionnaires :
            - "account_name" : Nom du compte Twitter,
            - "account_id" : L'ID du compte Twitter.
            OU une liste vide si l'artiste n'a pas de compte Twitter.
            OU None s'il y a eu un problème sur le serveur AOTF.
    """
    def get_twitter_accounts ( self, illust_url : str, timeout : int = 300 ) :
        start = time()
        while True :
            response = self.get_request( illust_url )
            if response["error"] != None :
                print( "Erreur : " + response["error"] )
                # Si des comptes Twitter ont étés trouvés, on laisse la
                # fonction les retourner
                if response["twitter_accounts"] == [] :
                    return None
            if response["status"] != "WAIT_LINK_FINDER" and response["status"] != "LINK_FINDER" :
                return response["twitter_accounts"]
            sleep( 5 )
            if time() - start > timeout :
                raise Timeout_Reached( timeout )
    
    """
    Obtenir la liste des Tweets de l'artiste de cette illustration trouvés par
    le serveur.
    @param illust_url URL d'une illustration sur l'un des sites supportés par
                      le serveur.
    @param timeout En seconde, le temps de traitement maximal du serveur.
                   Emet une erreur Timeout_Reached si atteint.
                   (OPTIONNEL)
    @return Liste de dictionnaires :
            - "tweet_id" : L'ID du Tweet.
            - "account_id": L'ID du compte Twitter.
            - "image_position" : La position de l'image dans le tweet, entre 1 et 4.
            - "distance" : La distance calculée entre l'image de requête et cette image.
            OU une liste vide si l'artiste n'a pas de compte Twitter ou
            l'artiste n'a pas de compte Twitter.
            OU None s'il y a eu un problème sur le serveur AOTF.
    """
    def get_tweets ( self, illust_url : str, timeout : int = 3600 ) :
        start = time()
        while True :
            response = self.get_request( illust_url )
            if response["error"] != None :
                print( "Erreur : " + response["error"] )
                return None
            if response["status"] == "END" :
                return response["results"]
            sleep( 5 )
            if time() - start > timeout :
                raise Timeout_Reached( timeout )
