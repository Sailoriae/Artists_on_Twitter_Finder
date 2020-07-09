"""
Script principal. NE PAS LE LANCER PLUSIEURS FOIS !

Doit être utilisé avec IPython de préférance.
Sinon les messages des threads s'afficheront que lorsqu'il y aura une input.
"""

import threading
import queue
from time import sleep
import re

from class_CBIR_Engine_with_Database import CBIR_Engine_with_Database
from class_Link_Finder import Link_Finder


# TODO : RETOURNER LES TWEETS TROUVES EN LES ASSOCIANT A LEUR DISTANCE DE
# L'IMAGE DE REQUETE !
# Ce qui permet de les classer ! Car je le rappel, un artiste peut avoir
# plusieurs comptes

# TODO : Thread de vidage de la liste des requêtes lorsqu'elles sont au niveau
# de traitement 6 (= Fin de traitement)

# TODO : Serveur HTTP


"""
Classe représentant une requête dans notre système.
Cet objet est le même durant tout le processus.
"""
class Request :
    def __init__ ( self, input_url ) :
        # Une requête est identifiée par son URL de requête, c'est à dire l'URL
        # de l'illustration demandée
        self.input_url = input_url
        
        # Si jamais il y a eu un problème et qu'on ne peut pas traiter la
        # requête, on la met ici
        self.problem = None
        
        # Résultats du Link Finder
        self.twitter_accounts = []
        self.image_url = None
        
        # Résultats de la recherche inversée de l'image
        self.tweets_id = []
        
        # Status du traitement de cette requête :
        # 0 = En attente de traitement par un thread de Link Finder
        # 1 = En cours de traitement par un thread de Link Finder
        #     link_finder_thread_main()
        # 2 = En attente de traitement par un thread de scan de comptes Twitter
        # 3 = En cours de traitement par un thread de scan de comptes Twitter
        #     scan_twitter_account_thread_main()
        # 4 = En attente de traitement par un thread de recherche d'image inversée
        # 5 = En cours de traitement par un thread de recherche d'image inversée
        #     reverse_search_thread_main()
        # 6 = Fin de traitement
        self.status = 0
    
    def set_status_wait_link_finder( self ):
        self.status = 0
    def set_status_link_finder( self ):
        self.status = 1
    def set_status_wait_scan_twitter_account( self ):
        self.status = 2
    def set_status_scan_twitter_account( self ):
        self.status = 3
    def set_status_wait_reverse_search_thread( self ):
        self.status = 4
    def set_status_reverse_search_thread( self ):
        self.status = 5
    def set_status_done( self ):
        self.status = 6


"""
Variables globales, partagées entre les Threads.
"""
# Variable pour éteindre le service
keep_service_alive = True

# Les objets sont passés par adresse en Python
# Donc ils peuvent être en même dans dans la liste "requests" en en même temps
# dans les différentes files d'attente

# De plus, l'objet queue.Queue() est safe pour le multi-threads

# Liste des requêtes effectuées sur notre système
requests = []

# ETAPE 1, code de status de la requête : 1
# File d'attente de Link Finder
link_finder_queue = queue.Queue()

# ETAPE 2, code de status de la requête : 3
# File d'attente de scan de comptes Twitter
scan_twitter_account_queue = queue.Queue()

# ETAPE 3, code de status de la requête : 5
# File d'attente de la recherche d'image inversée
reverse_search_queue = queue.Queue()


"""
ETAPE 1 du traitement d'une requête.
Thread de Link Finder.
"""
def link_finder_thread_main( thread_id : int ) :
    # Initialisation de notre moteur de recherche des comptes Twitter
    finder_engine = Link_Finder()
    
    # Tant que on ne nous dit pas de nous arrêter
    while keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = link_finder_queue.get( block = False )
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
            request.problem = "URL invalide ! Elle ne mène pas à une illustration."
            request.set_status_done()
            
            print( "[link_finder_th" + str(thread_id) + "] URL invalide ! Elle ne mène pas à une illustration." )
            continue
        
        # Si jamais le site n'est pas supporté, on ne va pas plus loin avec
        # cette requête (On passe donc son status à "Fin de traitement")
        elif twitter_accounts == False :
            request.problem = "Site non supporté !"
            request.set_status_done()
            
            print( "[link_finder_th" + str(thread_id) + "] Site non supporté !" )
            continue
        
        # Si jamais aucun compte Twitter n'a été trouvé, on ne va pas plus loin
        # avec la requête (On passe donc son status à "Fin de traitement")
        elif twitter_accounts == []:
            request.problem = "Aucun compte Twitter trouvé pour cet artiste."
            request.set_status_done()
            
            print( "[link_finder_th" + str(thread_id) + "] Aucun compte Twitter trouvé pour l'artiste de cette illustration !" )
            continue
        
        # Stocker les comptes Twitter trouvés
        request.twitter_accounts = twitter_accounts
        
        print( "[link_finder_th" + str(thread_id) + "] Comptes Twitter trouvés pour cet artiste :\n" +
               "[link_finder_th" + str(thread_id) + "] " + str( twitter_accounts ) )
        
        # Théoriquement, on a déjà vérifié que l'URL existe, donc on devrait
        # forcément trouver une image pour cette requête
        request.image_url = finder_engine.get_image_url( request.input_url )
        
        print( "[link_finder_th" + str(thread_id) + "] URL de l'image trouvée :\n" +
               "[link_finder_th" + str(thread_id) + "] " + request.image_url )
        
        # On passe le status de la requête à "En attente de traitement par un
        # thread de scan de comptes Twitter"
        request.set_status_wait_scan_twitter_account()
        
        # On met la requête dans la file d'attente de scan de comptes Twitter
        # Si on est dans le cas d'une procédure complète
        if request in requests :
            scan_twitter_account_queue.put( request )
    
    print( "[link_finder_th" + str(thread_id) + "] Arrêté !" )
    return


"""
ETAPE 2 du traitement d'une requête.
Thread de scan de comptes Twitter.
Ou : Thread d'indexation des tweets d'un compte Twitter.

Note importante : Ce thread doit être unique ! Il ne doit pas être exécuté
plusieurs fois.
En effet, il ne doit pas y avoir deux scans en même temps. Pour deux raisons :
- On pourrait scanner un même compte Twitter en même temps, deux fois donc,
- Et l'API Twitter nous bloque si on fait trop de requêtes.
"""
def scan_twitter_account_thread_main( thread_id : int ) :
    # Initialisation de notre moteur de recherche d'image par le contenu
    cbir_engine = CBIR_Engine_with_Database()
    
    # Tant que on ne nous dit pas de nous arrêter
    while keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = scan_twitter_account_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # On passe le status de la requête à "En cours de traitement par un
        # thread de scan de comptes Twitter"
        request.set_status_scan_twitter_account()
        
        # On scan les comptes Twitter de la requête
        for twitter_account in request.twitter_accounts :
            print( "[scan_twitter_account_th" + str(thread_id) + "] Scan du compte Twitter @" + twitter_account + "." )
            
            cbir_engine.index_or_update_all_account_tweets( twitter_account )
        
        # On passe le status de la requête à "En attente de traitement par un
        # thread de recherche d'image inversée"
        request.set_status_wait_reverse_search_thread()
        
        # On met la requête dans la file d'attente de la recherche d'image inversée
        # Si on est dans le cas d'une procédure complète
        if request in requests :
            reverse_search_queue.put( request )
    
    print( "[scan_twitter_account_th" + str(thread_id) + "] Arrêté !" )
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
            request = reverse_search_queue.get( block = False )
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
            
            request.tweets_id += cbir_engine.search_tweet( request.image_url, twitter_account )
        
        print( "[reverse_search_th" + str(thread_id) + "] Tweets trouvés : " + str( request.tweets_id ) )
        
        # On passe le status de la requête à "Fin de traitement"
        request.set_status_done()
    
    print( "[reverse_search_th" + str(thread_id) + "] Arrêté !" )
    return


"""
Lancement de la procédure pour une URL d'illustration.
@param illust_url L'illustration d'entrée.
"""
def launch_process ( illust_url : str ) :
    request = Request( illust_url )
    requests.append( request ) # Passé par adresse car c'est un objet
    link_finder_queue.put( request ) # Passé par addresse car c'est un objet

"""
Obtenir le status d'une requête.
@param illust_url L'illustration d'entrée.
@return Le numéro du status de la requête (Voir l'objet Request),
        Ou None si la requête est inconnue.
"""
def get_request_status ( illust_url : str ) -> int :
    for request in requests :
        if request.input_url == illust_url :
            return request.status
    return None


"""
Démarrage des threads.
"""
link_finder_thread = threading.Thread( name = "link_finder",
                                       target = link_finder_thread_main,
                                       args = ( 1, ) )
link_finder_thread.start()

scan_twitter_account_thread = threading.Thread( name = "scan_twitter_account",
                                                target = scan_twitter_account_thread_main,
                                                args = ( 1, ) )
scan_twitter_account_thread.start()

reverse_search_thread = threading.Thread( name = "reverse_search",
                                          target = reverse_search_thread_main,
                                          args = ( 1, ) )
reverse_search_thread.start()


"""
Entrée en ligne de commande.
"""
print( "Vous êtes en ligne de commande.")

while True :
    command = input()
    args = command.split(" ")
    
    if args[0] == "request" :
        if len(args) == 2 :
            print( "Lancement de la procédure !" )
            launch_process( args[1] )
        else :
            print( "Utilisation : request [URL de l'illustration]" )
    
    elif args[0] == "status" :
        if len(args) == 2 :
            status = get_request_status( args[1] )
            if status != None :
                print( "Status : " + str(status) )
            else :
                print( "Requête inconnue pour cet URL !" )
        else :
            print( "Utilisation : status [URL de l'illustration]" )
    
    elif args[0] == "scan" :
        if len(args) == 2 :
            # Vérification que le nom d'utilisateur Twitter est possible
            if re.compile("^@?(\w){1,15}$").match(args[1]) :
                print( "Demande de scan du compte @" + args[1] + "." )
                
                # Fabrication de l'objet Request
                request = Request( None )
                request.twitter_accounts = [ args[1] ]
                
                # Lancement du scan
                scan_twitter_account_queue.put( request )
            else :
                print( "Nom de compte Twitter impossible !" )
        else :
            print( "Utilisation : scan [Nom du compte à scanner]" )
    
    elif args[0] == "stop" :
        if len(args) == 1 :
            print( "Arrêt à la fin des procédures en cours..." )
            keep_service_alive = False
            break
        else :
            print( "Utilisation : stop")
    
    elif args[0] == "help" :
        if len(args) == 1 :
            print( "Scanner un compte : scan [Nom du compte à scanner]" )
            print( "Lancer la procédure complète pour un illustration : request [URL de l'illustration]" )
            print( "Voir le status d'une requête : status [URL de l'illustration]" )
            print( "Arrêter le service : stop" )
            print( "Afficher l'aide : help" )
            print( "" )
            print( "Note : Les requêtes sont identifiées par l'URL de l'illustration." )
        else :
            print( "Utilisation : help" )
    
    else :
        print( "Commande inconnue !" )


"""
Arrêt du système.
"""
# Attendre que les threads aient fini
link_finder_thread.join()
scan_twitter_account_thread.join()
reverse_search_thread.join()
