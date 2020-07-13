"""
Script principal. NE PAS LE LANCER PLUSIEURS FOIS !

Doit être utilisé avec IPython de préférance.
Sinon les messages des threads s'afficheront que lorsqu'il y aura une input.
"""

import threading
import queue
from time import sleep
import re
from typing import List

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs, urlsplit

from class_CBIR_Engine_with_Database import CBIR_Engine_with_Database
from class_Link_Finder import Link_Finder
import parameters as param

from database import SQLite
from twitter import TweepyAbtraction


# TODO : Thread de vidage de la liste des requêtes lorsqu'elles sont au niveau
# de traitement 8 (= Fin de traitement)


"""
Classe représentant une requête dans notre système.
Cet objet est le même durant tout le processus.
"""
class Request :
    """
    @param input_url URL de l'illustration de requête.
    @param full_pipeline Est ce que la requête a été mise dans la liste
                         `requests`... C'est à dire : Doit elle faire toute la
                         procédure de traitement / tout le pipeline ?
                         (OPTIONNEL, non par défaut)
                         Seule la fonction launch_process() doit être utilisée
                         pour lancer une procédure complète.
    """
    def __init__ ( self, input_url, full_pipeline = False ) :
        self.full_pipeline = full_pipeline
        
        # Une requête est identifiée par son URL de requête, c'est à dire l'URL
        # de l'illustration demandée
        self.input_url = input_url
        
        # Si jamais il y a eu un problème et qu'on ne peut pas traiter la
        # requête, on la met ici
        self.problem = None
        
        # Résultats du Link Finder
        self.twitter_accounts = []
        self.image_url = None
        
        # Liste de tuples (str, int), avec le nom du compte Twitter, et son ID
        # On est certain que ces comptes existent, contrairement au résultat
        # Link Finder
        self.twitter_accounts_with_id = []
        
        # Résultats de la fonction get_GOT3_list() dans la classe
        # CBIR_Engine_with_Database, associés au compte Twitter scanné.
        # A VIDER UNE FOIS UTILISE, CAR C'EST LOURD EN MEMOIRE !
        self.get_GOT3_list_result = []
        
        # Résultats de la recherche inversée de l'image
        # Est une liste d'objets Image_in_DB
        self.founded_tweets = []
        
        # Status du traitement de cette requête :
        # 0 = En attente de traitement par un thread de Link Finder
        # 1 = En cours de traitement par un thread de Link Finder
        #     link_finder_thread_main()
        # 2 = En attente de traitement par un thread de listage des tweet
        #     d'un compte Twitter
        # 3 = En cours de traitement par un thread de listage des tweets d'un
        #     compte Twitter
        #     list_account_tweets_thread_main()
        # 4 = En attente de traitement par un thread d'indexation des tweet
        #     d'un compte Twitter
        # 5 = En cours de traitement par un thread d'indexation des tweets d'un
        #     compte Twitter
        #     index_twitter_account_thread_main()
        # 6 = En attente de traitement par un thread de recherche d'image inversée
        # 7 = En cours de traitement par un thread de recherche d'image inversée
        #     reverse_search_thread_main()
        # 8 = Fin de traitement
        self.status = 0
    
    def set_status_wait_link_finder( self ):
        self.status = 0
    def set_status_link_finder( self ):
        self.status = 1
    def set_status_wait_list_account_tweets( self ):
        self.status = 2
    def set_status_list_account_tweets( self ):
        self.status = 3
    def set_status_wait_index_twitter_account( self ):
        self.status = 4
    def set_status_index_twitter_account( self ):
        self.status = 5
    def set_status_wait_reverse_search_thread( self ):
        self.status = 6
    def set_status_reverse_search_thread( self ):
        self.status = 7
    def set_status_done( self ):
        self.status = 8
    
    def get_status_string( self ):
        if self.status == 0 :
            return "WAIT_LINK_FINDER"
        if self.status == 1 :
            return "LINK_FINDER"
        if self.status == 2 :
            return "WAIT_LIST_ACCOUNT_TWEETS"
        if self.status == 3 :
            return "LIST_ACCOUNT_TWEETS"
        if self.status == 4 :
            return "WAIT_INDEX_ACCOUNT_TWEETS"
        if self.status == 5 :
            return "INDEX_ACCOUNT_TWEETS"
        if self.status == 6 :
            return "WAIT_IMAGE_REVERSE_SEARCH"
        if self.status == 7 :
            return "IMAGE_REVERSE_SEARCH"
        if self.status == 8 :
            return "END"


"""
Classe contenant l'ensemble des requêtes dans le système.
A INITIALISER UNE SEULE FOIS !
"""
class Pipeline :
    def __init__ ( self ) :
        # Les objets sont passés par adresse en Python
        # Donc ils peuvent être en même dans dans la liste "requests" en en même temps
        # dans les différentes files d'attente
        
        # De plus, l'objet queue.Queue() est safe pour le multi-threads
        
        # Liste des requêtes effectuées sur notre système
        self.requests = []
        
        # Sémaphore pour l'accès à la liste request
        self.requests_sem = threading.Semaphore()
        
        # ETAPE 1, code de status de la requête : 1
        # File d'attente de Link Finder
        self.link_finder_queue = queue.Queue()
        
        # ETAPE 2, PARTIE 1/2, code de status de la requête : 3
        # File d'attente de listage des tweets d'un compte Twitter
        self.list_account_tweets_queue = queue.Queue()
        
        # ETAPE 2, PARTIE 2/2, code de status de la requête : 5
        # File d'attente d'indexation des tweets d'un compte Twitter
        self.index_twitter_account_queue = queue.Queue()
        
        # ETAPE 3, code de status de la requête : 7
        # File d'attente de la recherche d'image inversée
        self.reverse_search_queue = queue.Queue()
    
    """
    Lancement de la procédure complète pour une URL d'illustration.
    @param illust_url L'illustration d'entrée.
    @return L'objet Request créé.
    """
    def launch_full_process ( self, illust_url : str ) :
        # Vérifier d'abord qu'on n'est pas déjà en train de traiter cette illustration
        self.requests_sem.acquire()
        for request in self.requests :
            if request.input_url == illust_url :
                self.requests_sem.release()
                return
        self.requests_sem.release()
        
        request = Request( illust_url, full_pipeline = True )
        self.requests.append( request ) # Passé par adresse car c'est un objet
        self.link_finder_queue.put( request ) # Passé par addresse car c'est un objet
        
        return request
    
    """
    Obtenir l'objet d'une requête.
    @param illust_url L'illustration d'entrée.
    @return Un objet Request,
            Ou None si la requête est inconnue.
    """
    def get_request ( self, illust_url : str ) -> Request :
        self.requests_sem.acquire()
        for request in self.requests :
            if request.input_url == illust_url :
                self.requests_sem.release()
                return request
        self.requests_sem.release()
        
        return None


"""
Variables globales, partagées entre les Threads.
"""
# Variable pour éteindre le service
keep_service_alive = True

pipeline = Pipeline()


"""
ETAPE 1 du traitement d'une requête.
Thread de Link Finder.
"""
def link_finder_thread_main( thread_id : int ) :
    # Initialisation de notre moteur de recherche des comptes Twitter
    finder_engine = Link_Finder()
    
    # Initialisation de notre couche d'abstraction à l'API Twitter
    twitter = TweepyAbtraction( param.API_KEY,
                                param.API_SECRET,
                                param.OAUTH_TOKEN,
                                param.OAUTH_TOKEN_SECRET )
    
    # Tant que on ne nous dit pas de nous arrêter
    while keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = pipeline.link_finder_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # On passe le status de la requête à "En cours de traitement par un
        # thread de Link Finder"
        request.set_status_link_finder()
        
        print( "[link_finder_th" + str(thread_id) + "] Link Finder pour :\n" +
               "[link_finder_th" + str(thread_id) + "] " + request.input_url )
        
        # On lance la recherche des comptes Twitter de l'artiste
        twitter_accounts = finder_engine.get_twitter_accounts( request.input_url )
        
        # Si jamais l'URL de la requête est invalide, on ne va pas plus loin
        # avec elle (On passe donc son status à "Fin de traitement")
        if twitter_accounts == None :
            request.problem = "INVALID_URL"
            request.set_status_done()
            
            print( "[link_finder_th" + str(thread_id) + "] URL invalide ! Elle ne mène pas à une illustration." )
            continue
        
        # Si jamais le site n'est pas supporté, on ne va pas plus loin avec
        # cette requête (On passe donc son status à "Fin de traitement")
        elif twitter_accounts == False :
            request.problem = "UNSUPPORTED_WEBSITE"
            request.set_status_done()
            
            print( "[link_finder_th" + str(thread_id) + "] Site non supporté !" )
            continue
        
        # Si jamais aucun compte Twitter n'a été trouvé, on ne va pas plus loin
        # avec la requête (On passe donc son status à "Fin de traitement")
        elif twitter_accounts == []:
            request.problem = "NO_TWITTER_ACCOUNT_FOR_THIS_ARTIST"
            request.set_status_done()
            
            print( "[link_finder_th" + str(thread_id) + "] Aucun compte Twitter trouvé pour l'artiste de cette illustration !" )
            continue
        
        # Stocker les comptes Twitter trouvés
        request.twitter_accounts = twitter_accounts
        
        # On vérifie la liste des comptes Twitter
        for account in twitter_accounts :
            account_id = twitter.get_account_id( account )
            if account_id != None :
                request.twitter_accounts_with_id.append( ( account, account_id ) )
        
        # Si jamais aucun compte Twitter valide n'a été trouvé, on ne va pas
        # plus loin avec la requête (On passe donc son status à "Fin de
        # traitement")
        if twitter_accounts == []:
            request.problem = "NO_VALID_TWITTER_ACCOUNT_FOR_THIS_ARTIST"
            request.set_status_done()
            
            print( "[link_finder_th" + str(thread_id) + "] Aucun compte Twitter valide trouvé pour l'artiste de cette illustration !" )
            continue
        
        print( "[link_finder_th" + str(thread_id) + "] Comptes Twitter trouvés pour cet artiste :\n" +
               "[link_finder_th" + str(thread_id) + "] " + str( twitter_accounts ) )
        
        # Théoriquement, on a déjà vérifié que l'URL existe, donc on devrait
        # forcément trouver une image pour cette requête
        request.image_url = finder_engine.get_image_url( request.input_url )
        
        print( "[link_finder_th" + str(thread_id) + "] URL de l'image trouvée :\n" +
               "[link_finder_th" + str(thread_id) + "] " + request.image_url )
        
        # On passe le status de la requête à "En attente de traitement par un
        # thread de listage des tweets d'un compte Twitter"
        request.set_status_wait_list_account_tweets()
        
        # On met la requête dans la file d'attente de listage des tweets d'un
        # compte Twitter
        # Si on est dans le cas d'une procédure complète
        if request.full_pipeline :
            pipeline.list_account_tweets_queue.put( request )
    
    print( "[link_finder_th" + str(thread_id) + "] Arrêté !" )
    return


"""
ETAPE 2, PARTIE 1/2 du traitement d'une requête.
Thread de listage des Tweets avec médias d'un compte Twitter.

Note importante : Ce thread doit être unique ! Il ne doit pas être exécuté
plusieurs fois.
En effet, il ne doit pas y avoir deux scans en même temps. Pour deux raisons :
- On pourrait scanner un même compte Twitter en même temps, deux fois donc,
- Et l'API Twitter nous bloque si on fait trop de requêtes.
"""
def list_account_tweets_thread_main( thread_id : int ) :
    # Initialisation de notre moteur de recherche d'image par le contenu
    cbir_engine = CBIR_Engine_with_Database()
    
    # Tant que on ne nous dit pas de nous arrêter
    while keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = pipeline.list_account_tweets_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # On passe le status de la requête à "En cours de traitement par un
        # thread de listage des tweets d'un compte Twitter"
        request.set_status_list_account_tweets()
        
        # On liste les tweets des comptes Twitter de la requête
        for twitter_account in request.twitter_accounts :
            print( "[list_account_tweets_th" + str(thread_id) + "] Listage des tweets du compte Twitter @" + twitter_account + "." )
            
            GOT3_list = cbir_engine.get_GOT3_list( twitter_account )
            
            if GOT3_list == None :
                continue
            
            request.get_GOT3_list_result.append( ( twitter_account,
                                                   GOT3_list ) )
        
        # Si la liste des tweets trouvés par GetOldTweets3 est vide, ça ne sert
        # à rien de continuer !
        if request.get_GOT3_list_result == [] :
            request.problem = "NO_TWITTER_ACCOUNT_FOR_THIS_ARTIST"
            request.set_status_done()
            
            print( "[list_account_tweets_th" + str(thread_id) + "] Aucun compte Twitter valide !" )
            continue # On arrête là
        
        # On passe le status de la requête à "En attente de traitement par un
        # thread d'indexation des tweets d'un compte Twitter"
        request.set_status_wait_index_twitter_account()
        
        # On met la requête dans la file d'attente d'indexation des tweets d'un
        # compte Twitter
        # Si on est dans le cas d'une procédure complète
        if request.full_pipeline :
            pipeline.index_twitter_account_queue.put( request )
    
    print( "[list_account_tweets_th" + str(thread_id) + "] Arrêté !" )
    return


"""
ETAPE 2, PARTIE 2/2 du traitement d'une requête.
Thread d'indexation des tweets d'un compte Twitter.

Note importante : Ce thread doit être unique ! Il ne doit pas être exécuté
plusieurs fois.
En effet, il ne doit pas y avoir deux scans en même temps. Pour deux raisons :
- On pourrait scanner un même compte Twitter en même temps, deux fois donc,
- Et l'API Twitter nous bloque si on fait trop de requêtes.
"""
def index_twitter_account_thread_main( thread_id : int ) :
    # Initialisation de notre moteur de recherche d'image par le contenu
    cbir_engine = CBIR_Engine_with_Database()
    
    # Tant que on ne nous dit pas de nous arrêter
    while keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = pipeline.index_twitter_account_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # On passe le status de la requête à "En cours de traitement par un
        # thread d'indexation des tweets d'un compte Twitter"
        request.set_status_index_twitter_account()
        
        # On index / scan les comptes Twitter de la requête
        for (twitter_account, get_GOT3_list_result) in request.get_GOT3_list_result :
            print( "[index_twitter_account_th" + str(thread_id) + "] Indexation / scan du compte Twitter @" + twitter_account + "." )
            
            cbir_engine.index_or_update_all_account_tweets( twitter_account, get_GOT3_list_result )
        
        # Vider la liste get_GOT3_list_result parce que c'est lourd et qu'on
        # en n'aura plus besoin
        request.get_GOT3_list_result = []
        
        # On passe le status de la requête à "En attente de traitement par un
        # thread de recherche d'image inversée"
        request.set_status_wait_reverse_search_thread()
        
        # On met la requête dans la file d'attente de la recherche d'image inversée
        # Si on est dans le cas d'une procédure complète
        if request.full_pipeline :
            pipeline.reverse_search_queue.put( request )
    
    print( "[index_twitter_account_th" + str(thread_id) + "] Arrêté !" )
    return


"""
ETAPE 3 du traitement d'une requête.
Thread de recherche d'image inversée.
Ou : Thread d'utilisation de l'indexation pour trouver le tweet de requête.
"""
def reverse_search_thread_main( thread_id : int ) :
    # Initialisation de notre moteur de recherche d'image par le contenu
    cbir_engine = CBIR_Engine_with_Database()
    
    # Tant que on ne nous dit pas de nous arrêter
    while keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = pipeline.reverse_search_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # On passe le status de la requête à "En cours de traitement par un
        # thread de recherche d'image inversée"
        request.set_status_reverse_search_thread()
        
        print( "[reverse_search_th" + str(thread_id) + "] Recherche de l'image suivante :\n" +
               "[reverse_search_th" + str(thread_id) + "] " + request.input_url )
        
        # On recherche les Tweets contenant l'image de requête
        # Et on les stocke dans l'objet de requête
        for twitter_account in request.twitter_accounts :
            print( "[reverse_search_th" + str(thread_id) + "] Recherche sur le compte Twitter @" + twitter_account + "." )
            
            result = cbir_engine.search_tweet( request.image_url, twitter_account )
            if result != None :
                request.founded_tweets += result
            else :
                print( "[reverse_search_th" + str(thread_id) + "] Erreur lors de la recherche d'image inversée." )
                request.problem = "ERROR_DURING_REVERSE_SEARCH"
        
        # Si il n'y a pas de compte Twitter dans la requête
        if request.twitter_accounts == []:
            print( "[reverse_search_th" + str(thread_id) + "] Recherche dans toute la base de données." )
            
            result = cbir_engine.search_tweet( request.image_url )
            if result != None :
                request.founded_tweets += result
            else :
                print( "[reverse_search_th" + str(thread_id) + "] Erreur lors de la recherche d'image inversée." )
        
        # Trier la liste des résultats
        # On trie une liste d'objets par rapport à leur attribut "distance"
        request.founded_tweets = sorted( request.founded_tweets,
                                         key = lambda x: x.distance,
                                         reverse = False )
        
        print( "[reverse_search_th" + str(thread_id) + "] Tweets trouvés (Du plus au moins proche) :\n" +
               "[reverse_search_th" + str(thread_id) + "] " + str( [ data.tweet_id for data in request.founded_tweets ] ) )
        
        # On passe le status de la requête à "Fin de traitement"
        request.set_status_done()
    
    print( "[reverse_search_th" + str(thread_id) + "] Arrêté !" )
    return


"""
Serveur HTTP
"""
class HTTP_Server( BaseHTTPRequestHandler ) :
    def __init__( self, *args, **kwargs ) :
        # Accès direct à la base de données pour le processus principal
        # N'UTILISER QUE DES METHODES QUI FONT SEULEMENT DES SELECT !
        self.bdd_direct_access = SQLite( param.SQLITE_DATABASE_NAME )
        
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
                request = pipeline.get_request( illust_url )
                
                # Si la requête n'a pas encore été faite, on lance la procédure et
                # on affiche son status à 0
                if request == None :
                    request = pipeline.launch_full_process( illust_url )
                
                # On envoit les informations sur la requête
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
            self.end_headers()
            
            response = "{"
            
            stats = self.bdd_direct_access.get_stats()
            response += "\"indexed_tweets_count\" : " + str(stats[0]) + ", "
            response += "\"indexed_accounts_count\" : " + str(stats[1])
            
            response += "}\n"
            
            self.wfile.write( response.encode("utf-8") )
        
        # Sinon, page inconnue, erreur 404
        else :
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            
            self.wfile.write( "404 Not Found\n".encode("utf-8") )

"""
Pour faire du multi-thread du serveur HTTP
Source : https://pymotw.com/2/BaseHTTPServer/index.html#threading-and-forking
"""
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

"""
Thread du serveur HTTP.
"""
def http_server_thread_main( thread_id : int ) :
    http_server = ThreadedHTTPServer( ("", param.HTTP_SERVER_PORT ), HTTP_Server )
    while keep_service_alive :
        http_server.handle_request()
    http_server.server_close()
    
    print( "[http_server_th" + str(thread_id) + "] Arrêté !" )
    return


"""
Obtenir des statistiques sur la base de données
@return Une liste contenant, dans l'ordre suivant :
        - Le nombre de tweets indexés
        - Le nombre de comptes indexés
"""
# Accès direct à la base de données pour le processus principal
# N'UTILISER QUE DES METHODES QUI FONT SEULEMENT DES SELECT !
bdd_direct_access = SQLite( param.SQLITE_DATABASE_NAME )
def get_stats() :
    return bdd_direct_access.get_stats()


"""
Démarrage des threads.
"""
link_finder_threads = []
for i in range( param.NUMBER_OF_LINK_FINDER_THREADS ) :
    link_finder_thread = threading.Thread( name = "link_finder_" + str(i+1),
                                           target = link_finder_thread_main,
                                           args = ( i+1, ) )
    link_finder_thread.start()
    link_finder_threads.append( link_finder_thread )

list_account_tweets_threads = []
for i in range( param.NUMBER_OF_LIST_ACCOUNT_TWEETS_THREADS ) :
    list_account_tweets_thread = threading.Thread( name = "list_account_tweets_" + str(i+1),
                                                     target = list_account_tweets_thread_main,
                                                     args = ( i+1, ) )
    list_account_tweets_thread.start()
    list_account_tweets_threads.append( list_account_tweets_thread )

index_twitter_account_threads = []
for i in range( param.NUMBER_OF_INDEX_TWITTER_ACCOUNT_THREADS ) :
    index_twitter_account_thread = threading.Thread( name = "index_twitter_account_" + str(i+1),
                                                     target = index_twitter_account_thread_main,
                                                     args = ( i+1, ) )
    index_twitter_account_thread.start()
    index_twitter_account_threads.append( index_twitter_account_thread )

reverse_search_threads = []
for i in range( param.NUMBER_OF_REVERSE_SEARCH_THREADS ) :
    reverse_search_thread = threading.Thread( name = "reverse_search_" + str(i+1),
                                              target = reverse_search_thread_main,
                                              args = ( i+1, ) )
    reverse_search_thread.start()
    reverse_search_threads.append( reverse_search_thread )

http_server_threads = []
for i in range( param.NUMBER_OF_HTTP_SERVER_THREADS ) :
    http_server_thread = threading.Thread( name = "http_server_thread_" + str(i+1),
                                           target = http_server_thread_main,
                                           args = ( i+1, ) )
    http_server_thread.start()
    http_server_threads.append( http_server_thread )


"""
Entrée en ligne de commande.
"""
print( "Vous êtes en ligne de commande.")
print( "Tapez `help` pour afficher l'aide.")

while True :
    command = input()
    args = command.split(" ")
    
    if args[0] == "request" :
        if len(args) == 2 :
            print( "Lancement de la procédure !" )
            pipeline.launch_full_process( args[1] )
        else :
            print( "Utilisation : request [URL de l'illustration]" )
    
    elif args[0] == "status" :
        if len(args) == 2 :
            request = pipeline.get_request( args[1] )
            if request != None :
                print( "Status : " + str(request.status) + " " + request.get_status_string() )
            else :
                print( "Requête inconnue pour cet URL !" )
        else :
            print( "Utilisation : status [URL de l'illustration]" )
    
    elif args[0] == "result" :
        if len(args) == 2 :
            request = pipeline.get_request( args[1] )
            if request != None :
                print( "Résultat : " + str( [ (data.tweet_id, data.distance) for data in request.founded_tweets ] ) )
            else :
                print( "Requête inconnue pour cet URL !" )
        else :
            print( "Utilisation : result [URL de l'illustration]" )
    
    elif args[0] == "scan" :
        if len(args) == 2 :
            # Vérification que le nom d'utilisateur Twitter est possible
            if re.compile("^@?(\w){1,15}$").match(args[1]) :
                print( "Demande de scan / d'indexation du compte @" + args[1] + "." )
                
                # Fabrication de l'objet Request
                request = Request( None )
                request.twitter_accounts = [ args[1] ]
                
                # Lancement du scan
                pipeline.index_account_tweets_queue.put( request )
            else :
                print( "Nom de compte Twitter impossible !" )
        else :
            print( "Utilisation : scan [Nom du compte à scanner]" )
    
    elif args[0] == "search" :
        if len(args) in [ 2, 3 ] :
            # Fabrication de l'objet Request
            request = Request( args[1] )
            request.image_url = args[1]
            
            if len(args) == 3 :
                # Vérification que le nom d'utilisateur Twitter est possible
                if re.compile("^@?(\w){1,15}$").match(args[2]) :
                    print( "Recherche sur le compte @" + args[2] + "." )
                    request.twitter_accounts = [ args[2] ]
                    # Lancement de la recherche
                    pipeline.reverse_search_queue.put( request )
                else :
                    print( "Nom de compte Twitter impossible !" )
            else :
                print( "Recherche dans toute la base de données !" )
                # Lancement de la recherche
                pipeline.reverse_search_queue.put( request )
        else :
            print( "Utilisation : search [URL de l'image à chercher] [Nom du compte Twitter (OPTIONNEL)]" )
    
    elif args[0] == "stats" :
        if len(args) == 1 :
            stats = get_stats()
            print( "Nombre de tweets indexés : ", stats[0] )
            print( "Nombre de comptes Twitter indexés : ", stats[1] )
        else :
            print( "Utilisation : stats")
    
    elif args[0] == "stop" :
        if len(args) == 1 :
            print( "Arrêt à la fin des procédures en cours..." )
            keep_service_alive = False
            break
        else :
            print( "Utilisation : stop")
    
    elif args[0] == "help" :
        if len(args) == 1 :
            print( "Lancer une requête : request [URL de l'illustration]\n" +
                   "Voir le status d'une requête : status [URL de l'illustration]\n" +
                   "Voir le résultat d'une requête : result [URL de l'illustration]\n" +
                   "\n" +
                   "Notes :\n" +
                   " - Une requête est une procédure complète pour un illustration\n" +
                   " - Les requêtes sont identifiées par l'URL de l'illustration.\n" +
                   "\n" +
                   "Forcer l'indexation de tous les tweets d'un compte : scan [Nom du compte à scanner]\n" +
                   "Rechercher une image dans la base de données : search [URL de l'image] [Nom du compte Twitter (OPTIONNEL)]\n" +
                   "\n" +
                   "Afficher des statistiques de la base de données : stats\n" +
                   "Arrêter le service : stop\n" +
                   "Afficher l'aide : help\n" )
        else :
            print( "Utilisation : help" )
    
    else :
        print( "Commande inconnue !" )


"""
Arrêt du système.
"""
# Attendre que les threads aient fini
for thread in link_finder_threads :
    thread.join()
for thread in list_account_tweets_threads :
    thread.join()
for thread in index_twitter_account_threads :
    thread.join()
for thread in reverse_search_threads :
    thread.join()
for thread in http_server_threads :
    thread.join()
