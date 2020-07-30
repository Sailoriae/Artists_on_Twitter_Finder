#!/usr/bin/python3
# coding: utf-8


"""
Classe représentant une requête par un utilisateur. Cet objet est le même
durant tout le processus de traitement.

Une requête est identifiée par son URL de requête, c'est à dire l'URL
de l'illustration demandée.
"""
class User_Request :
    """
    @param input_url L'URL de l'illustration de requête.
    @param ip_address L'adresse IP qui a lancé la requête.
    """
    def __init__ ( self, input_url : str,
                         ip_address : str = None ) :
        self.input_url = input_url
        self.ip_address = ip_address
        
        # Si jamais il y a eu un problème et qu'on ne peut pas traiter la
        # requête, on le met ici sous forme d'une string
        self.problem = None
        
        # Résultat du Link Finder (Etape 1)
        # Image source de l'illustration
        self.image_url = None
        
        # Résultat du Link Finder (Etape 1)
        # Liste de tuples (str, int), avec le nom du compte Twitter, et son ID
        # On est certain que ces comptes existent, c'est le thread de Link Finder
        # qui vérifie
        self.twitter_accounts_with_id = []
        
        # Résultat du Link Finder (Etape 1)
        # Objet datetime de la date de publication de l'image
        self.datetime = None
        
        # Cache de l'indexer (Etape 2)
        # Liste les requêtes de ses comptes dans le système d'indexation / de
        # mise à jour de l'indexation des comptes Twitter (Threads étapes
        # parallèles A, B, C et D, pipeline d'indexation / de scan)
        self.scan_requests = None
        
        # Résultat de la recherche inversée (Etape 3)
        # Résultats de la recherche inversée de l'image
        # Est une liste d'objets Image_in_DB
        self.founded_tweets = []
        
        # ID de l'étape dans laquelle la requête se trouve.
        # 0 : En attente de traitement à l'étape suivante...
        # 1 : En cours de traitement par un thread de Link Finder.
        # 2 : En attente de traitement à l'étape suivante...
        # 3 : En cours de traitement par un thread d'Indexation.
        # 4 : En attente de traitement à l'étape suivante...
        # 5 : En cours de traitement par un thread de recherche inversée.
        # 6 : Fin de traitement.
        self.status = -1
        
        # Date de fin de la procédure
        self.finished_date = None
    
    def get_status_string( self ) :
        if self.status == 0 :
            return "WAIT_LINK_FINDER"
        if self.status == 1 :
            return "LINK_FINDER"
        if self.status == 2 :
            return "WAIT_INDEX_ACCOUNTS_TWEETS"
        if self.status == 3 :
            return "INDEX_ACCOUNTS_TWEETS"
        if self.status == 4 :
            return "WAIT_IMAGE_REVERSE_SEARCH"
        if self.status == 5 :
            return "IMAGE_REVERSE_SEARCH"
        if self.status == 6 :
            return "END"
