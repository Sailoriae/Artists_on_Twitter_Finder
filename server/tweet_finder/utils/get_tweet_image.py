#!/usr/bin/python3
# coding: utf-8

import urllib
import http
from time import sleep

try :
    from url_to_content import url_to_content
except ModuleNotFoundError :
    from .url_to_content import url_to_content


# Note importante :
# On peut télécharger les images des tweets donnés par l'API de recherche en
# meilleure qualité.
# En effet, il y a 4 niveaux de qualité sur Twitter : "thumb", "small",
# "medium" et "large". Et par défaut, si rien n'est indiqué, le serveur nous
# envoie la qualité "medium". Si il n'y a pas de qualité "large", le serveur
# nous renvoie quand même quelque chose !
# Donc toujours prendre la meilleure qualité ! Tant pis pour la connexion et la
# RAM, mais cela permet de ne pas trop écarter les images à cause des
# compressions.


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
def get_tweet_image ( image_url : str ) -> bytes :
    retry_count = 0
    while True :
        try :
            # Télécharger l'image au format maximal !
            # Théoriquement, on a toujours le format d'URL suivant :
            # https://pbs.twimg.com/media/EgwU7JdUwAECztR.jpg
            if "?" in image_url : # Sécurité
                raise Exception( "URL d'image de Tweet problématique : " + image_url )
            large_image_url = image_url + "?name=large"
            return url_to_content( large_image_url )
        
        except urllib.error.HTTPError as error :
            print( "[get_tweet_image] Erreur avec l'image :", image_url )
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
            print( "[get_tweet_image] Erreur avec l'image :", image_url )
            print( error )
            
            if retry_count < 1 : # Essayer un coup d'attendre
                print( "[get_tweet_image] On essaye d'attendre 10 secondes..." )
                sleep( 10 )
                retry_count += 1
                continue
            
            print( "[get_tweet_image] Abandon !" )
            raise error
