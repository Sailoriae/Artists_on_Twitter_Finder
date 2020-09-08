#!/usr/bin/python3
# coding: utf-8

from http.server import ThreadingHTTPServer

try :
    from class_HTTP_Server import http_server_container
except ModuleNotFoundError :
    from .class_HTTP_Server import http_server_container

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param


"""
ATTENTION ! CE THREAD DOIT ETRE UNIQUE !

Thread du serveur HTTP.
"""
def thread_http_server( thread_id : int, shared_memory ) :
    HTTP_Server = http_server_container( shared_memory._pyroUri.asString() )
    
    # http.server.ThreadingHTTPServer() fait lui-même le multi-threads du
    # serveur HTTP
    http_server = ThreadingHTTPServer( ("", param.HTTP_SERVER_PORT ), HTTP_Server )
    
    while shared_memory.keep_service_alive :
        http_server.handle_request()
    http_server.server_close()
    
    print( "[http_server_th" + str(thread_id) + "] Arrêté !" )
    return
