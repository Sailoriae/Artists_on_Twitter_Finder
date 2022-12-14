#!/usr/bin/python3
# coding: utf-8

from datetime import datetime
from time import time
from statistics import mean

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendamment (Notamment pour des
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

import parameters as param
from tweet_finder.cbir_engine.class_CBIR_Engine import HASH_SIZE

if param.USE_MYSQL_INSTEAD_OF_SQLITE :
    import mysql.connector
    from pkg_resources import parse_version as version
    
    # Les version antérieures à la 8.0.24 peuvent retourner des chaines de
    # caractères à la place de données binaires (Pour le type BINARY)
    if version( mysql.connector.__version__ ) < version( "8.0.24" ) :
        raise ModuleNotFoundError( "La version de la librairie MySQL-Connector-Python doit être supérieure à la 8.0.24 !" )
    
    # Les versions 8.0.29 et 8.0.30 peuvent retourner des chaines de caractères
    # à la place de données binaires (Pour le type BINARY)
    if ( version( mysql.connector.__version__ ) > version( "8.0.28" ) and
         version( mysql.connector.__version__ ) < version( "8.0.31" ) ) :
        raise ModuleNotFoundError( "Les versions 8.0.29 et 8.0.30 de la librairie MySQL-Connector-Python ne sont pas utilisables !" )
else :
    import sqlite3


# Note : Si on veut optimiser les perfs lors de la recherche, il faut :
# 1 - Utiliser MySQLdb, doc : https://mysqlclient.readthedocs.io/index.html
# 2 - Faire des "fetchmany()" dans l'itérateur des images.
# Avec MySQLdb, fait un "SELECT * FROM tweets" prend 2 secondes par millions
# d'images. La recherche dans toute la BDD reste donc compliquée. Est-ce que ça
# vaut le coup ?
# Autre gros problème : MySQLdb utilise forcément des curseurs buffered. Ce qui
# fait exploser la RAM lors d'un gros SELECT... Comme par exemple lors de la
# recherche.


"""
Calcul de la taille nécessaire pour stocker les empreintes des images.
"""
HASH_SIZE_BYTES = HASH_SIZE**2 // 8 # en octets
if ( HASH_SIZE**2 % 8 ) > 0 : HASH_SIZE_BYTES += 1

"""
Fonction utilisée pour le stockage des empreintes des images.
"""
def to_bin( value : int ) -> bytes :
    if value != None : return value.to_bytes(HASH_SIZE_BYTES, byteorder="big")
    return None
def to_int( value : bytes ) -> int :
    if value != None : return int.from_bytes(value, byteorder="big")
    return None


"""
Couche d'abstraction à une base de données SQLite ou MySQL.
"""
class SQLite_or_MySQL :
    """
    Constructeur : Connexion à la base de données.
    """
    def __init__( self ) :
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            self._conn = mysql.connector.connect(
                host = param.MYSQL_ADDRESS,
                port = param.MYSQL_PORT,
                user = param.MYSQL_USERNAME,
                password = param.MYSQL_PASSWORD,
                database = param.MYSQL_DATABASE_NAME
            )
        else :
            self._conn = sqlite3.connect(
                param.SQLITE_DATABASE_NAME,
            )
    
    """
    Installer le serveur AOTF, c'est à dire créer nos tables et nos indexes.
    Cette méthode peut être appelée à chaque démarrage, cela n'écrasera pas
    les tables ni les indexes existants.
    """
    def install_database( self ) :
        c = self._conn.cursor()
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            account_table = """CREATE TABLE IF NOT EXISTS accounts (
                                   account_id BIGINT UNSIGNED PRIMARY KEY,
                                   last_SearchAPI_indexing_api_date CHAR(10) CHARACTER SET ascii COLLATE ascii_bin,
                                   last_SearchAPI_indexing_local_date DATETIME,
                                   last_SearchAPI_indexing_cursor_reset_date DATETIME,
                                   last_TimelineAPI_indexing_tweet_id BIGINT UNSIGNED,
                                   last_TimelineAPI_indexing_local_date DATETIME,
                                   last_use DATETIME,
                                   uses_count BIGINT UNSIGNED DEFAULT 0 NOT NULL )"""
            
            tweets_table = """CREATE TABLE IF NOT EXISTS tweets (
                                  account_id BIGINT UNSIGNED NOT NULL,
                                  tweet_id BIGINT UNSIGNED PRIMARY KEY,
                                  image_1_name VARCHAR(19) CHARACTER SET ascii COLLATE ascii_bin,
                                  image_1_hash BINARY(""" + str(HASH_SIZE_BYTES) + """),
                                  image_2_name VARCHAR(19) CHARACTER SET ascii COLLATE ascii_bin,
                                  image_2_hash BINARY(""" + str(HASH_SIZE_BYTES) + """),
                                  image_3_name VARCHAR(19) CHARACTER SET ascii COLLATE ascii_bin,
                                  image_3_hash BINARY(""" + str(HASH_SIZE_BYTES) + """),
                                  image_4_name VARCHAR(19) CHARACTER SET ascii COLLATE ascii_bin,
                                  image_4_hash BINARY(""" + str(HASH_SIZE_BYTES) + """) )"""
            
            reindex_tweets_table = """CREATE TABLE IF NOT EXISTS reindex_tweets (
                                          tweet_id BIGINT UNSIGNED PRIMARY KEY,
                                          account_id BIGINT UNSIGNED,
                                          image_1_url VARCHAR(48) CHARACTER SET ascii COLLATE ascii_bin,
                                          image_2_url VARCHAR(48) CHARACTER SET ascii COLLATE ascii_bin,
                                          image_3_url VARCHAR(48) CHARACTER SET ascii COLLATE ascii_bin,
                                          image_4_url VARCHAR(48) CHARACTER SET ascii COLLATE ascii_bin,
                                          last_retry_date DATETIME,
                                          retries_count TINYINT UNSIGNED DEFAULT 0 NOT NULL )"""
        
        else :
            account_table = """CREATE TABLE IF NOT EXISTS accounts (
                                   account_id UNSIGNED BIGINT PRIMARY KEY,
                                   last_SearchAPI_indexing_api_date CHAR(10),
                                   last_SearchAPI_indexing_local_date DATETIME,
                                   last_SearchAPI_indexing_cursor_reset_date DATETIME ,
                                   last_TimelineAPI_indexing_tweet_id UNSIGNED BIGINT,
                                   last_TimelineAPI_indexing_local_date DATETIME,
                                   last_use DATETIME,
                                   uses_count UNSIGNED BIGINT DEFAULT 0 NOT NULL )"""
            
            tweets_table = """CREATE TABLE IF NOT EXISTS tweets (
                                  account_id UNSIGNED BIGINT NOT NULL,
                                  tweet_id UNSIGNED BIGINT PRIMARY KEY,
                                  image_1_name VARCHAR(19),
                                  image_1_hash BINARY(""" + str(HASH_SIZE_BYTES) + """),
                                  image_2_name VARCHAR(19),
                                  image_2_hash BINARY(""" + str(HASH_SIZE_BYTES) + """),
                                  image_3_name VARCHAR(19),
                                  image_3_hash BINARY(""" + str(HASH_SIZE_BYTES) + """),
                                  image_4_name VARCHAR(19),
                                  image_4_hash BINARY(""" + str(HASH_SIZE_BYTES) + """) )"""
            
            reindex_tweets_table = """CREATE TABLE IF NOT EXISTS reindex_tweets (
                                          tweet_id UNSIGNED BIGINT PRIMARY KEY,
                                          account_id UNSIGNED BIGINT,
                                          image_1_url VARCHAR(48),
                                          image_2_url VARCHAR(48),
                                          image_3_url VARCHAR(48),
                                          image_4_url VARCHAR(48),
                                          last_retry_date DATETIME,
                                          retries_count UNSIGNED TINYINT DEFAULT 0 NOT NULL )"""
        
        c.execute( account_table )
        c.execute( tweets_table )
        c.execute( reindex_tweets_table )
        
        # Créer un index permet d'accélérer grandement la recherche sur un
        # compte Twitter en particulier !
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            try :
                c.execute( "CREATE INDEX account_id ON tweets ( account_id )" )
            except mysql.connector.errors.ProgrammingError : # L'index existe déjà
                pass
        else :
            c.execute( "CREATE INDEX IF NOT EXISTS account_id ON tweets ( account_id )" )
        
        self._conn.commit()
    
    """
    Destructeur : Déconnexion propre de la base de données.
    """
    def __del__( self ) :
        if not hasattr( self, "_conn" ) :
            return
        if not param.USE_MYSQL_INSTEAD_OF_SQLITE :
            try :
                self._conn.close()
            except sqlite3.ProgrammingError :
                pass
        else :
            self._conn.close()
    
    """
    Obtenir un curseur.
    @param buffered Pour MySQL, obtenir un curseur dont toutes les données sont
                    sorties de la base de données en mises en cache.
    @param commit Accepter les modifications faites par d'autres acteurs sur la
                  BDD MySQL. Dans le cas du serveur AOTF, il faut toujours
                  mettre sur True si on va utiliser le curseur pour faire un
                  SELECT. Pas besoin pour un INSERT INTO ou un UPDATE.
    @param retry_once Utilisation interne, ne pas modifier.
    """
    def _get_cursor( self, buffered = False, commit = False, retry_once = True ) :
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            try :
                # Il faut faire un COMMIT avant de faire un SELECT afin
                # d'accepter les modifications faites par d'autres acteurs sur
                # la base de données MySQL
                # Sans ça, la base de données sera vue dans le même état que
                # lors du premier SELECT
                # Source 1 : https://bugs.mysql.com/bug.php?id=102053
                # Source 2 : https://stackoverflow.com/a/64864679
                # Voir documentation sur l'isolation "REPEATABLE READ"
                if commit : self._conn.commit()
                # En vrai, je ne suis pas certaine d'avoir bien compris, mais
                # ça fonctionne
                # Je n'ai pas l'impression qu'il y ait ce problème avec SQLite
                # Sauvegarde de la 1ère source car l'explication est chouette :
                # https://web.archive.org/web/20220112210448/https://bugs.mysql.com/bug.php?id=102053
                
                return self._conn.cursor( buffered = buffered )
            
            # On attrape n'importe quel erreur, parce qu'il y en a des privées
            except Exception as error :
                if not retry_once :
                    raise error # Doit tomber dans le collecteur d'erreurs
                print( "Reconnexion à la base de données MySQL..." )
                self._conn = mysql.connector.connect(
                    host = param.MYSQL_ADDRESS,
                    port = param.MYSQL_PORT,
                    user = param.MYSQL_USERNAME,
                    password = param.MYSQL_PASSWORD,
                    database = param.MYSQL_DATABASE_NAME
                )
                return self._get_cursor( buffered = buffered, commit = commit, retry_once = False )
        
        else :
            return self._conn.cursor()
    
    """
    Ajouter un tweet à la base de données
    
    @param account_id L'ID du compte associé au tweet
    @param tweet_id L'ID du tweet à ajouter
    
    @param cbir_hash_1 L'empreinte de la première image du Tweet (OPTIONNEL)
    @param cbir_hash_2 L'empreinte de la deuxième image du Tweet (OPTIONNEL)
    @param cbir_hash_3 L'empreinte de la troisième image du Tweet (OPTIONNEL)
    @param cbir_hash_4 L'empreinte de la quatrième image du Tweet (OPTIONNEL)
    
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
    
    @param FORCE_INDEX Forcer l'ajout du Tweet. Efface ce qui a déjà été
                       enregistré.
    """
    def insert_tweet( self, account_id : int,
                      tweet_id : int,
                      cbir_hash_1 : int = None, # Peut être à None en fait si la première image est corrompue
                      cbir_hash_2 : int = None,
                      cbir_hash_3 : int = None,
                      cbir_hash_4 : int = None,
                      image_name_1 : str = None,
                      image_name_2 : str = None,
                      image_name_3 : str = None,
                      image_name_4 : str = None,
                      FORCE_INDEX = True ) :
         # Ne pas re-vérifier, la classe Tweets_Indexer le fait déjà
#        if self.is_tweet_indexed( tweet_id ) :
#            return
        
        # Indexer même si toutes les images du Tweet sont corrompues
#        if cbir_hash_1 == None and cbir_hash_2 == None and cbir_hash_3 == None and cbir_hash_4 == None :
#            return
        
        # Vérifier les données
        if ( image_name_1 == None and cbir_hash_1 != None or
             image_name_2 == None and cbir_hash_2 != None or
             image_name_3 == None and cbir_hash_3 != None or
             image_name_4 == None and cbir_hash_4 != None ) :
            raise AssertionError( "L'empreinte de chaque image doit être associée à un nom !" )
        if ( account_id == None or tweet_id == None ) :
            raise AssertionError( "L'ID du compte et l'ID du Tweet doivent être définis !" )
        
        # Si il faut forcer l'indexation, on efface ce qui a déjà été insert
        if FORCE_INDEX :
            c = self._get_cursor()
            c.execute( "DELETE FROM tweets WHERE tweet_id = %s", (tweet_id,) )
            self._conn.commit()
        
        c = self._get_cursor()
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            c.execute( "INSERT INTO tweets VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s ) ON DUPLICATE KEY UPDATE tweets.tweet_id = tweets.tweet_id",
                       ( account_id, tweet_id, image_name_1,  to_bin(cbir_hash_1),  image_name_2,  to_bin(cbir_hash_2), image_name_3, to_bin(cbir_hash_3), image_name_4, to_bin(cbir_hash_4) ) )
        else :
            c.execute( "INSERT INTO tweets VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ) ON CONFLICT ( tweet_id ) DO NOTHING",
                       ( account_id, tweet_id, image_name_1,  to_bin(cbir_hash_1),  image_name_2,  to_bin(cbir_hash_2), image_name_3, to_bin(cbir_hash_3), image_name_4, to_bin(cbir_hash_4) ) )
        
        self._conn.commit()
    
    """
    Récupérer les résultats CBIR de toutes les images d'un compte Twitter, ou
    de toutes les images dans la base de données.
    @param account_id L'ID du compte Twitter (OPTIONNEL)
    @return Un itérateur de dictionnaires représentant les images de Tweets
    """
    def get_images_in_db_iterator( self, account_id : int = 0, add_step_3_times = None ) :
        request = "SELECT * FROM tweets"
        
        if param.ENABLE_METRICS :
            select_time = None # Durée pour faire le SELECT
            iteration_times = [] # Durées des itérations
            usage_times = [] # Durées des utilisations
            start = time()
        
        if account_id != 0 :
            if param.USE_MYSQL_INSTEAD_OF_SQLITE :
                request += " WHERE account_id = %s"
                
                save_date = "UPDATE accounts SET last_use = %s WHERE account_id = %s"
                update_count = "UPDATE accounts SET uses_count = uses_count + 1 WHERE account_id = %s"
            else :
                request += " WHERE account_id = ?"
                
                save_date = "UPDATE accounts SET last_use = ? WHERE account_id = ?"
                update_count = "UPDATE accounts SET uses_count = uses_count + 1 WHERE account_id = ?"
            
            # Sauvegarder la date d'utilisation de ce compte, et faire +1 au
            # compteur d'utilisations
            c = self._get_cursor()
            c.execute( save_date, ( datetime.now().strftime('%Y-%m-%d %H:%M:%S'), account_id ) )
            c.execute( update_count, ( account_id, ) )
            self._conn.commit()
        
        # Note : Ca ne sert à rien que le curseur soit buffered
        # En fait, en testant sur un gros compte (@MayoRiyo), ça fait perdre plus de temps que ça en fait gagner
        c = self._get_cursor( commit = account_id == 0 ) # Sinon on vient de faire un commit
        
        if param.ENABLE_METRICS :
            select_start = time()
        if account_id != 0 :
            c.execute( request, ( account_id, ) )
        else :
            c.execute( request )
        if param.ENABLE_METRICS :
            select_time = time() - select_start
        
        # Itérer sur les Tweets
        while True :
            if param.ENABLE_METRICS :
                iteration_start = time()
            tweet_line = c.fetchone()
            if param.ENABLE_METRICS :
                iteration_times.append( time() - iteration_start )
            
            # Si on a fini d'itérer sur tous les Tweets
            if tweet_line == None :
                if param.ENABLE_METRICS :
                    if select_time != None and iteration_times != [] and usage_times != [] :
                        print( f"[Images_It] Itération sur {len(usage_times)} images en {time() - start :.5g} secondes." )
                        print( f"[Images_It] Temps pour obtenir les Tweets : {select_time :.5g} secondes." )
                        print( f"[Images_It] Temps moyen d'itération : {mean(iteration_times) :.5g} secondes." )
                        print( f"[Images_It] Temps moyen d'utilisation : {mean(usage_times) :.5g} secondes." )
                    if add_step_3_times != None :
                        add_step_3_times( None, select_time, iteration_times, usage_times )
                break
            
            # Itérer sur les images du Tweet
            images_count = None
            for i in range(3,-1,-1) : # i = 3, 2, 1, 0
                # Si l'empreinte est à NULL, on passe cette image
                if tweet_line[3+i*2] == None :
                    continue
                
                # Détecter le nombre d'images dans le Tweet
                if images_count == None :
                    images_count = i+1
                
                if param.ENABLE_METRICS :
                    usage_start = time()
                
                yield { "account_id" :     tweet_line[0],               # ID du compte Twitter
                        "tweet_id" :       tweet_line[1],               # ID du Tweet
                        "image_name" :     tweet_line[2+i*2],           # Nom de l'image
                        "image_hash" :     to_int( tweet_line[3+i*2] ), # Empreinte de l'image
                        "image_position" : i+1,                         # Position de l'image
                        "images_count" :   images_count,                # Nombre d'images dans le Tweet
                        "distance" :       None                         # Défini par défaut
                       }
                
                if param.ENABLE_METRICS :
                    usage_times.append( time() - usage_start )
    
    """
    Executer une recherche exacte d'empreinte sur toutes les images présentes
    dans la base de données.
    @param image_hash Le hash de l'image à chercher
    @param account_id L'ID du compte Twitter (OPTIONNEL)
    @return Un itérateur de dictionnaires représentant les images de Tweets
    """
    def exact_image_hash_search( self, request_image_hash : int, account_id : int = 0 ) :
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = "SELECT * FROM tweets WHERE ( image_1_hash = %s OR image_2_hash = %s OR image_3_hash = %s OR image_4_hash = %s )"
            
            if account_id != 0 :
                request += " AND account_id = %s"
                
                save_date = "UPDATE accounts SET last_use = %s WHERE account_id = %s"
                update_count = "UPDATE accounts SET uses_count = uses_count + 1 WHERE account_id = %s"
        else :
            request = "SELECT * FROM tweets WHERE ( image_1_hash = ? OR image_2_hash = ? OR image_3_hash = ? OR image_4_hash = ? )"
            
            if account_id != 0 :
                request += " AND account_id = ?"
                
                save_date = "UPDATE accounts SET last_use = ? WHERE account_id = ?"
                update_count = "UPDATE accounts SET uses_count = uses_count + 1 WHERE account_id = ?"
            
        # Sauvegarder la date d'utilisation de ce compte, et faire +1 au
        # compteur d'utilisations
        if account_id != 0 :
            c = self._get_cursor()
            c.execute( save_date, ( datetime.now().strftime('%Y-%m-%d %H:%M:%S'), account_id ) )
            c.execute( update_count, ( account_id, ) )
            self._conn.commit()
        
        where_hash = to_bin( request_image_hash )
        c = self._get_cursor( commit = account_id == 0 ) # Sinon on vient de faire un commit
        if account_id != 0 :
            c.execute( request, ( where_hash, where_hash, where_hash, where_hash, account_id ) )
        else :
            c.execute( request, ( where_hash, where_hash, where_hash, where_hash ) )
        
        # Itérer sur les Tweets ayant une image avec le même hash
        while True :
            tweet_line = c.fetchone()
            
            # Si on a fini d'itérer sur tous les Tweets
            if tweet_line == None :
                break
            
            # Itérer sur les images du Tweet
            images_count = None
            for i in range(3,-1,-1) : # i = 3, 2, 1, 0
                # Si l'empreinte est à NULL, on passe cette image
                if tweet_line[3+i*2] == None :
                    continue
                
                # Détecter le nombre d'images dans le Tweet
                if images_count == None :
                    images_count = i+1
                
                # On est obligé de vérifier que le hash correspond, car notre
                # requête SQL ne différencie pas les 4 images de Tweets (Ce qui
                # est plus rapide à exécuter pour le serveur SQL)
                image_hash = to_int( tweet_line[3+i*2] )
                if image_hash != request_image_hash :
                    continue
                
                yield { "account_id" :     tweet_line[0],     # ID du compte Twitter
                        "tweet_id" :       tweet_line[1],     # ID du Tweet
                        "image_name" :     tweet_line[2+i*2], # Nom de l'image
                        "image_hash" :     image_hash,        # Empreinte de l'image
                        "image_position" : i+1,               # Position de l'image
                        "images_count" :   images_count,      # Nombre d'images dans le Tweet
                        "distance" :       0                  # Est égale à 0
                       }
    
    """
    API DE RECHERCHE
    Stocker la date du Tweet le plus récent d'un compte Twitter
    Si le compte Twitter est déjà dans la base de données, sa date de dernier
    scan sera mise à jour
    
    @param account_id ID du compte Twitter
    @param last_scan Date du Tweet indexé le plus récent, au format YYYY-MM-DD
    """
    def set_account_SearchAPI_last_tweet_date( self, account_id : int, last_update : str ) :
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Si pas de conflit / clé dupliquée, c'est que c'est la première indexation
        # On met donc le dernier reset du curseur d'indexation avec l'API de recherche à maintenant
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = """INSERT INTO accounts (
                            account_id,
                            last_SearchAPI_indexing_api_date,
                            last_SearchAPI_indexing_local_date,
                            last_SearchAPI_indexing_cursor_reset_date ) VALUES ( %s, %s, %s, %s )
                         ON DUPLICATE KEY UPDATE last_SearchAPI_indexing_api_date = %s, last_SearchAPI_indexing_local_date = %s"""
        else :
            request = """INSERT INTO accounts (
                            account_id,
                            last_SearchAPI_indexing_api_date,
                            last_SearchAPI_indexing_local_date,
                            last_SearchAPI_indexing_cursor_reset_date ) VALUES ( ?, ?, ?, ? )
                         ON CONFLICT ( account_id ) DO UPDATE SET last_SearchAPI_indexing_api_date = ?, last_SearchAPI_indexing_local_date = ?"""
        
        c = self._get_cursor()
        c.execute( request,
                   ( account_id, last_update, now, now, last_update, now ) )
        self._conn.commit()
    
    """
    API DE TIMELINE
    Stocker l'ID du Tweet le plus récent d'un compte Twitter
    Si le compte Twitter est déjà dans la base de données, sa date de dernier
    scan sera mise à jour
    
    @param account_id ID du compte Twitter
    @param tweet_id ID du Tweet indexé le plus récent
    """
    def set_account_TimelineAPI_last_tweet_id( self, account_id : int, tweet_id : int ) :
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c = self._get_cursor()
        
        # Important : Doit aussi enregistrer last_SearchAPI_indexing_cursor_reset_date si il crée le compte dans la BDD
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = """INSERT INTO accounts (
                             account_id,
                             last_TimelineAPI_indexing_tweet_id,
                             last_TimelineAPI_indexing_local_date,
                             last_SearchAPI_indexing_cursor_reset_date ) VALUES ( %s, %s, %s, %s )
                         ON DUPLICATE KEY UPDATE last_TimelineAPI_indexing_tweet_id = %s, last_TimelineAPI_indexing_local_date = %s"""
        else :
            request = """INSERT INTO accounts (
                             account_id,
                             last_TimelineAPI_indexing_tweet_id,
                             last_TimelineAPI_indexing_local_date,
                             last_SearchAPI_indexing_cursor_reset_date ) VALUES ( ?, ?, ?, ? )
                         ON CONFLICT ( account_id ) DO UPDATE SET last_TimelineAPI_indexing_tweet_id = ?, last_TimelineAPI_indexing_local_date = ?"""
        
        c.execute( request,
                   ( account_id, tweet_id, now, now, tweet_id, now ) )
        self._conn.commit()
    
    """
    API DE RECHERCHE
    Récupérer la date du Tweet le plus récent d'un compte Twitter
    @param account_id ID du compte Twitter
    @return Date du Tweet indexé le plus récent, au format YYYY-MM-DD
            Ou None si le compte est inconnu
    """
    def get_account_SearchAPI_last_tweet_date( self, account_id : int ) -> str :
        c = self._get_cursor( commit = True )
        
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
        c = self._get_cursor( commit = True )
        
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
        c = self._get_cursor( commit = True )
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = "SELECT last_SearchAPI_indexing_local_date FROM accounts WHERE account_id = %s"
        else :
            request = "SELECT last_SearchAPI_indexing_local_date FROM accounts WHERE account_id = ?"
        
        c.execute( request,
                   ( account_id, ) )
        last_scan = c.fetchone()
        if last_scan != None :
            if not param.USE_MYSQL_INSTEAD_OF_SQLITE :
                if last_scan[0] == None : return None
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
        c = self._get_cursor( commit = True )
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = "SELECT last_TimelineAPI_indexing_local_date FROM accounts WHERE account_id = %s"
        else :
            request = "SELECT last_TimelineAPI_indexing_local_date FROM accounts WHERE account_id = ?"
        
        c.execute( request,
                   ( account_id, ) )
        last_scan = c.fetchone()
        if last_scan != None :
            if not param.USE_MYSQL_INSTEAD_OF_SQLITE :
                if last_scan[0] == None : return None
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
        c = self._get_cursor( commit = True )
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
        c = self._get_cursor( commit = True )
        
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
        c = self._get_cursor( commit = True )
        
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
    
    Cet itérateur donne des dictionnaires contenant les champs suivant :
    - "account_id" : L'ID du compte Twitter,
    - "last_SearchAPI_indexing_local_date" : Sa date de dernière MàJ avec l'API de recherche,
    - "last_TimelineAPI_indexing_local_date" : Sa date dernière MàJ avec l'API de timeline.
    """
    def get_oldest_updated_account( self ) :
        c = self._get_cursor( commit = True )
        
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
        
        to_return = {}
        for triplet in c.fetchall() :
            last_SearchAPI_indexing_local_date = triplet[1]
            last_TimelineAPI_indexing_local_date = triplet[2]
            if last_SearchAPI_indexing_local_date != None :
                if not param.USE_MYSQL_INSTEAD_OF_SQLITE :
                    last_SearchAPI_indexing_local_date = datetime.strptime( last_SearchAPI_indexing_local_date, '%Y-%m-%d %H:%M:%S' )
            if last_TimelineAPI_indexing_local_date != None :
                if not param.USE_MYSQL_INSTEAD_OF_SQLITE :
                    last_TimelineAPI_indexing_local_date = datetime.strptime( last_TimelineAPI_indexing_local_date, '%Y-%m-%d %H:%M:%S' )
            to_return["account_id"] = triplet[0]
            to_return["last_SearchAPI_indexing_local_date"] = last_SearchAPI_indexing_local_date
            to_return["last_TimelineAPI_indexing_local_date"] = last_TimelineAPI_indexing_local_date
            yield to_return
    
    """
    Enregistrer un ID de Tweet à réessayer.
    """
    def add_retry_tweet( self, tweet_id, account_id, image_1_url, image_2_url, image_3_url, image_4_url ) :
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        c = self._get_cursor()
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = """INSERT INTO reindex_tweets ( tweet_id, account_id, image_1_url, image_2_url, image_3_url, image_4_url, last_retry_date ) VALUES ( %s, %s, %s, %s, %s, %s, %s )
                         ON DUPLICATE KEY UPDATE last_retry_date = %s, retries_count = retries_count+1"""
        else :
            request = """INSERT INTO reindex_tweets ( tweet_id, account_id, image_1_url, image_2_url, image_3_url, image_4_url, last_retry_date ) VALUES ( ?, ?, ?, ?, ?, ?, ? )
                         ON CONFLICT ( tweet_id ) DO UPDATE SET last_retry_date = ?, retries_count = retries_count+1"""
        
        c.execute( request,
                   ( tweet_id, account_id, image_1_url, image_2_url, image_3_url, image_4_url, now, now ) )
        self._conn.commit()
    
    """
    Enregistrement de secours d'un ID de Tweet à réessayer.
    """
    def add_retry_tweet_id( self, tweet_id ) :
        c = self._get_cursor()
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = """INSERT INTO reindex_tweets ( tweet_id ) VALUES ( %s )
                         ON DUPLICATE KEY UPDATE tweet_id = tweet_id"""
        else :
            request = """INSERT INTO reindex_tweets ( tweet_id ) VALUES ( ? )
                         ON CONFLICT ( tweet_id ) DO NOTHING"""
        
        c.execute( request, ( tweet_id, ) )
        self._conn.commit()
    
    """
    Supprimer un ID de Tweet à réessayer.
    """
    def remove_retry_tweet( self, tweet_id ) :
        c = self._get_cursor()
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = "DELETE FROM reindex_tweets WHERE tweet_id = %s"
        else :
            request = "DELETE FROM reindex_tweets WHERE tweet_id = ?"
        
        c.execute( request, ( tweet_id, ) )
        self._conn.commit()
    
    """
    Obtenir un itérateur sur les Tweets à retenter d'indexer.
    Cet itérateur donne des dictionnaires contenant les champs suivant :
    - "tweet_id" : ID du Tweet,
    - "last_retry_date" : Objet "datetime", date du dernier réessai,
    - "images" : Liste des URL des images du Tweet,
    - "retries_count" : Compteur de réessais.
    C'est le même format que celui de la fonction "analyse_tweet_json()".
    Les Tweets sont triés par ordre du plus récemment réessayé au plus récent.
    """
    def get_retry_tweets( self ) :
        c = self._get_cursor( commit = True )
        
        c.execute( "SELECT tweet_id, account_id, image_1_url, image_2_url, image_3_url, image_4_url, last_retry_date, retries_count FROM reindex_tweets ORDER BY last_retry_date" )
        
        to_return = {}
        for data in c.fetchall() :
            to_return["tweet_id"] = data[0]
            to_return["user_id"] = data[1]
            to_return["images"] = []
            if data[2] != None : to_return["images"].append( data[2] )
            if data[3] != None : to_return["images"].append( data[3] )
            if data[4] != None : to_return["images"].append( data[4] )
            if data[5] != None : to_return["images"].append( data[5] )
            if not param.USE_MYSQL_INSTEAD_OF_SQLITE and data[6] != None :
                to_return["last_retry_date"] = datetime.strptime( data[6], '%Y-%m-%d %H:%M:%S' )
            else :
                to_return["last_retry_date"] = data[6]
            to_return["retries_count"] = data[7]
            yield to_return
    
    """
    API DE RECHERCHE
    Supprimer date du Tweet le plus récent d'un compte Twitter.
    On ne supprime pas la date locale afin de ne pas interférer avec la mise à
    jour automatique.
    
    @param account_id ID du compte Twitter.
    """
    def reset_account_SearchAPI_last_tweet_date( self, account_id : int ):
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = """UPDATE accounts
                         SET last_SearchAPI_indexing_api_date = NULL,
                             last_SearchAPI_indexing_cursor_reset_date = %s
                         WHERE account_id = %s"""
        else :
            request = """UPDATE accounts
                         SET last_SearchAPI_indexing_api_date = NULL,
                             last_SearchAPI_indexing_cursor_reset_date = ?
                         WHERE account_id = ?"""
        
        c = self._get_cursor()
        c.execute( request,
                   ( datetime.now().strftime('%Y-%m-%d %H:%M:%S'), account_id ) )
        self._conn.commit()
    
    """
    API DE RECHERCHE
    Egaliser la date du dernier reset du curseur d'indexation avec l'API decode
    recherche avec celle de la date locale de ce même curseur d'indexation.
    Est utilisée si l'ID d'un compte Twitter est ajouté manuellement.
    
    @param account_id ID du compte Twitter.
    """
    def equalize_reset_account_SearchAPI_date( self, account_id : int ):
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            request = """UPDATE accounts
                         SET last_SearchAPI_indexing_cursor_reset_date = last_SearchAPI_indexing_local_date
                         WHERE account_id = %s"""
        else :
            request = """UPDATE accounts
                         SET last_SearchAPI_indexing_cursor_reset_date = last_SearchAPI_indexing_local_date
                         WHERE account_id = ?"""
        
        c = self._get_cursor()
        c.execute( request, ( account_id, ) )
        self._conn.commit()
    
    """
    Obtenir un itérateur sur les comptes enregistrés dans la base, triés par
    ordre de reset de leur curseur d'indexation avec l'API de recherche. Du
    plus ancien au plus récent.
    Cet itérateur donne des dictionnaires contenant les champs suivant :
    - "account_id" : ID du compte Twitter,
    - "last_cursor_reset_date" : Objet "datetime", date du dernier reset,
    - "last_SearchAPI_indexing_local_date" : Objet "datetime".
    """
    def get_oldest_reseted_account( self ) :
        c = self._get_cursor( commit = True )
        
        c.execute( """SELECT account_id,
                             last_SearchAPI_indexing_cursor_reset_date,
                             last_SearchAPI_indexing_local_date
                      FROM accounts
                      ORDER BY last_SearchAPI_indexing_cursor_reset_date""" )
        
        to_return = {}
        for data in c.fetchall() :
            to_return["account_id"] = data[0]
            if not param.USE_MYSQL_INSTEAD_OF_SQLITE and data[1] != None :
                to_return["last_cursor_reset_date"] = datetime.strptime( data[1], '%Y-%m-%d %H:%M:%S' )
            else :
                to_return["last_cursor_reset_date"] = data[1]
            if not param.USE_MYSQL_INSTEAD_OF_SQLITE and data[2] != None :
                to_return["last_SearchAPI_indexing_local_date"] = datetime.strptime( data[2], '%Y-%m-%d %H:%M:%S' )
            else :
                to_return["last_SearchAPI_indexing_local_date"] = data[2]
            yield to_return
