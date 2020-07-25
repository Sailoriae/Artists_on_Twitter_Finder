#!/usr/bin/python3
# coding: utf-8

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param


"""
Serveur HTTP
"""
# Fonction contenant la classe, permettant de passer le paramètre pipeline
def http_server_container ( pipeline_arg ) :
    class HTTP_Server( BaseHTTPRequestHandler ) :
        pipeline = pipeline_arg # Attribut de classe
        
        def __init__( self, *args, **kwargs ) :
            super(BaseHTTPRequestHandler, self).__init__(*args, **kwargs)
        
        def do_GET( self ) :
            page = urlsplit( self.path ).path
            if page[0] == "/" :
                page = page[1:] # On enlève le premier "/"
            page = page.split("/")
            parameters = dict( parse_qs( urlsplit( self.path ).query ) )
            
            # Si on est à la racine
            # GET /
            # GET /?url=[URL de l'illustration de requête]
            if len(page) == 1 and page[0] == "" :
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                
                response = "{"
                
                # On envoit forcément les mêmes champs, même si ils sont vides !
                try :
                    illust_url = parameters["url"][0]
                except KeyError :
                    response += "\"status\" : \"END\""
                    response += ", \"twitter_accounts\" : [ ]"
                    response += ", \"results\" : [ ]"
                    response += ", \"error\" : \"NO_URL_FIELD\""
                else :
                    # Lance une nouvelle requête, ou donne la requête déjà existante
                    request = self.pipeline.launch_full_process( illust_url,
                                                                 ip_address = self.client_address[0],
                                                                 intelligent_skip_indexing = param.FORCE_INTELLIGENT_SKIP_INDEXING )
                    
                    # Si request == None, c'est qu'on ne peut pas lancer une
                    # nouvelle requête car l'addresse IP a trop de requêtes en
                    # cours de traitement, donc on renvoit l'erreur
                    # YOUR_IP_HAS_MAX_PENDING_REQUESTS
                    if request == None :
                        response += "\"status\" : \"END\""
                        response += ", \"twitter_accounts\" : [ ]"
                        response += ", \"results\" : [ ]"
                        response += ", \"error\" : \"YOUR_IP_HAS_MAX_PENDING_REQUESTS\""
                    
                    # Sinon, on envoit les informations sur la requête
                    else :
                        response += "\"status\" : \"" + request.get_status_string() + "\""
                        
                        response += ", \"twitter_accounts\" : ["
                        for account in request.twitter_accounts_with_id :
                            response += " { "
                            response += "\"account_name\" : \"" + str(account[0]) + "\", "
                            response += "\"account_id\" : \"" + str(account[1]) + "\""  # Envoyer en string et non en int
                            response += " },"
                        if response[-1] == "," : # Supprimer la dernière virgule
                            response = response[:-1]
                        response += " ]"
                        
                        response += ", \"results\" : ["
                        for result in request.founded_tweets :
                            response += " { "
                            response += "\"tweet_id\" : \"" + str(result.tweet_id) + "\", " # Envoyer en string et non en int
                            response += "\"account_id\" : \"" + str(result.account_id) + "\", " # Envoyer en string et non en int
                            response += "\"image_position\" : " + str(result.image_position) + ", "
                            response += "\"distance\" : " + str(result.distance)
                            response += " },"
                        if response[-1] == "," : # Supprimer la dernière virgule
                            response = response[:-1]
                        response += " ]"
                        
                        if request.problem != None :
                            response += ", \"error\" : \"" + request.problem + "\""
                        else :
                            response += ", \"error\" : \"\""
                    
                response += "}\n"
                
                self.wfile.write( response.encode("utf-8") )
            
            # Si on demande les stats
            # GET /stats
            elif len(page) == 1 and page[0] == "stats" : 
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                
                response = "{"
                
                response += "\"indexed_tweets_count\" : " + str(self.pipeline.tweets_count) + ", "
                response += "\"indexed_accounts_count\" : " + str(self.pipeline.accounts_count)
                
                response += "}\n"
                
                self.wfile.write( response.encode("utf-8") )
            
            # Sinon, page inconnue, erreur 404
            else :
                self.send_response(404)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                
                self.wfile.write( "404 Not Found\n".encode("utf-8") )
    
    return HTTP_Server
