#!/usr/bin/python3
# coding: utf-8

from datetime import datetime


"""
Classe représentant une requête dans notre système.
Cet objet est le même durant tout le processus de traitement.

SEUL L'OBJET PIPELINE DOIT POUVOIR INSTANCIER CETTE CLASSE !
Car c'est elle qui gère toutes les requêtes.
"""
class Request :
    """
    @param input_url URL de l'illustration de requête.
    @param pipeline L'objet Pipeline, mémoire partagée.
    """
    def __init__ ( self, input_url,
                         pipeline,
                         do_link_finder = False,
                         do_indexing = False,
                         do_reverse_search = False,
                         ip_address = None ) :
        # Est ce que la requête doit faire l'étape 1, c'est à dire passer dans
        # le "thread_step_1_link_finder"
        self.do_link_finder = do_link_finder
        
        # Est ce que cette requête doit faire les étapes 2, 3 et 4, c'est à
        # dire passer dans les 3 threads suivants :
        # - "thread_step_2_GOT3_list_account_tweets"
        # - "thread_step_3_GOT3_index_account_tweets"
        # - "thread_step_4_TwitterAPI_index_account_tweets"
        self.do_indexing = do_indexing
        
        # Est ce que cette requête doit faire l'étape 5, c'est à dire passer
        # dans le thread "thread_step_5_reverse_search"
        self.do_reverse_search = do_reverse_search
        
        
        # Addresse IP qui a lancé la requête
        self.ip_address = ip_address
        
        # Objet de mémoire partagée
        self.pipeline = pipeline
        
        
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
        #     thread_step_1_link_finder()
        #
        # 2 = En attente de traitement par un thread de listage des tweet
        #     d'un compte Twitter avec GetOldTweets3
        # 3 = En cours de traitement par un thread de listage des tweets d'un
        #     compte Twitter avec GetOldTweets3
        #     thread_step_2_GOT3_list_account_tweets()
        #
        # 4 = En attente de traitement par un thread d'indexation des tweet
        #     d'un compte Twitter avec GetOldTweets3
        # 5 = En cours de traitement par un thread d'indexation des tweets d'un
        #     compte Twitter avec GetOldTweets3
        #     thread_step_3_GOT3_index_account_tweets()
        #
        # 6 = En attente de traitement par un thread d'indexation des tweet
        #     d'un compte Twitter avec l'API Twitter publique
        # 7 = En cours de traitement par un thread d'indexation des tweets d'un
        #     compte Twitter avec l'API Twitter publique
        #     thread_step_4_TwitterAPI_index_account_tweets()
        #
        # 8 = En attente de traitement par un thread de recherche d'image inversée
        # 9 = En cours de traitement par un thread de recherche d'image inversée
        #     thread_step_5_reverse_search()
        #
        # 10 = Fin de traitement
        if do_link_finder :
            self.status = 0
        elif do_indexing :
            self.status = 3
        elif do_reverse_search :
            self.status = 9
        
        
        # Date de fin de la procédure, c'est à dire d'appel de la méthode
        # set_status_done
        self.finished_date = None
    
    def set_status_done( self ) :
        self.status = 10
        self.finished_date = datetime.now()
        if self.ip_address != None :
            self.pipeline.remove_ip_address( self.ip_address )
    
    def get_status_string( self ) :
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
            return "WAIT_SECOND_INDEX_ACCOUNT_TWEETS"
        if self.status == 7 :
            return "SECOND_INDEX_ACCOUNT_TWEETS"
        if self.status == 8 :
            return "WAIT_IMAGE_REVERSE_SEARCH"
        if self.status == 9 :
            return "IMAGE_REVERSE_SEARCH"
        if self.status == 10 :
            return "END"
