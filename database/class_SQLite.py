#!/usr/bin/python3
# coding: utf-8

import sqlite3
from typing import List
from datetime import datetime

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
        c.execute( "CREATE TABLE IF NOT EXISTS tweets ( account_id INTEGER, tweet_id INTEGER PRIMARY KEY, image_1_features TEXT, image_2_features TEXT, image_3_features TEXT, image_4_features TEXT, hashtags TEXT )" )
        c.execute( "CREATE TABLE IF NOT EXISTS accounts ( account_id INTEGER PRIMARY KEY, last_GOT3_indexing_api_date STRING, last_GOT3_indexing_local_date TIMESTAMP )" )
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
    @param cbir_features_1 La liste des caractéristiques issues de l'analyse
                           CBIR pour la première image du Tweet
    @param cbir_features_2 La liste des caractéristiques issues de l'analyse
                           CBIR pour la seconde image du Tweet
                           (OPTIONNEL)
    @param cbir_features_3 La liste des caractéristiques issues de l'analyse
                           CBIR pour la troisième image du Tweet
                           (OPTIONNEL)
    @param cbir_features_4 La liste des caractéristiques issues de l'analyse
                           CBIR pour la quatrième image du Tweet
                           (OPTIONNEL)
    @param hashtags La liste des hashtags du Tweet (OPTIONNEL)
    """
    def insert_tweet( self, account_id : int, tweet_id : int,
                      cbir_features_1 : List[float],
                      cbir_features_2 : List[float] = None,
                      cbir_features_3 : List[float] = None,
                      cbir_features_4 : List[float] = None,
                      hashtags : List[str] = None ) :
        c = self.conn.cursor()
        
        cbir_features_1_str = ";".join( [ str( value ) for value in cbir_features_1 ] )
        
        if cbir_features_2 != None :
            cbir_features_2_str = ";".join( [ str( value ) for value in cbir_features_2 ] )
        else :
            cbir_features_2_str = None
        
        if cbir_features_3 != None :
            cbir_features_3_str = ";".join( [ str( value ) for value in cbir_features_3 ] )
        else :
            cbir_features_3_str = None
        
        if cbir_features_4 != None :
            cbir_features_4_str = ";".join( [ str( value ) for value in cbir_features_4 ] )
        else :
            cbir_features_4_str = None
        
        if hashtags != None and hashtags != [] :
            hashtags_str = ";".join( [ hashtag for hashtag in hashtags ] )
        else :
            hashtags_str = None
        
        c.execute( """INSERT INTO tweets VALUES ( ?, ?, ?, ?, ?, ?, ? )
                      ON CONFLICT ( tweet_id ) DO NOTHING """, # Si le tweet est déjà stocké, on ne fait rien
                   ( account_id,
                     tweet_id,
                     cbir_features_1_str,
                     cbir_features_2_str,
                     cbir_features_3_str,
                     cbir_features_4_str,
                     hashtags_str,) )
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
            c.execute( "SELECT account_id, tweet_id, image_1_features, image_2_features, image_3_features, image_4_features FROM tweets WHERE account_id = ?",
                       ( account_id, ) )
        else :
            c.execute( "SELECT account_id, tweet_id, image_1_features, image_2_features, image_3_features, image_4_features FROM tweets" )
        
        return SQLite_Image_Features_Iterator( c )
    
    """
    Stocker la date du dernier scan d'un compte Twitter
    Si le compte Twitter est déjà dans la base de données, sa date de dernier
    scan sera mise à jour
    
    @param account_id ID du compte Twitter
    @param last_scan Date du dernier scan, au format YYYY-MM-DD
    """
    def set_account_last_scan( self, account_id : int, last_update : str ) :
        now = datetime.now()
        c = self.conn.cursor()
        c.execute( """INSERT INTO accounts VALUES ( ?, ?, ? )
                      ON CONFLICT ( account_id ) DO UPDATE SET last_GOT3_indexing_api_date = ?, last_GOT3_indexing_local_date = ?""",
                   ( account_id, last_update, now, last_update, now ) )
        self.conn.commit()
    
    """
    Récupérer la date du dernier scan d'un compte Twitter
    @param account_id ID du compte Twitter
    @return Date du dernier scan, au format YYYY-MM-DD
            Ou None si le compte est inconnu
    """
    def get_account_last_scan( self, account_id : int ) -> str :
        c = self.conn.cursor()
        c.execute( "SELECT last_GOT3_indexing_api_date FROM accounts WHERE account_id = ?",
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
    Savoir si un Tweet est déjà indexé ou non
    @param tweet_id L'ID du tweet
    @return True ou False
    """
    def is_tweet_indexed( self, tweet_id : int ) -> bool :
        c = self.conn.cursor()
        c.execute( "SELECT * FROM tweets WHERE tweet_id = ?", ( tweet_id, ) )
        return c.fetchone() != None


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
