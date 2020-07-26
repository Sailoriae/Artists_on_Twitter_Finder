#!/usr/bin/python3
# coding: utf-8


"""
Classe représentant une indexation (Nouvelle ou mise à jour) d'un ID de compte
Twitter dans la base de données. Cet objet est le même durant tout le processus
de traitement.

Une requête est identifiée par l'ID du compte Twitter.
"""
class Scan_Request :
    """
    @param account_id L'ID du compte Twitter à indexer / scanner. Ne sert qu'à
                      identifier.
    @param acount_name Le nom du compte Twitter à indexer / scanner. Attention,
                       c'est lui qui est revérifié et scanné !
    @param is_prioritary Est ce que cette requête est prioritaire ?
    """
    def __init__ ( self, account_id : int,
                         acount_name : str,
                         is_prioritary : bool = False ) :
        self.account_id = account_id
        self.account_name = acount_name
        self.is_prioritary = is_prioritary
        
        # Si jamais un thread de traitement a planté avec la requête, le
        # collecteur d'erreur l'indiquera ici
        self.has_failed = False
        
        # ID de l'étape dans laquelle la requête se trouve.
        # 0 : En attente de traitement à l'étape suivante...
        # 1 : En cours de traitement par un thread de Listage des Tweets avec
        #     GetOldTweets3.
        # 2 : En attente de traitement à l'étape suivante...
        # 3 : En cours de traitement par un thread d'Indexation des Tweets avec
        #     GetOldTweets3.
        # 4 : En attente de traitement à l'étape suivante...
        # 5 : En cours de traitement par un thread d'Indexation des Tweets avec
        #     l'API Twitter publique.
        # 6 : Fin de traitement.
        self.status = -1
        
        # Attribut pour annuler cette requête lorsqu'elle sortira d'une file
        # d'attente. Utilisé afin de passer la requête en prioritaire.
        self.is_cancelled = False
        
        # Résultats de la fonction get_GOT3_list() de la classe
        # CBIR_Engine_with_Database. A VIDER UNE FOIS UTILISE, CAR C'EST LOURD
        # EN MEMOIRE !
        self.get_GOT3_list_result = None
        
        # Date de fin de la procédure
        self.finished_date = None
