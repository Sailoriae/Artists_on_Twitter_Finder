#!/usr/bin/python3
# coding: utf-8

from time import time
from statistics import mean

try :
    from class_Image_in_DB import Image_in_DB
    from sql_requests_dict import sql_requests_dict
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .class_Image_in_DB import Image_in_DB
    from .sql_requests_dict import sql_requests_dict

CBIR_LIST_LENGHT = 240


"""
Itérateur sur les images de Tweets contenues dans la base de données.

Cet objet doit uniquement être instancié par la méthode
"get_images_in_db_iterator()" de la classe "SQLite_or_MySQL" contenue dans le
fichier "class_SQLite_or_MySQL.py".
"""
class Image_Features_Iterator :
    """
    Pourquoi passer la connexion et pas les curseurs ?
    Parce que : For nonbuffered cursors, rows are not fetched from the server
    until a row-fetching method is called. In this case, you must be sure to
    fetch all rows of the result set before executing any other statements on
    the same connection, or an InternalError (Unread result found) exception
    will be raised.
    Source :
    https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursorbuffered.html
    
    @param conn Connexion à la BDD SQL.
    """
    def __init__( self, conn,
                        account_id,
                        request_1,
                        request_2,
                        request_3,
                        request_4,
                        ENABLE_METRICS = False ) :
        self.conn = conn
        self.current_cursor = self.conn.cursor()
        self.current_table = 1
        
        if account_id != 0 :
            self.current_cursor.execute( request_1, ( account_id, ) )
        else :
            self.current_cursor.execute( request_1 )
        
        self.account_id = account_id
        self.request_2 = request_2
        self.request_3 = request_3
        self.request_4 = request_4
        
        self.ENABLE_METRICS = ENABLE_METRICS
        if ENABLE_METRICS :
            self.iteration_times = [] # Durées des itérations
            self.usage_times = [] # Durées des utilisations
            self.usage_start = None
        
        # Fonction pour enregistrer les temps d'éxécution
        self.add_step_3_times = None

    def __iter__( self ) :
        return self

    """
    @return Un objet Image_in_DB
    """
    def __next__( self ) -> Image_in_DB :
        if self.ENABLE_METRICS :
            iteration_start = time()
            if self.usage_start != None :
                self.usage_times.append( time() - self.usage_start )
        
        # On prend une nouvelle ligne dans la table
        current_line = self.current_cursor.fetchone()
        
        # Si cette ligne est vide, c'est qu'on est au bout de la table, donc on
        # passe à la table suivante
        if current_line == None :
            self.current_table += 1
            
            # Si on a fait les 4 tables, on termine l'itération
            if self.current_table == 5 :
                if self.ENABLE_METRICS :
                    if self.iteration_times != [] and self.usage_times != [] :
                        print( "[Images_It] Temps moyen d'itération :", mean( self.iteration_times ) )
                        print( "[Images_It] Temps moyen d'utilisation :", mean( self.usage_times ) )
                    if self.add_step_3_times != None :
                        self.add_step_3_times( self.iteration_times, self.usage_times )
                raise StopIteration
            
            if self.current_table == 2 :
                self.current_cursor = self.conn.cursor()
                if self.account_id != 0 :
                    self.current_cursor.execute( self.request_2, ( self.account_id, ) )
                else :
                    self.current_cursor.execute( self.request_2 )
            if self.current_table == 3 :
                self.current_cursor = self.conn.cursor()
                if self.account_id != 0 :
                    self.current_cursor.execute( self.request_2, ( self.account_id, ) )
                else :
                    self.current_cursor.execute( self.request_2 )
            if self.current_table == 4 :
                self.current_cursor = self.conn.cursor()
                if self.account_id != 0 :
                    self.current_cursor.execute( self.request_2, ( self.account_id, ) )
                else :
                    self.current_cursor.execute( self.request_2 )
            
            return self.__next__()
        
        if self.ENABLE_METRICS :
            self.iteration_times.append( time() - iteration_start )
            self.usage_start = time()
        
        return Image_in_DB (
                   current_line[0], # ID du compte Twitter
                   current_line[1], # ID du Tweet
                   current_line[ 4 : 4+CBIR_LIST_LENGHT ], # Features CBIR de l'image
                   self.current_table
               )
