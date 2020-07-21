#!/usr/bin/python3
# coding: utf-8

import requests
from random import randrange
from time import sleep
import http

"""
Faire un GET HTTP en réessant de manière bourrin si jamais on a une erreur,
comme par exemple une rate limit.
"""
def get_with_rate_limits ( url, max_retry = 10 ):
    retry_count = 0
    while True : # Solution très bourrin pour gèrer les rate limits
        try :
            return requests.get( url )
            break
        
        except http.client.RemoteDisconnected as error :
            print( error )
            sleep( randrange( 5, 15 ) )
            retry_count += 1
            if retry_count > max_retry :
                raise error # Sera récupérée par le collecteur d'erreurs
        
        except urllib.error.HTTPError as error :
            if error.code == 404 :
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
