#!/usr/bin/python3
# coding: utf-8

import requests
from random import uniform
from time import sleep
import http
import urllib


# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendamment (Notamment pour des
# tests), il faut que son répertoire de travail soit ce même répertoire
if __name__ == "__main__" :
    from os.path import abspath as get_abspath
    from os.path import dirname as get_dirname
    from os import chdir as change_wdir
    from os import getcwd as get_wdir
    from sys import path
    change_wdir(get_dirname(get_abspath(__file__)))
    change_wdir( "../../.." )
    path.append(get_wdir())

import utils.constants as const


# Se faire passer pour un vrai navigateur, hyper important pour Pixiv !
headers = {
    "User-Agent" : const.USER_AGENT
}


"""
Faire un GET HTTP en réessant de manière bourrin si jamais on a une erreur,
comme par exemple une rate limit.
Peut retourner des codes différents de HTTP 200 (Par exemple des 404 ou 403),
car utilise le module "requests", et non "urllib".
@param retry_on_those_http_errors Liste d'erreurs HTTP sur lesquelles on
                                  réessaye.
"""
def get_with_rate_limits ( url, max_retry = 5, retry_on_those_http_errors = [] ):
    retry_count = 0
    while True : # Solution très bourrin pour gèrer les rate limits
        try :
            to_return = requests.get( url, headers = headers, timeout = 60 )
            if to_return.status_code in retry_on_those_http_errors :
                print( f"[get_with_rate_limits] Erreur {to_return.status_code} pour : {url}" )
                retry_count += 1
                if retry_count > max_retry :
                    raise Exception( f"Nombre maximal de tentatives pour un ré-essai sur une erreur HTTP (Ici, erreur {to_return.status_code})" ) # Doit tomber dans le collecteur d'erreurs
                sleep( uniform( 30, 60 ) )
            else :
                return to_return
        
        except http.client.RemoteDisconnected as error :
            print( f"{type(error).__name__}: {error}" )
            retry_count += 1
            if retry_count > max_retry :
                raise error # Sera récupérée par le collecteur d'erreurs
            sleep( uniform( 5, 15 ) )
        
        except urllib.error.HTTPError as error : # Je ne sais plus si c'est cette erreur peut tomber
            if error.code == 404 : # N'arrive pas en fait, la lib laisse passer les erreurs 404
                print( f"{type(error).__name__}: {error}" )
                raise error # On peut raise tout de suite car 404
            else :
                print( f"{type(error).__name__}: {error}" )
                retry_count += 1
                if retry_count > max_retry :
                    raise error # Sera récupérée par le collecteur d'erreurs
                sleep( uniform( 5, 15 ) )
        
        except Exception as error :
            print( f"{type(error).__name__}: {error}" )
            retry_count += 2
            if retry_count > max_retry :
                raise error # Sera récupérée par le collecteur d'erreurs
            sleep( uniform( 5, 15 ) )
