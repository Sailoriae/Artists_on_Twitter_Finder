#!/usr/bin/python3
# coding: utf-8

from time import time
from statistics import mean

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendemment (Notemment pour des
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

from tweet_finder.database.class_Image_in_DB import Image_in_DB

CBIR_LIST_LENGHT = 240


# Utiliser des curseurs avec tampon, permet d'accélérer l'itération et la
# recherche, mais consomme plus de mémoire vive
# Fonctionne uniquement en cas de recherche pour un compte Twitter
BUFFERED_CURSOR = False
# Ralentit cependant les temps pour faire les requêtes SQL (SELECT)
# Du coup, ça vaut plus le coup de ne pas utiliser de tampon
# Testé avec @MayoRiyo (Plus de 20.000 images indexées)


# Note :
# Ca ne sert à rien de chercher une optimisation avec fetchmany(). En effet :
# The fetchone() method is used by fetchall() and fetchmany().
# Source :
# https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-fetchone.html


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
        self.ENABLE_METRICS = ENABLE_METRICS
        if ENABLE_METRICS :
            self.select_times = [] # Durées pour faire les SELECT
            self.iteration_times = [] # Durées des itérations
            self.usage_times = [] # Durées des utilisations
            self.usage_start = None
            self.iteration_start = None
            self.start = time()
        
        self.conn = conn
        self.buffered_cursors = account_id != 0 and BUFFERED_CURSOR
        self.current_cursor = self.conn.cursor( buffered = self.buffered_cursors )
        self.current_table = 1
        
        if self.ENABLE_METRICS : start_select = time()
        if account_id != 0 :
            self.current_cursor.execute( request_1, ( account_id, ) )
        else :
            self.current_cursor.execute( request_1 )
        if self.ENABLE_METRICS : self.select_times.append( time() - start_select )
        
        self.account_id = account_id
        self.request_2 = request_2
        self.request_3 = request_3
        self.request_4 = request_4
        
        # Fonction pour enregistrer les temps d'éxécution
        self.add_step_3_times = None

    def __iter__( self ) :
        return self

    """
    @return Un objet Image_in_DB
    """
    def __next__( self, do_not_reset_iteration_start = False ) -> Image_in_DB :
        if self.ENABLE_METRICS :
            if not do_not_reset_iteration_start :
                self.iteration_start = time()
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
                        print( f"[Images_It] Itération sur {len(self.usage_times)} images en {time() - self.start} secondes." )
                        print( f"[Images_It] Temps moyen de requête SQL : {mean(self.select_times)} secondes." )
                        print( f"[Images_It] Temps moyen d'itération : {mean(self.iteration_times)} secondes." )
                        print( f"[Images_It] Temps moyen d'utilisation : {mean(self.usage_times)} secondes." )
                    if self.add_step_3_times != None :
                        self.add_step_3_times( [], self.select_times, self.iteration_times, self.usage_times )
                raise StopIteration
            
            if self.current_table == 2 :
                self.current_cursor = self.conn.cursor( buffered = self.buffered_cursors )
                if self.ENABLE_METRICS : start_select = time()
                if self.account_id != 0 :
                    self.current_cursor.execute( self.request_2, ( self.account_id, ) )
                else :
                    self.current_cursor.execute( self.request_2 )
                if self.ENABLE_METRICS : self.select_times.append( time() - start_select )
            if self.current_table == 3 :
                self.current_cursor = self.conn.cursor( buffered = self.buffered_cursors )
                if self.ENABLE_METRICS : start_select = time()
                if self.account_id != 0 :
                    self.current_cursor.execute( self.request_3, ( self.account_id, ) )
                else :
                    self.current_cursor.execute( self.request_3 )
                if self.ENABLE_METRICS : self.select_times.append( time() - start_select )
            if self.current_table == 4 :
                self.current_cursor = self.conn.cursor( buffered = self.buffered_cursors )
                if self.ENABLE_METRICS : start_select = time()
                if self.account_id != 0 :
                    self.current_cursor.execute( self.request_4, ( self.account_id, ) )
                else :
                    self.current_cursor.execute( self.request_4 )
                if self.ENABLE_METRICS : self.select_times.append( time() - start_select )
            
            return self.__next__( do_not_reset_iteration_start = True )
        
        # Si la liste des caractéristiques est à NULL, on passe cette image
        if current_line[5] == None :
            return self.__next__( do_not_reset_iteration_start = True )
        
        if self.ENABLE_METRICS :
            self.iteration_times.append( time() - self.iteration_start )
            self.usage_start = time()
        
        return Image_in_DB (
                   current_line[0], # ID du compte Twitter
                   current_line[1], # ID du Tweet
                   current_line[4], # Nom de l'image
                   current_line[ 5 : 5+CBIR_LIST_LENGHT ], # Features CBIR de l'image
                   self.current_table
               )
