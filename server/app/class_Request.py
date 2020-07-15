#!/usr/bin/python3
# coding: utf-8


"""
Classe représentant une requête dans notre système.
Cet objet est le même durant tout le processus de traitement.
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
