#!/usr/bin/python3
# coding: utf-8

import Pyro5.server
from time import time


"""
Classe représentant une requête par un utilisateur. Cet objet est le même
durant tout le processus de traitement.

Une requête est identifiée par son URL de requête, c'est à dire l'URL
de l'illustration demandée.

Note : Pour les objets, on stocke en réalité l'URI qui mène à l'objet sur le
serveur Pyro, et pas l'objet directement (Car Pyro ne peut pas exécuter sur le
serveur les méthodes des sous-objets), et pas le Proxy vers l'objet (Car un
Proxy ne peut être utilisé que par un seul thread à la fois).
"""
@Pyro5.server.expose
class User_Request :
    # Type de requête, pour la reconnaitre plus facilement dans le collecteur
    # d'erreurs
    _request_type = "user"
    
    """
    @param input_url L'URL de l'illustration de requête.
    @param ip_address L'adresse IP qui a lancé la requête.
    @param is_direct Mettre à True si cette requête sera placée directement
                     à l'étape de recherche (Etape 3) sans passer par le Link
                     Finder. L'URL doit donc mener directemet à un fichier
                     image, et non à une page d'illustration sur un site
                     supporté.
    @param binary_image Image binaire. L'URL de l'image ne sert alors plus que
                        d'identifiant, et la requête sera une requête directe.
    """
    def __init__ ( self, input_url : str,
                         ip_address : str = None,
                         is_direct : bool = False,
                         binary_image = None ) :
        if binary_image != None :
            self._is_direct = True
        
        self._input_url = input_url
        self._ip_address = ip_address
        self._is_direct = is_direct
        self._binary_image = binary_image
        
        # Si jamais il y a eu un problème et qu'on ne peut pas traiter la
        # requête, on le met ici sous forme d'une string
        self._problem = None
        
        # Résultat du Link Finder (Etape 1)
        # Image source de l'illustration
        self._image_urls = None
        
        # En cas de requête directe où l'URL d'entrée mène à une image
        if is_direct and binary_image == None :
            self._image_urls = [ input_url ]
        
        # Résultat du Link Finder (Etape 1)
        # Liste de tuples (str, int), avec le nom du compte Twitter, et son ID
        # On est certain que ces comptes existent, c'est le thread de Link Finder
        # qui vérifie
        self._twitter_accounts_with_id = []
        
        # Résultat du Link Finder (Etape 1)
        # Objet datetime de la date de publication de l'image
        self._datetime = None
        
        # Cache de l'indexer (Etape 2)
        # Liste les requêtes de ses comptes dans le système d'indexation / de
        # mise à jour de l'indexation des comptes Twitter (Threads étapes
        # parallèles A, B, C et D, pipeline d'indexation / de scan)
        self._scan_requests = None
        
        # Cache de l'indexer (Etape 2)
        # Permet de savoir quand la requête a été vue pour la dernière fois,
        # afin de ne pas trop itérer dessus
        self._last_seen_indexer = 0
        
        # Résultat de l'indexer (Etape 2)
        # Est ce que la requête a des comptes qui sont inconnus de la base de
        # données, et donc vont être indexés pour la première fois
        self._has_first_time_scan = False
        
        # Résultat de la recherche inversée (Etape 3)
        # Résultats de la recherche inversée de l'image
        # Est une liste d'objets Image_in_DB
        self._found_tweets = []
        
        # ID de l'étape dans laquelle la requête se trouve.
        # 0 : En attente de traitement à l'étape suivante...
        # 1 : En cours de traitement par un thread de Link Finder.
        # 2 : En attente de traitement à l'étape suivante...
        # 3 : En cours de traitement par un thread d'Indexation.
        # 4 : En attente de traitement à l'étape suivante...
        # 5 : En cours de traitement par un thread de recherche inversée.
        # 6 : Fin de traitement.
        self._status = -1
        
        # Date de début de la procédure
        self._start = time()
        
        # Date de fin de la procédure
        self._finished_date = None
    
    """
    Getters et setters pour Pyro.
    """
    @property
    def request_type( self ) : return self._request_type
    
    @property
    def input_url( self ) : return self._input_url
    
    @property
    def ip_address( self ) : return self._ip_address
    
    @property
    def is_direct( self ) : return self._is_direct
    
    @property
    def binary_image( self ) : return self._binary_image
    
    @property
    def problem( self ) : return self._problem
    @problem.setter
    def problem( self, value ) : self._problem = value
    
    @property
    def image_urls( self ) : return self._image_urls
    @image_urls.setter
    def image_urls( self, value ) : self._image_urls = value
    
    @property
    def twitter_accounts_with_id( self ) : return self._twitter_accounts_with_id
    @twitter_accounts_with_id.setter
    def twitter_accounts_with_id( self, value ) : self._twitter_accounts_with_id = value
    
    @property
    def datetime( self ) : return self._datetime
    @datetime.setter
    def datetime( self, value ) : self._datetime = value
    
    @property
    def scan_requests( self ) : return self._scan_requests
    @scan_requests.setter
    def scan_requests( self, value ) : self._scan_requests = value
    
    @property
    def last_seen_indexer( self ) : return self._last_seen_indexer
    @last_seen_indexer.setter
    def last_seen_indexer( self, value ) : self._last_seen_indexer = value
    
    @property
    def has_first_time_scan( self ) : return self._has_first_time_scan
    @has_first_time_scan.setter
    def has_first_time_scan( self, value ) : self._has_first_time_scan = value
    
    @property
    def found_tweets( self ) : return self._found_tweets
    @found_tweets.setter
    def found_tweets( self, value ) : self._found_tweets = value
    
    @property
    def status( self ) : return self._status
    @status.setter
    def status( self, value ) : self._status = value
    
    @property
    def start( self ) : return self._start
    
    @property
    def finished_date( self ) : return self._finished_date
    @finished_date.setter
    def finished_date( self, value ) : self._finished_date = value
    
    def get_status_string( self ) :
        if self._status == 0 :
            return "WAIT_LINK_FINDER"
        if self._status == 1 :
            return "LINK_FINDER"
        if self._status == 2 :
            return "WAIT_INDEX_ACCOUNTS_TWEETS"
        if self._status == 3 :
            return "INDEX_ACCOUNTS_TWEETS"
        if self._status == 4 :
            return "WAIT_IMAGE_REVERSE_SEARCH"
        if self._status == 5 :
            return "IMAGE_REVERSE_SEARCH"
        if self._status == 6 :
            return "END"
