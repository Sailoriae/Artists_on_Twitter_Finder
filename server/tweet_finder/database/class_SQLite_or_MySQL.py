#!/usr/bin/python3
# coding: utf-8

from typing import List
from datetime import datetime

try :
    from class_Image_Features_Iterator import Image_Features_Iterator
    from class_Less_Recently_Updated_Accounts_Iterator import Less_Recently_Updated_Accounts_Iterator
    from features_list_for_db import features_list_for_db
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .class_Image_Features_Iterator import Image_Features_Iterator
    from .class_Less_Recently_Updated_Accounts_Iterator import Less_Recently_Updated_Accounts_Iterator
    from .features_list_for_db import features_list_for_db

# Ajouter le répertoire parent du parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

import parameters as param

if param.USE_MYSQL_INSTEAD_OF_SQLITE :
    import mysql.connector
else :
    import sqlite3

# Nombre de valeurs dans la liste renvoyée par le moteur CBIR
# SI CE PARAMETRE EST CHANGE, IL FAUT RESET LA BASE DE DONNEES !
CBIR_LIST_LENGHT = 240


"""
Couche d'abstraction à la base de données SQLite.

Une liste est stockée sous forme d'une chaine de caractéres.
Le séparateur des élément est le caractère ';'.
"""
class SQLite_or_MySQL :
    """
    Constructeur
    """
    def __init__( self ) :
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            self.conn = mysql.connector.connect(
                host = param.MYSQL_ADDRESS,
                port = param.MYSQL_PORT,
                user = param.MYSQL_USERNAME,
                password = param.MYSQL_PASSWORD,
                database = param.MYSQL_DATABASE_NAME
            )
        else :
            self.conn = sqlite3.connect(
                param.SQLITE_DATABASE_NAME,
            )
        
        c = self.conn.cursor()
        
        tweets_table = """CREATE TABLE IF NOT EXISTS tweets (
                              account_id UNSIGNED BIGINT,
                              tweet_id UNSIGNED BIGINT PRIMARY KEY,
                              hashtags VARCHAR,"""
        
        # On stocker les listes de caractéristiques sur plusieurs colonnes
        # Cf. moteur CBIR, listes de 240 valeurs
        # Comme le moteur CBIR renvoit des listes de numpy.float32, c'est à
        # des floats sur 32 bits, on a besoin que de 4 octets pour les stocker,
        # donc les REAL qui prennent 4 octets
        for image_id in range(1, 5) : # 4 images max dans un Tweet, numérotées de 1 à 4
            for feature_id in range( 0, CBIR_LIST_LENGHT ) : # 240 valeurs à stocker
                tweets_table += " image_" + str(image_id) + "_feature_" + str(feature_id) + " UNSIGNED REAL,"
        
        tweets_table = tweets_table[:-1] # Suppression de la virgule finale
        tweets_table += " )"
        
        c.execute( tweets_table )
        
        account_table = """CREATE TABLE IF NOT EXISTS accounts (
                               account_id UNSIGNED BIGINT PRIMARY KEY,
                               last_GOT3_indexing_api_date CHAR(10),
                               last_GOT3_indexing_local_date DATETIME,
                               last_TwitterAPI_indexing_tweet_id UNSIGNED BIGINT,
                               last_TwitterAPI_indexing_local_date DATETIME )"""
        c.execute( account_table )
        
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
                           240 VALEURS MAXIMUM
    @param cbir_features_2 La liste des caractéristiques issues de l'analyse
                           CBIR pour la seconde image du Tweet
                           240 VALEURS MAXIMUM
                           (OPTIONNEL)
    @param cbir_features_3 La liste des caractéristiques issues de l'analyse
                           CBIR pour la troisième image du Tweet
                           240 VALEURS MAXIMUM
                           (OPTIONNEL)
    @param cbir_features_4 La liste des caractéristiques issues de l'analyse
                           CBIR pour la quatrième image du Tweet
                           240 VALEURS MAXIMUM
                           (OPTIONNEL)                    
    @param hashtags La liste des hashtags du Tweet (OPTIONNEL)
    """
    def insert_tweet( self, account_id : int, tweet_id : int,
                      cbir_features_1 : List[float],
                      cbir_features_2 : List[float] = None,
                      cbir_features_3 : List[float] = None,
                      cbir_features_4 : List[float] = None,
                      hashtags : List[str] = None ) :
        if self.is_tweet_indexed( tweet_id ) :
            return
        
        c = self.conn.cursor()
        
        cbir_features_1_formatted = features_list_for_db( cbir_features_1 )
        
        if cbir_features_2 != None :
            cbir_features_2_formatted = features_list_for_db( cbir_features_2 )
        else :
            cbir_features_2_formatted = features_list_for_db( [] )
        
        if cbir_features_3 != None :
            cbir_features_3_formatted = features_list_for_db( cbir_features_3 )
        else :
            cbir_features_3_formatted = features_list_for_db( [] )
        
        if cbir_features_4 != None :
            cbir_features_4_formatted = features_list_for_db( cbir_features_4  )
        else :
            cbir_features_4_formatted = features_list_for_db( [] )
        
        if hashtags != None and hashtags != [] and hashtags != [""] :
            hashtags_str = ";".join( [ hashtag for hashtag in hashtags ] )
        else :
            hashtags_str = None
        
        request = "INSERT INTO tweets VALUES ( ?, ?, ?," + " ?," * CBIR_LIST_LENGHT * 4
        request = request[:-1] # Suppression de la virgule finale
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = request.replace( "?", "%s" )
            request += " ) ON DUPLICATE KEY UPDATE tweets.tweet_id = tweets.tweet_id"
        else :
            request += " ) ON CONFLICT ( tweet_id ) DO NOTHING"
        
        to_insert = tuple( [ account_id,
                            tweet_id,
                            hashtags_str ]
                           + cbir_features_1_formatted
                           + cbir_features_2_formatted
                           + cbir_features_3_formatted
                           + cbir_features_4_formatted )
        
        c.execute( request, to_insert )
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
            request = "SELECT * FROM tweets WHERE account_id = ?"
            
            if param.USE_MYSQL_INSTEAD_OF_SQLITE :
                request = request.replace( "?", "%s" )
            
            c.execute( request,
                       ( account_id, ) )
        else :
            request = "SELECT * FROM tweets"
            
            c.execute( request )
        
        return Image_Features_Iterator( c )
    
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
        
        request = """INSERT INTO accounts ( account_id, last_GOT3_indexing_api_date, last_GOT3_indexing_local_date ) VALUES ( ?, ?, ? )
                     ON CONFLICT ( account_id ) DO UPDATE SET last_GOT3_indexing_api_date = ?, last_GOT3_indexing_local_date = ?"""
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = """INSERT INTO accounts ( account_id, last_GOT3_indexing_api_date, last_GOT3_indexing_local_date ) VALUES ( %s, %s, %s )
                         ON DUPLICATE KEY UPDATE last_GOT3_indexing_api_date = %s, last_GOT3_indexing_local_date = %s"""
        
        c.execute( request,
                   ( account_id, last_update, now.strftime('%Y-%m-%d %H:%M:%S'), last_update, now.strftime('%Y-%m-%d %H:%M:%S') ) )
        self.conn.commit()
    
    """
    Stocker l'ID du Tweet le plus récent scanné d'un compte Twitter, via l'API
    publique de Twitter
    Si le compte Twitter est déjà dans la base de données, sa date de dernier
    scan sera mise à jour
    
    @param account_id ID du compte Twitter
    @param tweet_id ID du Tweet scanné le plus récent
    """
    def set_account_last_scan_with_TwitterAPI( self, account_id : int, tweet_id : int ) :
        now = datetime.now()
        c = self.conn.cursor()
        
        request = """INSERT INTO accounts ( account_id, last_TwitterAPI_indexing_tweet_id, last_TwitterAPI_indexing_local_date ) VALUES ( ?, ?, ? )
                     ON CONFLICT ( account_id ) DO UPDATE SET last_TwitterAPI_indexing_tweet_id = ?, last_TwitterAPI_indexing_local_date = ?"""
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = """INSERT INTO accounts ( account_id, last_TwitterAPI_indexing_tweet_id, last_TwitterAPI_indexing_local_date ) VALUES ( %s, %s, %s )
                         ON DUPLICATE KEY UPDATE last_TwitterAPI_indexing_tweet_id = %s, last_TwitterAPI_indexing_local_date = %s"""
        
        c.execute( request,
                   ( account_id, tweet_id, now.strftime('%Y-%m-%d %H:%M:%S'), tweet_id, now.strftime('%Y-%m-%d %H:%M:%S') ) )
        self.conn.commit()
    
    """
    Récupérer la date du dernier scan d'un compte Twitter
    @param account_id ID du compte Twitter
    @return Date du dernier scan, au format YYYY-MM-DD
            Ou None si le compte est inconnu
    """
    def get_account_last_scan( self, account_id : int ) -> str :
        c = self.conn.cursor()
        
        request = "SELECT last_GOT3_indexing_api_date FROM accounts WHERE account_id = ?"
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = request.replace( "?", "%s" )
        
        c.execute( request,
                   ( account_id, ) )
        last_scan = c.fetchone()
        if last_scan != None :
            return last_scan[0]
        else :
            return None
    
    """
    Récupérer l'ID du dernier Tweet scanné avec l'API Twitter, associé à la
    date locale de ce dernier scan.
    
    @param account_id ID du compte Twitter
    @return L'ID du dernier Tweet scanné
            Ou None si le compte est inconnu
    """
    def get_account_last_scan_with_TwitterAPI( self, account_id : int ) -> int :
        c = self.conn.cursor()
        
        request = "SELECT last_TwitterAPI_indexing_tweet_id FROM accounts WHERE account_id = ?"
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = request.replace( "?", "%s" )
        
        c.execute( request,
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
        
        request = "SELECT tweet_id FROM tweets WHERE tweet_id = ?"
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = request.replace( "?", "%s" )
        
        c.execute( request, ( tweet_id, ) )
        return c.fetchone() != None
    
    """
    Savoir si un compte Twitter est dans la base de données ou non
    @param account_id L'ID du compte Twitter
    @return True ou False
    """
    def is_account_indexed( self, account_id : int ) -> bool :
        c = self.conn.cursor()
        
        request = "SELECT account_id FROM accounts WHERE account_id = ?"
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = request.replace( "?", "%s" )
        
        c.execute( request, ( account_id, ) )
        return c.fetchone() != None
    
    """
    Retourner un itérateur sur les IDs des comptes Twitter dans la base données,
    triés dans l'ordre du moins récemment mise à jour au plus récemment mis à
    jour.
    La date de mise à jour la plus vielle est calculée avec la valeur minimum
    de la date du dernier scan avec GetOldTweets3 et du dernier scan avec l'API
    Twitter publique.
    
    @return Un itérateur sur le résultat
            Voir le fichier "class_Less_Recently_Updated_Accounts_Iterator.py"
    """
    def get_oldest_updated_account( self ) -> int :
        c = self.conn.cursor()
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            # Le "ORDER BY LEAST()" considère bien la valeur NULL comme
            # inférieure à toutes les autres valeurs, et la place en tête.
            # C'est parfait pour nous !
            c.execute( """SELECT account_id, last_GOT3_indexing_local_date, last_TwitterAPI_indexing_local_date
                          FROM accounts
                          ORDER BY LEAST( last_GOT3_indexing_local_date,
                                          last_TwitterAPI_indexing_local_date ) ASC""" )
        else :
            c.execute( """SELECT account_id, last_GOT3_indexing_local_date, last_TwitterAPI_indexing_local_date
                          FROM accounts
                          ORDER BY MIN( last_GOT3_indexing_local_date,
                                        last_TwitterAPI_indexing_local_date ) ASC""" )
        return Less_Recently_Updated_Accounts_Iterator( c )

"""
Test du bon fonctionnement de cette classe
"""
if __name__ == '__main__' :
    bdd = SQLite_or_MySQL()
    bdd.insert_tweet( 12, 42, [0.0000000001, 1000000000] )
    bdd.insert_tweet( 12, 42, [10.01, 1.1] )
    bdd.get_images_in_db_iterator( 12 )
    
    bdd.set_account_last_scan( 12, "2020-07-02" )
    bdd.get_account_last_scan( 13 )
    
    bdd.conn.close()
