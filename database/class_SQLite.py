#!/usr/bin/python3
# coding: utf-8

import sqlite3
from typing import List

try :
    from class_SQLite_Image_Features_Iterator import SQLite_Image_Features_Iterator
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .class_SQLite_Image_Features_Iterator import SQLite_Image_Features_Iterator


"""
Couche d'abstraction à la base de données SQLite.

Une liste est stockée sous forme d'une chaine de caractéres.
Le séparateur des élément est le caractère ';'.
"""
class SQLite :
    """
    Constructeur
    """
    def __init__( self, database_name : str ) :
        self.conn = sqlite3.connect( database_name )
        
        c = self.conn.cursor()
        c.execute( "CREATE TABLE IF NOT EXISTS tweets ( account_id INTEGER, tweet_id INTEGER, image_features TEXT )" )
        c.execute( "CREATE TABLE IF NOT EXISTS accounts ( account_id INTEGER PRIMARY KEY, last_scan STRING )" )
        self.conn.commit()
    
    """
    Destructeur
    """
    def __del__( self ) :
        self.conn.close()
    
    """
    Ajouter un tweet à la base de données
    @param account_id L'ID du compte associé au tweet
    @param tweet_id L'ID du tweet à ajouter
    @param cbir_features La liste des caractéristiques issues de l'analyse CBIR
    """
    def insert_tweet( self, account_id : int, tweet_id : int, cbir_features : List[float] ) :
        c = self.conn.cursor()
        c.execute( "INSERT INTO tweets VALUES ( ?, ?, ? )",
                   ( account_id,
                     tweet_id,
                     ";".join( [ str( value ) for value in cbir_features ] ) , ) )
        self.conn.commit()
    
    """
    Récupérer les résultats CBIR de toutes les images d'un compte Twitter, ou
    de toutes les images dans la base de données.
    @param account_id L'ID du compte Twitter (OPTIONNEL)
    @return Un itérateur sur le résultat
            Voir le fichier "class_SQLite_Image_Features_Iterator.py"
    """
    def get_images_in_db_iterator( self, account_id : int = 0 ) :
        c = self.conn.cursor()
        
        if account_id != 0 :
            c.execute( "SELECT account_id, tweet_id, image_features FROM tweets WHERE account_id = ?",
                       ( account_id, ) )
        else :
            c.execute( "SELECT account_id, tweet_id, image_features FROM tweets" )
        
        return SQLite_Image_Features_Iterator( c )
    
    """
    Stocker la date du dernier scan d'un compte Twitter
    Si le compte Twitter est déjà dans la base de données, sa date de dernier
    scan sera mise à jour
    
    @param account_id ID du compte Twitter
    @param last_scan Date du dernier scan, au format YYYY-MM-DD
    """
    def set_account_last_scan( self, account_id : int, last_update : str ) :
        c = self.conn.cursor()
        c.execute( """INSERT INTO accounts VALUES ( ?, ? )
                      ON CONFLICT ( account_id ) DO UPDATE SET last_scan = ?""",
                   ( account_id, last_update, last_update, ) )
        self.conn.commit()
    
    """
    Récupérer la date du dernier scan d'un compte Twitter
    @param account_id ID du compte Twitter
    @return Date du dernier scan, au format YYYY-MM-DD
            Ou None si le compte est inconnu
    """
    def get_account_last_scan( self, account_id : int ) -> str :
        c = self.conn.cursor()
        c.execute( "SELECT last_scan FROM accounts WHERE account_id = ?",
                   ( account_id, ) )
        last_scan = c.fetchone()
        if last_scan != None :
            return last_scan[0]
        else :
            return None
    
    """
    Obtenir des statistiques sur la base de données
    @return Une liste contenant, dans l'ordre suivant :
            - Le nombre de tweets indexés
            - Le nombre de comptes indexés
    """
    def get_stats( self ) :
        c = self.conn.cursor()
        c.execute( "SELECT COUNT( * ) FROM tweets" )
        count_tweets = c.fetchone()[0]
        c.execute( "SELECT COUNT( * ) FROM accounts" )
        count_accounts = c.fetchone()[0]
        return [ count_tweets, count_accounts ]


"""
Test du bon fonctionnement de cette classe
"""
if __name__ == '__main__' :
    bdd = SQLite( "Test_SQLite_Database.db" )
    bdd.insert_tweet( 12, 42, [0.0000000001, 1000000000] )
    bdd.insert_tweet( 12, 42, [10.01, 1.1] )
    bdd.get_images_in_db_iterator( 12 )
    
    bdd.set_account_last_scan( 12, "2020-07-02" )
    bdd.get_account_last_scan( 13 )
    
    bdd.conn.close()
