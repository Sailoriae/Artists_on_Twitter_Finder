#!/usr/bin/python3
# coding: utf-8

from typing import List
from datetime import datetime

try :
    from class_Image_Features_Iterator import Image_Features_Iterator
    from class_Less_Recently_Updated_Accounts_Iterator import Less_Recently_Updated_Accounts_Iterator
#    from features_list_for_db import features_list_for_db
    from sql_requests_dict import sql_requests_dict
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .class_Image_Features_Iterator import Image_Features_Iterator
    from .class_Less_Recently_Updated_Accounts_Iterator import Less_Recently_Updated_Accounts_Iterator
#    from .features_list_for_db import features_list_for_db
    from .sql_requests_dict import sql_requests_dict

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
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            tweets_table = """CREATE TABLE IF NOT EXISTS tweets (
                                  account_id BIGINT UNSIGNED,
                                  tweet_id BIGINT UNSIGNED PRIMARY KEY,
                                  hashtags TEXT )"""
            
            tweets_images_1_table = """CREATE TABLE IF NOT EXISTS tweets_images_1 (
                                           tweet_id BIGINT UNSIGNED PRIMARY KEY,
                                           image_name TEXT,"""
            tweets_images_2_table = """CREATE TABLE IF NOT EXISTS tweets_images_2 (
                                           tweet_id BIGINT UNSIGNED PRIMARY KEY,
                                           image_name TEXT,"""
            tweets_images_3_table = """CREATE TABLE IF NOT EXISTS tweets_images_3 (
                                           tweet_id BIGINT UNSIGNED PRIMARY KEY,
                                           image_name TEXT,"""
            tweets_images_4_table = """CREATE TABLE IF NOT EXISTS tweets_images_4 (
                                           tweet_id BIGINT UNSIGNED PRIMARY KEY,
                                           image_name TEXT,"""
            
            # On stocker les listes de caractéristiques sur plusieurs colonnes
            # Cf. moteur CBIR, listes de 240 valeurs
            # Comme le moteur CBIR renvoit des listes de numpy.float32, c'est à
            # des floats sur 32 bits, on a besoin que de 4 octets pour les stocker,
            # donc les FLOAT qui prennent 4 octets
            for feature_id in range( 0, CBIR_LIST_LENGHT ) : # 240 valeurs à stocker
                tweets_images_1_table += " image_1_feature_" + str(feature_id) + " FLOAT UNSIGNED,"
                tweets_images_2_table += " image_2_feature_" + str(feature_id) + " FLOAT UNSIGNED,"
                tweets_images_3_table += " image_3_feature_" + str(feature_id) + " FLOAT UNSIGNED,"
                tweets_images_4_table += " image_4_feature_" + str(feature_id) + " FLOAT UNSIGNED,"
        
        else :
            tweets_table = """CREATE TABLE IF NOT EXISTS tweets (
                                  account_id UNSIGNED BIGINT,
                                  tweet_id UNSIGNED BIGINT PRIMARY KEY,
                                  hashtags TEXT )"""
            
            tweets_images_1_table = """CREATE TABLE IF NOT EXISTS tweets_images_1 (
                                           tweet_id UNSIGNED BIGINT PRIMARY KEY,
                                           image_name TEXT,"""
            tweets_images_2_table = """CREATE TABLE IF NOT EXISTS tweets_images_2 (
                                           tweet_id UNSIGNED BIGINT PRIMARY KEY,
                                           image_name TEXT,"""
            tweets_images_3_table = """CREATE TABLE IF NOT EXISTS tweets_images_3 (
                                           tweet_id UNSIGNED BIGINT PRIMARY KEY,
                                           image_name TEXT,"""
            tweets_images_4_table = """CREATE TABLE IF NOT EXISTS tweets_images_4 (
                                           tweet_id UNSIGNED BIGINT PRIMARY KEY,
                                           image_name TEXT,"""
            
            # On stocker les listes de caractéristiques sur plusieurs colonnes
            # Cf. moteur CBIR, listes de 240 valeurs
            # Comme le moteur CBIR renvoit des listes de numpy.float32, c'est à
            # des floats sur 32 bits, on a besoin que de 4 octets pour les stocker,
            # donc les REAL qui prennent 4 octets
            for feature_id in range( 0, CBIR_LIST_LENGHT ) : # 240 valeurs à stocker
                tweets_images_1_table += " image_1_feature_" + str(feature_id) + " UNSIGNED REAL,"
                tweets_images_2_table += " image_2_feature_" + str(feature_id) + " UNSIGNED REAL,"
                tweets_images_3_table += " image_3_feature_" + str(feature_id) + " UNSIGNED REAL,"
                tweets_images_4_table += " image_4_feature_" + str(feature_id) + " UNSIGNED REAL,"
        
        # Suppression de la virgule finale et ajout de la parenthèse finale
        tweets_images_1_table = tweets_images_1_table[:-1] + " )"
        tweets_images_2_table = tweets_images_2_table[:-1] + " )"
        tweets_images_3_table = tweets_images_3_table[:-1] + " )"
        tweets_images_4_table = tweets_images_4_table[:-1] + " )"
        
        c.execute( tweets_table )
        c.execute( tweets_images_1_table )
        c.execute( tweets_images_2_table )
        c.execute( tweets_images_3_table )
        c.execute( tweets_images_4_table )
        
        # Créer un index permet d'accélérer grandement la recherche sur un
        # compte Twitter en particulier !
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            try :
                c.execute( "CREATE INDEX account_id ON tweets ( account_id )" )
            except mysql.connector.errors.ProgrammingError : # L'index existe déjà
                pass
        else :
            c.execute( "CREATE INDEX IF NOT EXISTS account_id ON tweets ( account_id )" )
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            account_table = """CREATE TABLE IF NOT EXISTS accounts (
                                   account_id BIGINT UNSIGNED PRIMARY KEY,
                                   last_SearchAPI_indexing_api_date CHAR(10),
                                   last_SearchAPI_indexing_local_date DATETIME,
                                   last_SearchAPI_indexing_cursor_reset_date DATETIME,
                                   last_TimelineAPI_indexing_tweet_id BIGINT UNSIGNED,
                                   last_TimelineAPI_indexing_local_date DATETIME,
                                   last_use DATETIME,
                                   uses_count BIGINT UNSIGNED DEFAULT 0 )"""
            
            reindex_tweets_table = """CREATE TABLE IF NOT EXISTS reindex_tweets (
                                          tweet_id BIGINT UNSIGNED PRIMARY KEY,
                                          account_id BIGINT UNSIGNED,
                                          image_1_url TEXT,
                                          image_2_url TEXT,
                                          image_3_url TEXT,
                                          image_4_url TEXT,
                                          hashtags TEXT,
                                          last_retry_date DATETIME,
                                          retries_count TINYINT UNSIGNED DEFAULT 0 )"""
        
        else :
            account_table = """CREATE TABLE IF NOT EXISTS accounts (
                                   account_id UNSIGNED BIGINT PRIMARY KEY,
                                   last_SearchAPI_indexing_api_date CHAR(10),
                                   last_SearchAPI_indexing_local_date DATETIME,
                                   last_SearchAPI_indexing_cursor_reset_date DATETIME ,
                                   last_TimelineAPI_indexing_tweet_id UNSIGNED BIGINT,
                                   last_TimelineAPI_indexing_local_date DATETIME,
                                   last_use DATETIME,
                                   uses_count UNSIGNED BIGINT DEFAULT 0 )"""
            
            reindex_tweets_table = """CREATE TABLE IF NOT EXISTS reindex_tweets (
                                          tweet_id UNSIGNED BIGINT PRIMARY KEY,
                                          account_id UNSIGNED BIGINT,
                                          image_1_url TEXT,
                                          image_2_url TEXT,
                                          image_3_url TEXT,
                                          image_4_url TEXT,
                                          hashtags TEXT,
                                          last_retry_date DATETIME,
                                          retries_count UNSIGNED TINYINT DEFAULT 0 )"""
        
        c.execute( account_table )
        c.execute( reindex_tweets_table )
        
        self.conn.commit()
    
    """
    Destructeur
    """
    def __del__( self ) :
        if not param.USE_MYSQL_INSTEAD_OF_SQLITE :
            try :
                self.conn.close()
            except sqlite3.ProgrammingError :
                pass
        else :
            self.conn.close()
    
    """
    Obtenir un curseur.
    @param buffered Pour MySQL, obtenir un curseur dont toutes les données sont
                    sorties de la base de données en mises en cache.
    """
    def get_cursor( self, buffered = False ) :
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            try :
                return self.conn.cursor( buffered = buffered )
            except ( mysql.connector.errors.OperationalError, mysql.connector.errors.InternalError ) :
                print( "Reconnexion à la base de données MySQL..." )
                self.conn = mysql.connector.connect(
                    host = param.MYSQL_ADDRESS,
                    port = param.MYSQL_PORT,
                    user = param.MYSQL_USERNAME,
                    password = param.MYSQL_PASSWORD,
                    database = param.MYSQL_DATABASE_NAME
                )
                return self.conn.cursor( buffered = buffered )
        else :
            return self.conn.cursor()
    
    """
    Ajouter un tweet à la base de données
    Attention ! Ce sont les "image_name" qui disent si une image doit être
    stockée ! Si un cbir_features correspondant est à None, alors les
    caractéristiques de l'image sont mises à NULL.
    
    @param account_id L'ID du compte associé au tweet
    @param tweet_id L'ID du tweet à ajouter
    
    @param cbir_features_1 La liste des caractéristiques issues de l'analyse
                           CBIR pour la première image du Tweet
                           240 VALEURS MAXIMUM
                           (OPTIONNEL)
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
    
    @param image_name_1 Le "nom" de la première image, c'est à dire son ID,
                        pour la retrouver directement avec un GET HTTP
                        (OPTIONNEL)
    @param image_name_2 Le "nom" de la seconde image, c'est à dire son ID,
                        pour la retrouver directement avec un GET HTTP
                        (OPTIONNEL)
    @param image_name_3 Le "nom" de la troisième image, c'est à dire son ID,
                        pour la retrouver directement avec un GET HTTP
                        (OPTIONNEL)
    @param image_name_4 Le "nom" de la quatrième image, c'est à dire son ID,
                        pour la retrouver directement avec un GET HTTP
                        (OPTIONNEL)
    
    @param hashtags La liste des hashtags du Tweet (OPTIONNEL)
    
    @param FORCE_INDEX Forcer l'ajout du Tweet. Efface ce qui a déjà été
                       enregistré.
    """
    def insert_tweet( self, account_id : int,
                      tweet_id : int,
                      cbir_features_1 : List[float] = None, # Peut être à None en fait si la première image est corrompue
                      cbir_features_2 : List[float] = None,
                      cbir_features_3 : List[float] = None,
                      cbir_features_4 : List[float] = None,
                      image_name_1 : str = None,
                      image_name_2 : str = None,
                      image_name_3 : str = None,
                      image_name_4 : str = None,
                      hashtags : List[str] = None,
                      FORCE_INDEX = True ) :
         # Ne pas re-vérifier, la classe Tweets_Indexer le fait déjà
#        if self.is_tweet_indexed( tweet_id ) :
#            return
        
        # Indexer même si toutes les images du Tweet sont corrompues
#        if cbir_features_1 == None and cbir_features_2 == None and cbir_features_3 == None and cbir_features_4 == None :
#            return
        
        # Si il faut forcer l'indexation, on efface ce qui a déjà été insert
        if FORCE_INDEX :
            c = self.get_cursor()
            c.execute( "DELETE FROM tweets WHERE tweet_id = %s", (tweet_id,) )
            c.execute( "DELETE FROM tweets_images_1 WHERE tweet_id = %s", (tweet_id,) )
            c.execute( "DELETE FROM tweets_images_2 WHERE tweet_id = %s", (tweet_id,) )
            c.execute( "DELETE FROM tweets_images_3 WHERE tweet_id = %s", (tweet_id,) )
            c.execute( "DELETE FROM tweets_images_4 WHERE tweet_id = %s", (tweet_id,) )
            self.conn.commit()
        
        c = self.get_cursor()
        
        # features_list_for_db() ne devrait pas être utilisé puisque
        # le moteur CBIR renvoit des listes fixes de 240 valeurs !
        
        if image_name_1 != None :
#            cbir_features_1_formatted = features_list_for_db( cbir_features_1 )
#            c.execute( sql_requests_dict["insert_tweet_image_1"],
#                       tuple( [tweet_id] + cbir_features_1_formatted ) )
            if cbir_features_1 != None :
                cbir_features_1 = [ float(v) for v in cbir_features_1 ]
            else :
                cbir_features_1 = [ None ] * CBIR_LIST_LENGHT
            c.execute( sql_requests_dict["insert_tweet_image_1"],
                       tuple( [tweet_id, image_name_1] + cbir_features_1 ) )
        
        if image_name_2 != None :
#            cbir_features_2_formatted = features_list_for_db( cbir_features_2 )
#            c.execute( sql_requests_dict["insert_tweet_image_2"],
#                       tuple( [tweet_id] + cbir_features_2_formatted ) )
            if cbir_features_2 != None :
                cbir_features_2 = [ float(v) for v in cbir_features_2 ]
            else :
                cbir_features_2 = [ None ] * CBIR_LIST_LENGHT
            c.execute( sql_requests_dict["insert_tweet_image_2"],
                       tuple( [tweet_id, image_name_2] + cbir_features_2 ) )
        
        if image_name_3 != None :
#            cbir_features_3_formatted = features_list_for_db( cbir_features_3 )
#            c.execute( sql_requests_dict["insert_tweet_image_3"],
#                       tuple( [tweet_id] + cbir_features_3_formatted ) )
            if cbir_features_3 != None :
                cbir_features_3 = [ float(v) for v in cbir_features_3 ]
            else :
                cbir_features_3 = [ None ] * CBIR_LIST_LENGHT
            c.execute( sql_requests_dict["insert_tweet_image_3"],
                       tuple( [tweet_id, image_name_3] + cbir_features_3 ) )
        
        if image_name_4 != None :
#            cbir_features_4_formatted = features_list_for_db( cbir_features_4  )
#            c.execute( sql_requests_dict["insert_tweet_image_4"],
#                       tuple( [tweet_id] + cbir_features_4_formatted ) )
            if cbir_features_4 != None :
                cbir_features_4 = [ float(v) for v in cbir_features_4 ]
            else :
                cbir_features_4 = [ None ] * CBIR_LIST_LENGHT
            c.execute( sql_requests_dict["insert_tweet_image_4"],
                       tuple( [tweet_id, image_name_4] + cbir_features_4 ) )
        
        if hashtags != None and hashtags != [] and hashtags != [""] :
            hashtags_str = ";".join( [ hashtag for hashtag in hashtags ] )
        else :
            hashtags_str = None
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            c.execute( "INSERT INTO tweets VALUES ( %s, %s, %s ) ON DUPLICATE KEY UPDATE tweets.tweet_id = tweets.tweet_id",
                       ( account_id, tweet_id, hashtags_str ) )
        else :
            c.execute( "INSERT INTO tweets VALUES ( ?, ?, ? ) ON CONFLICT ( tweet_id ) DO NOTHING",
                       ( account_id, tweet_id, hashtags_str ) )
        
        self.conn.commit()
    
    """
    Récupérer les résultats CBIR de toutes les images d'un compte Twitter, ou
    de toutes les images dans la base de données.
    @param account_id L'ID du compte Twitter (OPTIONNEL)
    @return Un itérateur sur le résultat
            Voir le fichier "class_SQLite_Image_Features_Iterator.py"
    """
    def get_images_in_db_iterator( self, account_id : int = 0 ) :
        request_1 = """SELECT * FROM tweets
                           INNER JOIN tweets_images_1 ON tweets.tweet_id = tweets_images_1.tweet_id"""
        request_2 = """SELECT * FROM tweets
                           INNER JOIN tweets_images_2 ON tweets.tweet_id = tweets_images_2.tweet_id"""
        request_3 = """SELECT * FROM tweets
                           INNER JOIN tweets_images_3 ON tweets.tweet_id = tweets_images_3.tweet_id"""
        request_4 = """SELECT * FROM tweets
                           INNER JOIN tweets_images_4 ON tweets.tweet_id = tweets_images_4.tweet_id"""
        
        if account_id != 0 :
            if param.USE_MYSQL_INSTEAD_OF_SQLITE :
                request_1 += " WHERE account_id = %s"
                request_2 += " WHERE account_id = %s"
                request_3 += " WHERE account_id = %s"
                request_4 += " WHERE account_id = %s"
                
                save_date = "UPDATE accounts SET last_use = %s WHERE account_id = %s"
                update_count = "UPDATE accounts SET uses_count = uses_count + 1 WHERE account_id = %s"
            else :
                request_1 += " WHERE account_id = ?"
                request_2 += " WHERE account_id = ?"
                request_3 += " WHERE account_id = ?"
                request_4 += " WHERE account_id = ?"
                
                save_date = "UPDATE accounts SET last_use = ? WHERE account_id = ?"
                update_count = "UPDATE accounts SET uses_count = uses_count + 1 WHERE account_id = ?"
            
            # Sauvegarder la date d'utilisation de ce compte, et faire +1 au
            # compteur d'utilisations
            c = self.get_cursor() # Note : Ca ne sert à rien qu'il soit buffered
            c.execute( save_date, ( datetime.now().strftime('%Y-%m-%d %H:%M:%S'), account_id ) )
            c.execute( update_count, ( account_id, ) )
            self.conn.commit()
        
        return Image_Features_Iterator( self.conn, account_id, request_1, request_2, request_3, request_4, ENABLE_METRICS = param.ENABLE_METRICS )
    
    """
    API DE RECHERCHE
    Stocker la date du Tweet le plus récent d'un compte Twitter
    Si le compte Twitter est déjà dans la base de données, sa date de dernier
    scan sera mise à jour
    
    @param account_id ID du compte Twitter
    @param last_scan Date du Tweet indexé le plus récent, au format YYYY-MM-DD
    """
    def set_account_SearchAPI_last_tweet_date( self, account_id : int, last_update : str ) :
        now = datetime.now()
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = """INSERT INTO accounts ( account_id, last_SearchAPI_indexing_api_date, last_SearchAPI_indexing_local_date ) VALUES ( %s, %s, %s )
                         ON DUPLICATE KEY UPDATE last_SearchAPI_indexing_api_date = %s, last_SearchAPI_indexing_local_date = %s"""
        else :
            request = """INSERT INTO accounts ( account_id, last_SearchAPI_indexing_api_date, last_SearchAPI_indexing_local_date ) VALUES ( ?, ?, ? )
                         ON CONFLICT ( account_id ) DO UPDATE SET last_SearchAPI_indexing_api_date = ?, last_SearchAPI_indexing_local_date = ?"""
        
        c = self.get_cursor()
        c.execute( request,
                   ( account_id, last_update, now.strftime('%Y-%m-%d %H:%M:%S'), last_update, now.strftime('%Y-%m-%d %H:%M:%S') ) )
        self.conn.commit()
    
    """
    API DE TIMELINE
    Stocker l'ID du Tweet le plus récent d'un compte Twitter
    Si le compte Twitter est déjà dans la base de données, sa date de dernier
    scan sera mise à jour
    
    @param account_id ID du compte Twitter
    @param tweet_id ID du Tweet indexé le plus récent
    """
    def set_account_TimelineAPI_last_tweet_id( self, account_id : int, tweet_id : int ) :
        now = datetime.now()
        c = self.get_cursor()
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = """INSERT INTO accounts ( account_id, last_TimelineAPI_indexing_tweet_id, last_TimelineAPI_indexing_local_date ) VALUES ( %s, %s, %s )
                         ON DUPLICATE KEY UPDATE last_TimelineAPI_indexing_tweet_id = %s, last_TimelineAPI_indexing_local_date = %s"""
        else :
            request = """INSERT INTO accounts ( account_id, last_TimelineAPI_indexing_tweet_id, last_TimelineAPI_indexing_local_date ) VALUES ( ?, ?, ? )
                         ON CONFLICT ( account_id ) DO UPDATE SET last_TimelineAPI_indexing_tweet_id = ?, last_TimelineAPI_indexing_local_date = ?"""
        
        c.execute( request,
                   ( account_id, tweet_id, now.strftime('%Y-%m-%d %H:%M:%S'), tweet_id, now.strftime('%Y-%m-%d %H:%M:%S') ) )
        self.conn.commit()
    
    """
    API DE RECHERCHE
    Récupérer la date du Tweet le plus récent d'un compte Twitter
    @param account_id ID du compte Twitter
    @return Date du Tweet indexé le plus récent, au format YYYY-MM-DD
            Ou None si le compte est inconnu
    """
    def get_account_SearchAPI_last_tweet_date( self, account_id : int ) -> str :
        c = self.get_cursor()
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = "SELECT last_SearchAPI_indexing_api_date FROM accounts WHERE account_id = %s"
        else :
            request = "SELECT last_SearchAPI_indexing_api_date FROM accounts WHERE account_id = ?"
        
        c.execute( request,
                   ( account_id, ) )
        last_scan = c.fetchone()
        if last_scan != None :
            return last_scan[0]
        else :
            return None
    
    """
    API DE TIMELINE
    Récupérer l'ID du Tweet le plus récent d'un compte Twitter
    @param account_id ID du compte Twitter
    @return ID du Tweet indexé le plus récent
            Ou None si le compte est inconnu
    """
    def get_account_TimelineAPI_last_tweet_id( self, account_id : int ) -> int :
        c = self.get_cursor()
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = "SELECT last_TimelineAPI_indexing_tweet_id FROM accounts WHERE account_id = %s"
        else :
            request = "SELECT last_TimelineAPI_indexing_tweet_id FROM accounts WHERE account_id = ?"
        
        c.execute( request,
                   ( account_id, ) )
        last_scan = c.fetchone()
        if last_scan != None :
            return last_scan[0]
        else :
            return None
    
    """
    API DE RECHERCHE
    Récupérer la date de l'enregistrement de la date du tweet le plus récent
    d'un compte Twitter
    C'est à dire la date du dernier appel à la fonction
    set_account_SearchAPI_last_tweet_date()
    @param account_id ID du compte Twitter
    @return Objet datetime
            Ou None si le compte est inconnu
    """
    def get_account_SearchAPI_last_scan_local_date( self, account_id : int ) -> str :
        c = self.get_cursor()
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = "SELECT last_SearchAPI_indexing_local_date FROM accounts WHERE account_id = %s"
        else :
            request = "SELECT last_SearchAPI_indexing_local_date FROM accounts WHERE account_id = ?"
        
        c.execute( request,
                   ( account_id, ) )
        last_scan = c.fetchone()
        if last_scan != None :
            if not param.USE_MYSQL_INSTEAD_OF_SQLITE :
                return datetime.strptime( last_scan[0], '%Y-%m-%d %H:%M:%S' )
            else :
                return last_scan[0]
        else :
            return None
    
    """
    API DE TIMELINE
    Récupérer la date de l'enregistrement de l'ID du Tweet le plus récent d'u
    compte Twitter
    C'est à dire la date du dernier appel à la fonction
    set_account_TimelineAPI_last_tweet_date()
    @param account_id ID du compte Twitter
    @return Objet datetime
            Ou None si le compte est inconnu
    """
    def get_account_TimelineAPI_last_scan_local_date( self, account_id : int ) -> int :
        c = self.get_cursor()
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = "SELECT last_TimelineAPI_indexing_local_date FROM accounts WHERE account_id = %s"
        else :
            request = "SELECT last_TimelineAPI_indexing_local_date FROM accounts WHERE account_id = ?"
        
        c.execute( request,
                   ( account_id, ) )
        last_scan = c.fetchone()
        if last_scan != None :
            if not param.USE_MYSQL_INSTEAD_OF_SQLITE :
                return datetime.strptime( last_scan[0], '%Y-%m-%d %H:%M:%S' )
            else :
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
        c = self.get_cursor()
        c.execute( "SELECT COUNT(*) FROM tweets" )
        count_tweets = c.fetchone()[0]
        c.execute( "SELECT COUNT(*) FROM accounts" )
        count_accounts = c.fetchone()[0]
        return [ count_tweets, count_accounts ]
    
    """
    Savoir si un Tweet est déjà indexé ou non
    @param tweet_id L'ID du tweet
    @return True ou False
    """
    def is_tweet_indexed( self, tweet_id : int ) -> bool :
        c = self.get_cursor()
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = "SELECT tweet_id FROM tweets WHERE tweet_id = %s"
        else :
            request = "SELECT tweet_id FROM tweets WHERE tweet_id = ?"
        
        c.execute( request, ( tweet_id, ) )
        return c.fetchone() != None
    
    """
    Savoir si un compte Twitter est dans la base de données ou non
    @param account_id L'ID du compte Twitter
    @return True ou False
    """
    def is_account_indexed( self, account_id : int ) -> bool :
        c = self.get_cursor()
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = "SELECT account_id FROM accounts WHERE account_id = %s"
        else :
            request = "SELECT account_id FROM accounts WHERE account_id = ?"
        
        c.execute( request, ( account_id, ) )
        return c.fetchone() != None
    
    """
    Retourner un itérateur sur les IDs des comptes Twitter dans la base données,
    triés dans l'ordre du moins récemment mise à jour au plus récemment mis à
    jour.
    La date de mise à jour la plus vielle est calculée avec la valeur minimum
    de la date du dernier scan avec l'API de recherche et du dernier scan avec
    l'API de timeline.
    
    @return Un itérateur sur le résultat
            Voir le fichier "class_Less_Recently_Updated_Accounts_Iterator.py"
    """
    def get_oldest_updated_account( self ) :
        # Il faut que ce curseur soit buffered car on peut être amené à faire
        # d'autres requêtes sur la BDD lors de l'utilisation de l'itérateur,
        # ce qui provoque des erreurs "mysql.connector.errors.InternalError:
        # Unread result found"
        # Parce que : For nonbuffered cursors, rows are not fetched from the
        # server until a row-fetching method is called. In this case, you must
        # be sure to fetch all rows of the result set before executing any
        # other statements on the same connection, or an InternalError (Unread
        # result found) exception will be raised.
        # Source :
        # https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursorbuffered.html
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            c = self.get_cursor(buffered=True)
        else :
            c = self.get_cursor()
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            # Le "ORDER BY LEAST()" considère bien la valeur NULL comme
            # inférieure à toutes les autres valeurs, et la place en tête.
            # C'est parfait pour nous !
            c.execute( """SELECT account_id, last_SearchAPI_indexing_local_date, last_TimelineAPI_indexing_local_date
                          FROM accounts
                          ORDER BY LEAST( last_SearchAPI_indexing_local_date,
                                          last_TimelineAPI_indexing_local_date ) ASC""" )
        else :
            c.execute( """SELECT account_id, last_SearchAPI_indexing_local_date, last_TimelineAPI_indexing_local_date
                          FROM accounts
                          ORDER BY MIN( last_SearchAPI_indexing_local_date,
                                        last_TimelineAPI_indexing_local_date ) ASC""" )
        return Less_Recently_Updated_Accounts_Iterator( c )
    
    """
    Enregistrer un ID de Tweet à réessayer.
    """
    def add_retry_tweet( self, tweet_id, account_id, image_1_url, image_2_url, image_3_url, image_4_url, hashtags ) :
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        c = self.get_cursor()
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = """INSERT INTO reindex_tweets ( tweet_id, account_id, image_1_url, image_2_url, image_3_url, image_4_url, hashtags, last_retry_date ) VALUES ( %s, %s, %s, %s, %s, %s, %s )
                         ON DUPLICATE KEY UPDATE last_retry_date = %s, retries_count = retries_count+1"""
        else :
            request = """INSERT INTO reindex_tweets ( tweet_id, account_id, image_1_url, image_2_url, image_3_url, image_4_url, hashtags, last_retry_date ) VALUES ( ?, ?, ?, ?, ?, ?, ? )
                         ON CONFLICT ( tweet_id ) DO UPDATE SET last_retry_date = ?, retries_count = retries_count+1"""
        
        if hashtags != None and hashtags != [] and hashtags != [""] :
            hashtags_str = ";".join( [ hashtag for hashtag in hashtags ] )
        else :
            hashtags_str = None
        
        c.execute( request,
                   ( tweet_id, account_id, image_1_url, image_2_url, image_3_url, image_4_url, hashtags_str, now, now ) )
        self.conn.commit()
    
    """
    Supprimer un ID de Tweet à réessayer.
    """
    def remove_retry_tweet( self, tweet_id ) :
        c = self.get_cursor()
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = "DELETE FROM reindex_tweets WHERE tweet_id = %s"
        else :
            request = "DELETE FROM reindex_tweets WHERE tweet_id = ?"
        
        c.execute( request, ( tweet_id, ) )
        self.conn.commit()
    
    """
    Obtenir un itérateur sur les Tweets à retenter d'indexer.
    Cet itérateur donne des dictionnaires contenant les champs suivant :
    - "tweet_id" : ID du Tweet,
    - "last_retry_date" : Objet "datetime", date du dernier réessai,
    - "retries_count" : Compteur de réessais.
    Les Tweets sont triés par ordre du plus récemment réessayé au plus récent.
    """
    def get_retry_tweets( self ) :
        c = self.get_cursor()
        
        c.execute( "SELECT tweet_id, account_id, image_1_url, image_2_url, image_3_url, image_4_url, hashtags, last_retry_date, retries_count FROM reindex_tweets ORDER BY last_retry_date" )
        
        to_return = {}
        for data in c.fetchall() :
            to_return["tweet_id"] = data[0]
            to_return["user_id"] = data[1]
            to_return["images"] = []
            if data[2] != None : to_return["images"].append( data[2] )
            if data[3] != None : to_return["images"].append( data[3] )
            if data[4] != None : to_return["images"].append( data[4] )
            if data[5] != None : to_return["images"].append( data[5] )
            if data[6] != None :
                to_return["hashtags"] = data[6].split(";")
            else :
                to_return["hashtags"] = None
            if not param.USE_MYSQL_INSTEAD_OF_SQLITE and data[6] != None :
                to_return["last_retry_date"] = datetime.strptime( data[6], '%Y-%m-%d %H:%M:%S' )
            else :
                to_return["last_retry_date"] = data[6]
            to_return["retries_count"] = data[7]
            yield to_return
    
    """
    API DE RECHERCHE
    Supprimer date du Tweet le plus récent d'un compte Twitter.
    
    @param account_id ID du compte Twitter.
    """
    def reset_account_SearchAPI_last_tweet_date( self, account_id : int ):
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = """UPDATE accounts
                         SET last_SearchAPI_indexing_api_date = NULL,
                             last_SearchAPI_indexing_local_date = NULL,
                             last_SearchAPI_indexing_cursor_reset_date = %s
                         WHERE account_id = %s"""
        else :
            request = """UPDATE accounts
                         SET last_SearchAPI_indexing_api_date = NULL,
                             last_SearchAPI_indexing_local_date = NULL,
                             last_SearchAPI_indexing_cursor_reset_date = ?
                         WHERE account_id = ?"""
        
        c = self.get_cursor()
        c.execute( request,
                   ( datetime.now().strftime('%Y-%m-%d %H:%M:%S'), account_id ) )
        self.conn.commit()
    
    """
    Obtenir un itérateur sur les comptes enregistrés dans la base, triés par
    ordre de reset de leur curseur d'indexation avec l'API de recherche. Du
    plus ancien au plus récent.
    Cet itérateur donne des dictionnaires contenant les champs suivant :
    - "account_id" : ID du compte Twitter,
    - "last_cursor_reset_date" : Objet "datetime", date du dernier reset.
    """
    def get_oldest_reseted_account( self ) :
        c = self.get_cursor()
        
        c.execute( "SELECT account_id, last_SearchAPI_indexing_cursor_reset_date FROM accounts ORDER BY last_SearchAPI_indexing_cursor_reset_date" )
        
        to_return = {}
        for data in c.fetchall() :
            to_return["account_id"] = data[0]
            if not param.USE_MYSQL_INSTEAD_OF_SQLITE and data[1] != None :
                to_return["last_cursor_reset_date"] = datetime.strptime( data[1], '%Y-%m-%d %H:%M:%S' )
            else :
                to_return["last_cursor_reset_date"] = data[1]
            yield to_return

"""
Test du bon fonctionnement de cette classe
"""
if __name__ == '__main__' :
    bdd = SQLite_or_MySQL()
    bdd.insert_tweet( 12, 42, [0.0000000001, 1000000000] )
    bdd.insert_tweet( 12, 42, [10.01, 1.1] )
    bdd.get_images_in_db_iterator( 12 )
    
    bdd.set_account_SearchAPI_last_tweet_date( 12, "2020-07-02" )
    bdd.get_account_SearchAPI_last_tweet_date( 13 )
    
    bdd.conn.close()
