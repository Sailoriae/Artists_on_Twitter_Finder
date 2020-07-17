#!/usr/bin/python3
# coding: utf-8

import requests


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
    @return Le JSON renvoyé par l'API. Voir la documentation pour plus
            d'information sur son contenu. Un JSON s'utilise comme un
            dictionnaire Python. Voir la documentation de l'API HTTP pour
            plus d'informations sur le contenu de ce JSON.
            Ou None si il y a un problème de connexion.
    """
    def get_request ( self, illust_url : str ) -> dict :
        try :
            return requests.get( "http://localhost:3301/?url=" + illust_url ).json()
        except Exception :
            print( "Problème de connexion avec le serveur." )
