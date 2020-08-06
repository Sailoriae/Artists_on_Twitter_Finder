#!/usr/bin/python3
# coding: utf-8

import Pyro4
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
# Fonction contenant la classe, permettant de passer le paramètre shared_memory
def http_server_container ( shared_memory_uri_arg ) :
    class HTTP_Server( BaseHTTPRequestHandler ) :
        shared_memory_uri = shared_memory_uri_arg # Attribut de classe
        
        def __init__( self, *args, **kwargs ) :
            self.shared_memory = Pyro4.Proxy( self.shared_memory_uri )
            super(BaseHTTPRequestHandler, self).__init__(*args, **kwargs)
        
        # Ne pas afficher les logs par défaut dans la console
        def log_message( self, format, *args ) :
            return
        
        def do_GET( self ) :
            page = urlsplit( self.path ).path
            if page[0] == "/" :
                page = page[1:] # On enlève le premier "/"
            page = page.split("/")
            parameters = dict( parse_qs( urlsplit( self.path ).query ) )
            
            client_ip = self.headers["X-Forwarded-For"]
            if client_ip == None :
                client_ip = self.client_address[0]
            
            print( "[HTTP]", client_ip, self.log_date_time_string(), "GET", self.path )
            
            # Vérifier que l'utilisateur ne fait pas trop de requêtes
            if not self.shared_memory.http_limitator.can_request( client_ip ) :
                self.send_response(429)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                
                self.wfile.write( "429 Too Many Requests\n".encode("utf-8") )
                return
            
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
                    request = self.shared_memory.user_requests.launch_request( illust_url,
                                                                               ip_address = client_ip )
                    
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
                
                response += "\"indexed_tweets_count\" : " + str(self.shared_memory.tweets_count) + ", "
                response += "\"indexed_accounts_count\" : " + str(self.shared_memory.accounts_count) + ", "
                response += "\"limit_per_ip_address\" : " + str(param.MAX_PENDING_REQUESTS_PER_IP_ADDRESS) + ", "
                response += "\"update_accounts_frequency\" : " + str(param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE)
                
                response += "}\n"
                
                self.wfile.write( response.encode("utf-8") )
            
            # Sinon, page inconnue, erreur 404
            else :
                self.send_response(404)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                
                self.wfile.write( "404 Not Found\n".encode("utf-8") )
    
    return HTTP_Server
