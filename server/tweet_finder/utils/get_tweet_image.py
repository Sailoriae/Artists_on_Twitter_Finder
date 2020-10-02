#!/usr/bin/python3
# coding: utf-8

import urllib
import http
from time import sleep

try :
    from url_to_content import url_to_content
except ModuleNotFoundError :
    from .url_to_content import url_to_content


"""
GET HTTP UNIFIE POUR OBTENIR LES IMAGES DE TWEETS.
NE PASSER QUE PAR CETTE FONCTIION ! Car elle gère les erreurs HTTP dûes à la
perte d'images sur les serveurs de Twitter.
NE PAS UTILISER CETTE FONCTION POUR DES IMAGES NE VENANT PAS DE TWEETS !

Fonction url_to_content() adapté à une image d'un Tweet.
Obtenir le contenu d'une image d'un Tweet disponible à une URL.
Attention : Cette fonction retourne le contenu binaire !

@param image_url L'URL de l'image du Tweet.

@return L'image sous forme de bits, à décoder !
        Ou None si il y a eu une erreur connue comme insolvable !
"""
def get_tweet_image ( url : str ) -> bytes :
    retry_count = 0
    while True :
        try :
            return url_to_content( url )
        
        except urllib.error.HTTPError as error :
            print( "[get_tweet_image] Erreur avec l'image :", url )
            print( error )
            
            if error.code == 404 or error.code == 500 or error.code == 403 : # Erreurs insolvables
                return None
            
            else :
                if error.code == 502 : # Il suffit d'attendre pour ce genre d'erreurs
                    if retry_count < 3 : # Essayer d'attendre, au maximum 3 coups
                        print( "[get_tweet_image] On essaye d'attendre 10 secondes..." )
                        sleep( 10 )
                        retry_count += 1
                        continue
                
                elif retry_count < 1 : # Essayer un coup d'attendre
                    print( "[get_tweet_image] On essaye d'attendre 10 secondes..." )
                    sleep( 10 )
                    retry_count += 1
                    continue
                
                print( "[get_tweet_image] Abandon !" )
                raise error
        
        except http.client.IncompleteRead as error :
            print( "[get_tweet_image] Erreur avec l'image :", url )
            print( error )
            
            if retry_count < 1 : # Essayer un coup d'attendre
                print( "[get_tweet_image] On essaye d'attendre 10 secondes..." )
                sleep( 10 )
                retry_count += 1
                continue
            
            print( "[get_tweet_image] Abandon !" )
            raise error
