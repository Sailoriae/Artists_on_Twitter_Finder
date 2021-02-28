#!/usr/bin/python3
# coding: utf-8

import requests
from random import randrange
from time import sleep
import http
import urllib


# Se faire passer pour un vrai navigateur, hyper important pour Pixiv !
headers = {
    "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0"
}


"""
Faire un GET HTTP en réessant de manière bourrin si jamais on a une erreur,
comme par exemple une rate limit.
@param retry_on_those_http_errors Liste d'erreurs HTTP sur lesquelles on
                                  réessaye.
"""
def get_with_rate_limits ( url, max_retry = 10, retry_on_those_http_errors = [] ):
    retry_count = 0
    while True : # Solution très bourrin pour gèrer les rate limits
        try :
            to_return = requests.get( url, headers = headers )
            if to_return.status_code in retry_on_those_http_errors :
                print( f"[get_with_rate_limits] Erreur {to_return.status_code} pour : {url}" )
                sleep( randrange( 30, 60 ) )
                retry_count += 1
                if retry_count > max_retry :
                    raise Exception( "Nombre maximal de tentatives pour un ré-essai sur une erreur HTTP (Ici, erreur {to_return.status_code})" ) # Doit tomber dans le collecteur d'erreurs
            else :
                return to_return
        
        except http.client.RemoteDisconnected as error :
            print( error )
            sleep( randrange( 5, 15 ) )
            retry_count += 1
            if retry_count > max_retry :
                raise error # Sera récupérée par le collecteur d'erreurs
        
        except urllib.error.HTTPError as error : # Je ne sais plus si c'est cette erreur peut tomber
            if error.code == 404 : # N'arrive pas en fait, la lib laisse passer les erreurs 404
                print( error )
                raise error # On peut raise tout de suite car 404
            else :
                print( error )
                sleep( randrange( 5, 15 ) )
                retry_count += 1
                if retry_count > max_retry :
                    raise error # Sera récupérée par le collecteur d'erreurs
        
        except Exception as error :
            print( error )
            sleep( randrange( 5, 15 ) )
            retry_count += 2
            if retry_count > max_retry :
                raise error # Sera récupérée par le collecteur d'erreurs
