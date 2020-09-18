#!/usr/bin/python3
# coding: utf-8

import requests
from time import sleep
from json import JSONDecodeError


class Error_During_Server_Connection_Init ( Exception ) :
    pass

class Server_Connection_Not_Initialised ( Exception ) :
    def __init__ ( self ) :
        self.message = "La connexion au serveur n'a pas été initialisée correctement."
        super().__init__( self.message )

class Max_Pending_Requests_On_Server ( Exception ) :
    def __init__ ( self ) :
        self.message = "Nombre maximum de requêtes en cours de traitement atteint sur ce serveur pour cet adresse IP."
        super().__init__( self.message )


"""
Classe de client à un serveur "Artists on Twitter Finder". Permet d'utiliser
son API.
"""
class WebAPI_Client :
    """
    @param base_api_address Addresse de base de l'API du serveur à utiliser,
                            avec un "/" au bout ! Par exemple :
                            https://sub.domain.tld/api/
    """
    def __init__ ( self, 
                   base_api_address : str = "http://localhost:3301/" ) :
        self.base_api_address = base_api_address
        self.ready = True # Car on utilise get_request() pour gérer les 429
        
        # Test de contact avec le serveur
        try :
            response_json = self.get_request( "" )
        except JSONDecodeError :
            print( "Ce serveur ne renvoit pas de JSON." )
            self.ready = False
            raise Error_During_Server_Connection_Init( "Ce serveur ne renvoit pas de JSON." )
        except Exception :
            print( "Impossible de contacter le serveur !" )
            self.ready = False
            raise Error_During_Server_Connection_Init( "Impossible de contacter le serveur !" )
        
        try :
            if response_json[ "error" ] != "NO_URL_FIELD" :
                print( "Ceci n'est pas un serveur \"Artists on Twitter Finder\"." )
                self.ready = False
                raise Error_During_Server_Connection_Init( "Ceci n'est pas un serveur \"Artists on Twitter Finder\"." )
        except ( KeyError, TypeError ) :
            print( "Ceci n'est pas un serveur \"Artists on Twitter Finder\"." )
            self.ready = False
            raise Error_During_Server_Connection_Init( "Ceci n'est pas un serveur \"Artists on Twitter Finder\"." )
        
        print( "Connexion réussie !" )
    
    """
    Obtenir le résultat JSON d'un appel sur l'API.
    @param illust_url URL d'une illustration sur l'un des sites supportés par
                      le serveur.
    @return Le JSON renvoyé par l'API. Voir la documentation pour plus
            d'information sur son contenu. Un JSON s'utilise comme un
            dictionnaire Python. Voir la documentation de l'API HTTP pour
            plus d'informations sur le contenu de ce JSON.
            Ou None si il y a un problème de connexion.
    """
    def get_request ( self, illust_url : str ) -> dict :
        if not self.ready :
            print( "La connexion au serveur n'a pas été initialisée correctement." )
            raise Server_Connection_Not_Initialised
        while True :
            response = requests.get( self.base_api_address + "query?url=" + illust_url )
            if response.status_code == 429 :
                sleep(1)
            else :
                response = response.json()
                if response["error"] == "YOUR_IP_HAS_MAX_PENDING_REQUESTS" :
                    raise Max_Pending_Requests_On_Server
                    break
                else :
                    return response
    
    """
    Obtenir la liste des comptes Twitter de l'artiste de cette illustration
    trouvés par le serveur.
    @param illust_url URL d'une illustration sur l'un des sites supportés par
                      le serveur.
    @param timeout En seconde, le temps de traitement maximal du serveur.
                   (OPTIONNEL)
    @return Liste de dictionnaires :
            - "account_name" : Nom du compte Twitter,
            - "account_id" : L'ID du compte Twitter.
            OU une liste vide si l'artiste n'a pas de compte Twitter.
            OU None s'il y a eu un problème, ou que le temps "timeout" s'est
            écoulé.
    """
    def get_twitter_accounts ( self, illust_url : str, timeout : int = 300 ) :
        sleep_count = 0
        while True :
            response = self.get_request( illust_url )
            if response == None :
                return None
            if response["error"] != None :
                print( "Erreur : " + response["error"] )
                return None
            if response["status"] != "WAIT_LINK_FINDER" and response["status"] != "LINK_FINDER" :
                return response["twitter_accounts"]
            sleep( 5 )
            sleep_count += 1
            if sleep_count * 5 > timeout :
                return None
    
    """
    Obtenir la liste des Tweets de l'artiste de cette illustration trouvés par
    le serveur.
    @param illust_url URL d'une illustration sur l'un des sites supportés par
                      le serveur.
    @param timeout En seconde, le temps de traitement maximal du serveur.
                   (OPTIONNEL)
    @return Liste de dictionnaires :
            - "tweet_id" : L'ID du Tweet.
            - "account_id": L'ID du compte Twitter.
            - "image_position" : La position de l'image dans le tweet, entre 1 et 4.
            - "distance" : La distance calculée entre l'image de requête et cette image.
            OU une liste vide si l'artiste n'a pas de compte Twitter ou
            l'artiste n'a pas de compte Twitter.
            OU None s'il y a eu un problème, ou que le temps "timeout" s'est
            écoulé.
    """
    def get_tweets ( self, illust_url : str, timeout : int = 3600 ) :
        sleep_count = 0
        while True :
            response = self.get_request( illust_url )
            if response == None :
                return None
            if response["error"] != None :
                print( "Erreur : " + response["error"] )
                return None
            if response["status"] == "END" :
                return response["results"]
            sleep( 5 )
            sleep_count += 1
            if sleep_count * 5 > timeout :
                return None
