#!/usr/bin/python3
# coding: utf-8

from tweepy.errors import TweepyException
from urllib.error import URLError
from requests.exceptions import ConnectionError
import socket


"""
Déterminer si une exception est dûe à une perte de connexion au réseau.
ATTENTION : "except Exception" ne prend que l'exception la plus "haute".
"""
def is_network_crash ( exception ) -> bool :
    if type( exception ) == TweepyException : # type() et pas isinstance()
        return True
    if type( exception ) == URLError :
        if type( exception.reason ) == OSError :
            if exception.reason.errno == 101 : # Network is unreachable
                return True
        return not network_available()
    if type( exception ) == ConnectionError :
        return not network_available()
    return False

"""
Vérifier la connexion au réseau en contactant Cloudflare.
"""
def network_available () -> bool :
    try : socket.create_connection( ( "1.1.1.1", 53 ) )
    except OSError : return False
    else : return True
