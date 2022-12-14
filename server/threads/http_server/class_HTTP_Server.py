#!/usr/bin/python3
# coding: utf-8

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit
import json
from time import time
from datetime import datetime
import traceback
from secrets import token_hex
from io import DEFAULT_BUFFER_SIZE

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
    change_wdir( "../.." )
    path.append(get_wdir())

from threads.http_server.generate_json import get_user_request_json_model
from threads.http_server.generate_json import generate_user_request_json
import parameters as param
from shared_memory.open_proxy import open_proxy


# Taille maximale de l'URL d'un illustration (Sinon, "URL_TOO_LONG")
# On sépare pour permettre une potentielle autre utilisation du POST
MAX_ILLUST_URL_SIZE = 256 # caractères

# Nombre de secondes pendant lesquelles ont garde en cache le JSON retourné par
# l'endpoint GET /stats (Au delà, il sera régénéré)
STATS_CACHE_TTL = 3 # secondes

# Taille maximale d'une image pour la recherche directe (Sinon HTTP 413)
MAX_IMAGE_SIZE = 20971520 # octets = 20 Mo


"""
Serveur HTTP, permettant d'utiliser AOTF.

Note : NE PAS CREER UNE API PERMETTANT DE FAIRE UNE RECHERCHE DANS TOUTE LA
BASE DE DONNEES ! En effet, malgré la vitesse améliorée par la méthode de la
recherche exacte, elle est toujours trop lente pour les très grosses BDD, et
donc peut être utilisé à des fins de DDOS.
De plus, cela serait une grosse faille de sécurité. Voir ce que sont les
"Server side request forgery" (SSRF).
"""
# Fonction contenant la classe, permettant de passer le paramètre shared_memory
def http_server_container ( shared_memory_uri_arg ) :
    class HTTP_Server( BaseHTTPRequestHandler ) :
        # Pyro5 ne permet plus de partager un Proxy entre threads (Snif)
        shared_memory_uri = shared_memory_uri_arg
        
        # Envoyer un header "Server" personnalisé
        server_version = "Artists on Twitter Finder"
        sys_version = ""
        
        # Mise en cache
        stats_cache = None # Endpoint GET /stats
        stats_cache_date = 0 # Besoin de rafraichir toutes les STATS_CACHE_TTL secondes
        
        # Dictionnaires des requêtes directes
        # Identifiant -> Compte sur lequel rechercher
        direct_requests = {}
        
        def __init__( self, *args, **kwargs ) :
            # En cas de crash, pour savoir si on peut envoyer un code 500
            # Rappel : Cette classe est réinstanciée à chaque requête
            self.header_sent = False
            
            super(BaseHTTPRequestHandler, self).__init__(*args, **kwargs)
        
        # Ne pas afficher les logs par défaut dans la console
        def log_message( self, format, *args ) :
            return
        
        # La méthode POST fonctionne comme la méthode GET
        def do_POST( self ) :
            return self.do_GET( method = "POST" )
        
        # La méthode HEAD doit fonctionner comme la méthode GET
        # Elle n'envoit juste pas de corps
        def do_HEAD( self ) :
            return self.do_GET( method = "HEAD" )
        
        # Collecteur d'erreurs du traitement des requêtes HTTP
        def do_GET( self, method = "GET" ) :
            try :
                self._do_GET( method = method )
            except Exception as error :
                error_name = "Erreur lors du traitement d'une requête HTTP !\n"
                error_name += f"S'est produite le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')}.\n"
                
                file = open( "http_server_errors.log", "a" )
                file.write( "ICI LE COLLECTEUR D'ERREURS DU SERVEUR HTTP !\n" )
                file.write( "Je suis dans le fichier suivant : threads/http_server/class_HTTP_Server.py\n" )
                file.write( error_name )
                traceback.print_exc( file = file )
                file.write( "\n\n\n" )
                file.close()
                
                print( error_name, end = "" )
                print( f"{type(error).__name__}: {error}" )
                print( "La pile d'appel complète a été écrite dans un fichier." )
                
                if self.header_sent : return
                
                self.send_response(500)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                if method != "HEAD" :
                    self.wfile.write( "500 Internal Server Error\n".encode("utf-8") )
        
        # Parce que XMLHttpRequest fait chier lors de l'envoi d'un fichier
        def do_OPTIONS( self ) :
            self.send_response(200)
            self.send_header("Allow", "GET, POST, HEAD, OPTIONS")
            self.send_header("Access-Control-Allow-Origin", "*") # Pour le dév de l'UI web, doit être modifié par le proxy en production
            self.send_header("Access-Control-Allow-Methods", "GET, POST, HEAD, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
        
        # Notre méthode GET gère aussi le POST et le HEAD
        def _do_GET( self, method = "GET" ) :
            # Analyser le chemin du GET HTTP
            endpoint = urlsplit( self.path ).path
            parameters = dict( parse_qs( urlsplit( self.path ).query ) )
            
            client_ip = self.headers["X-Forwarded-For"]
            if client_ip == None :
                client_ip = self.client_address[0]
            
            # Obtenir la taille du contenu (Dans le cas d'une requête POST)
            if method == "POST" :
                # Le param "Content-Length" est insensible à la casse
                content_length = int(self.headers.get("Content-Length", 0))
            
            # On mettra dans ces variables ce qu'on va retourner
            http_code : int = 200
            response_is_json : bool = False
            response : str = ""
            
            # Connexion au serveur de mémoire partagée
            # On crée une connexion à chaque requête, parce que Pyro5 ne permet
            # plus de partager un Proxy entre threads
            shared_memory = open_proxy( HTTP_Server.shared_memory_uri )
            
            # A partie de maintenant, on fait un "if" puis que des "elif" pour
            # toutes les autres possibilités, puis un "else" final pour le 404
            
            # =================================================================
            # HTTP 429
            # =================================================================
            # Vérifier que l'utilisateur ne fait pas trop de requêtes
            # En premier, c'est plus logique
            # Uniquement pour les API "lourdes" (C'est à dire qui font appel à
            # la mémoire partagée) et qui ne sont pas mises en cache
            # - "/query" en fait partie
            # - "/stats" peut être mise en cache
            # - "/config" est légère
            if ( endpoint not in [ "/stats", "/config" ] and
                 not shared_memory.http_limitator.can_request( client_ip ) ) :
                http_code = 429
                response = "429 Too Many Requests\n"
            
            # Ca ne sert à rien d'envoyer des erreurs HTTP 414 (URI Too Long),
            # car on a déjà lu l'URI de la requête
            
            # Ce ne sert non plus à rien d'envoyer par défaut des erreurs HTTP
            # 413 (Payload Too Large), car si on ne lit pas le contenu, il
            # reste dans la socket (Où il est déjà)
            
            # Il faut quand même vérifier que l'utilisateur n'envoie pas trop
            # de données (C'est ce qu'on fait pour l'API "/query")
            
            # =================================================================
            # HTTP 200 (Ou 403 pour les endpoints avancés)
            # =================================================================
            # Racine de l'API, affiche juste un petit message
            # GET /
            elif endpoint == "/" :
                http_code = 200
                response = "Artists of Twitter Finder\n"
                response += "Vous êtes sur l'API d'AOTF. Merci de consulter sa documentation afin de l'utiliser.\n"
                response += "You are on the AOTF API. Please check its documentation to use it.\n"
            
            # Si on veut lancer une requête ou obtenir son résultat
            # GET /query
            # GET /query?url=[URL de l'illustration de requête]
            elif endpoint == "/query" :
                http_code = 200
                response_dict = get_user_request_json_model()
                
                illust_url = None
                if method == "POST" :
                    # UTF-8 prend 1 à 4 octets par caractères
                    # Donc si on détasse 4 fois la taille maximale des URL qu'on peut
                    # traiter, on ne lit rien et on retourne une erreur "URL_TOO_LONG"
                    if content_length > MAX_ILLUST_URL_SIZE * 4 :
#                        http_code = 413 # Payload Too Large
                        response_dict["error"] = "URL_TOO_LONG"
                    
                    elif content_length != 0 :
                        try :
                            illust_url = self.rfile.read(content_length).decode('utf-8')
                        except UnicodeDecodeError :
                            response_dict["error"] = "NOT_AN_URL"
                        content_length = 0 # Signaler que le contenu a été lu
                else :
                    try :
                        illust_url = parameters["url"][0]
                    except KeyError :
                        pass
                
                # On envoit forcément les mêmes champs, même si ils sont vides !
                if illust_url == None :
                    if response_dict["error"] == None :
#                        http_code = 400 # Bad Request
                        response_dict["error"] = "NO_URL_FIELD"
                
                elif len( illust_url ) > MAX_ILLUST_URL_SIZE :
#                    if method == "POST" : http_code = 413 # Payload Too Large
#                    else : http_code = 414 # URI Too Long
                    response_dict["error"] = "URL_TOO_LONG"
                
                else :
                    # Lance une nouvelle requête, ou donne la requête déjà existante
                    request = shared_memory.user_requests.launch_request( illust_url,
                                                                          ip_address = client_ip )
                    
                    # Si request == None, c'est qu'on ne peut pas lancer une
                    # nouvelle requête car l'adresse IP a trop de requêtes en
                    # cours de traitement, donc on renvoit l'erreur
                    # YOUR_IP_HAS_MAX_PROCESSING_REQUESTS
                    if request == None :
                        response_dict["error"] = "YOUR_IP_HAS_MAX_PROCESSING_REQUESTS"
                    
                    # Sinon, on envoit les informations sur la requête
                    else :
                        generate_user_request_json( request, response_dict )
                
                response = json.dumps( response_dict )
                response_is_json = True
            
            # Si on demande les stats
            # GET /stats
            elif endpoint == "/stats" :
                http_code = 200
                
                # Eviter d'ouvrir deux fois ce proxy
                shared_memory_scan_requests = shared_memory.scan_requests
                
                if ( HTTP_Server.stats_cache == None or
                     time() - HTTP_Server.stats_cache_date >= STATS_CACHE_TTL ) :
                    HTTP_Server.stats_cache = json.dumps({
                        "indexed_tweets_count" : shared_memory.tweets_count,
                        "indexed_accounts_count" : shared_memory.accounts_count,
                        "processing_user_requests_count" : shared_memory.user_requests.processing_requests_count,
                        "processing_scan_requests_count" : shared_memory_scan_requests.processing_requests_count,
                        "pending_tweets_count" : shared_memory_scan_requests.step_C_index_tweets_queue.qsize()
                    })
                    HTTP_Server.stats_cache_date = time()
                
                response = HTTP_Server.stats_cache
                response_is_json = True
            
            # Si on demande les informations sur le serveur
            # GET /config
            elif endpoint == "/config" :
                http_code = 200
                
                # Ne peut pas être mis en cache car dépend de l'adresse IP
                response_dict = {
                    "limit_per_ip_address" : param.MAX_PROCESSING_REQUESTS_PER_IP_ADDRESS,
                    "ip_can_bypass_limit" : client_ip in param.UNLIMITED_IP_ADDRESSES,
                    "ip_can_use_advanced" : client_ip in param.ADVANCED_IP_ADDRESSES,
                    "update_accounts_frequency" : param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE,
                    "max_illust_url_size" : MAX_ILLUST_URL_SIZE
                }
                
                response = json.dumps( response_dict )
                response_is_json = True
            
            # Si on veut lancer une recherche par image ou obtenir son résultat
            # GET /search
            elif endpoint == "/search" :
                if not client_ip in param.ADVANCED_IP_ADDRESSES :
                    http_code = 403
                    response = "403 Forbidden\n"
                
                else :
                    http_code = 200
                    response_dict = get_user_request_json_model()
                    
                    if method != "POST" and not "identifier" in parameters :
                        response_dict["error"] = "IDENTIFIER_MISSING"
                    
                    elif method == "POST" and content_length == 0 :
                        response_dict["error"] = "IMAGE_MISSING"
                    
                    elif method == "POST" and content_length > MAX_IMAGE_SIZE :
                        response_dict["error"] = "QUERY_IMAGE_TOO_BIG"
                    
                    # Obtenir une requête
                    elif method != "POST" and "identifier" in parameters :
                        identifier = parameters["identifier"][0]
                        account_name = HTTP_Server.direct_requests[identifier] if identifier in HTTP_Server.direct_requests else None
                        
                        request = shared_memory.user_requests.launch_direct_request( identifier,
                                                                                     account_name = account_name,
                                                                                     do_not_launch = True )
                        
                        if request == None :
                            response_dict["error"] = "NO_SUCH_REQUEST"
                        else :
                            generate_user_request_json( request, response_dict )
                            response_dict["identifier"] = identifier
                    
                    # Lancer une nouvelle requête
                    elif method == "POST" and content_length > 0 :
                        identifier = token_hex(16)
                        
                        account_name = None
                        if "account_name" in parameters :
                            account_name = parameters["account_name"][0]
                        
                        HTTP_Server.direct_requests[identifier] = account_name
                        
                        binary_image = self.rfile.read(content_length)
                        content_length = 0 # Signaler que le contenu a été lu
                        
                        request = shared_memory.user_requests.launch_direct_request( identifier,
                                                                                     account_name = account_name,
                                                                                     binary_image = binary_image,
                                                                                     ip_address = client_ip )
                        
                        # L'adresse IP a trop de requêtes en cours
                        if request == None :
                            response_dict["error"] = "YOUR_IP_HAS_MAX_PROCESSING_REQUESTS"
                        
                        else :
                            generate_user_request_json( request, response_dict )
                            response_dict["identifier"] = identifier
                    
                    else :
                        raise Exception( "Ligne impossible à atteindre !" )
                    
                    response = json.dumps( response_dict )
                    response_is_json = True
            
            # =================================================================
            # HTTP 404
            # =================================================================
            # Sinon, page inconnue, erreur 404
            else :
                http_code = 404
                response = "404 Not Found\n"
            
            # Dans le cas d'un POST, il faut forcément lire le contenu envoyé,
            # sinon Apache retourne à utilisateur une erreur "502 Bad Gateway"
            # Confirmation : https://stackoverflow.com/a/28220558
            # On est obligé de lire avant de répondre
            if method == "POST" :
                # On lit par tranches de DEFAULT_BUFFER_SIZE afin de ne pas
                # saturer la mémoire vive
                # TODO : Trouver un meilleur moyen pour vider la socket
                # d'entrée sans la lire, c'est à dire sans charger le contenu
                # dans la mémoire vive
                for read_size in [ DEFAULT_BUFFER_SIZE ] * ( content_length // DEFAULT_BUFFER_SIZE ) + [ content_length % DEFAULT_BUFFER_SIZE] :
                    self.rfile.read(read_size)
            
            # Envoyer la réponse
            self.header_sent = True
            self.send_response(http_code)
            if response_is_json :
                self.send_header("Content-type", "application/json; charset=utf-8")
            else :
                self.send_header("Content-type", "text/plain; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*") # Pour le dév de l'UI web, doit être modifié par le proxy en production
            self.end_headers()
            if method != "HEAD" :
                self.wfile.write( response.encode("utf-8") )
            
            print( "[HTTP]", client_ip, self.log_date_time_string(), method, self.path, "HTTP", http_code )
    
    return HTTP_Server
