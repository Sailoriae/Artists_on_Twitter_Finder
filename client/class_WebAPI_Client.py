#!/usr/bin/python3
# coding: utf-8

import requests
from time import sleep


class Server_Connection_Not_Initialised ( Exception ) :
    def __init__ ( self ) :
        self.message = "La connexion au serveur n'a pas été initialisée correctement."
        super().__init__( self.message )

class Max_Pending_Requests_On_Server ( Exception ) :
    def __init__ ( self ) :
        self.message = "Nombre maximum de requêtes en cours de traitement atteint sur ce serveur pour cet adresse IP."
        super().__init__( self.message )


"""
Classe de client à un serveur "Artist_on_Twitter_Finder". Permet d'utiliser
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
        
        # Test de contact avec le serveur
        try :
            response = requests.get( base_api_address )
        except Exception :
            print( "Impossible de contacter le serveur !" )
            self.ready = False
            return
        
        try :
            json = response.json()
        except Exception :
            print( "Ce serveur ne renvoit pas de JSON.")
            self.ready = False
            return
        
        try :
            if json[ "error" ] != "NO_URL_FIELD" :
                print( "Ceci n'est pas un serveur \"Artist on Twitter Finder\".")
                self.ready = False
                return
        except ( KeyError, TypeError ) :
            print( "Ceci n'est pas un serveur \"Artist on Twitter Finder\".")
            self.ready = False
            return
        
        print( "Connexion réussie !" )
        self.ready = True
    
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
        try :
            while True :
                response = requests.get( self.base_api_address + "?url=" + illust_url )
                if response.status_code == 429 :
                    sleep(1)
                else :
                    response = response.json()
                    if response["error"] == "YOUR_IP_HAS_MAX_PENDING_REQUESTS" :
                        to_raise = Max_Pending_Requests_On_Server
                        break
                    else :
                        return response
        except Exception as error :
            print(error)
            print( "Problème de connexion avec le serveur." )
            return None
        
        raise to_raise
    
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
    def get_twitter_accounts ( self, illust_url : str, timeout = 300 ) :
        sleep_count = 0
        while True :
            response = self.get_request( illust_url )
            if response == None :
                return None
            if response["error"] != "" :
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
    def get_tweets ( self, illust_url : str, timeout = 3600 ) :
        sleep_count = 0
        while True :
            response = self.get_request( illust_url )
            if response == None :
                return None
            if response["error"] != "" :
                print( "Erreur : " + response["error"] )
                return None
            if response["status"] == "END" :
                return response["results"]
            sleep( 5 )
            sleep_count += 1
            if sleep_count * 5 > timeout :
                return None
