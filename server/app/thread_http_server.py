#!/usr/bin/python3
# coding: utf-8

try :
    from class_Threaded_HTTP_Server import Threaded_HTTP_Server
    from class_HTTP_Server import HTTP_Server
except ModuleNotFoundError :
    from .class_Threaded_HTTP_Server import Threaded_HTTP_Server
    from .class_HTTP_Server import HTTP_Server

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param


"""
Thread du serveur HTTP.
"""
def thread_http_server( thread_id : int, pipeline ) :
    http_server = Threaded_HTTP_Server( ("", param.HTTP_SERVER_PORT ), HTTP_Server )
    
    while pipeline.keep_service_alive :
        http_server.handle_request()
    http_server.server_close()
    
    print( "[http_server_th" + str(thread_id) + "] Arrêté !" )
    return
