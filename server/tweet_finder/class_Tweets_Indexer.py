#!/usr/bin/python3
# coding: utf-8

import traceback
import urllib
from time import sleep, time
from statistics import mean
import queue

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
    change_wdir( ".." )
    path.append(get_wdir())

from tweet_finder.database.class_SQLite_or_MySQL import SQLite_or_MySQL
from tweet_finder.cbir_engine.class_CBIR_Engine import CBIR_Engine
from tweet_finder.utils.url_to_PIL_image import binary_image_to_PIL_image
from tweet_finder.utils.get_tweet_image import get_tweet_image
from shared_memory.open_proxy import open_proxy


# Très très très important :
# 1 - On analyse les images en qualité maximale.
# 2 - Si l'image n'est plus accessible, on remplit ses champs avec NULL !


"""
Classe permettant d'indexer n'importe quel Tweet, du moment qu'il est au format
renvoyé par la fonction "analyse_tweet_json()". Elle gère aussi les intructions
d'enregistrement des curseurs, données par les deux méthodes de listage :
- Tweets_Lister_with_SearchAPI.list_SearchAPI_tweets()
- Tweets_Lister_with_TimelineAPI.list_TimelineAPI_tweets()

Si je dict d'instruction d'enregistrement contient le champs "request_uri", cela
indique la fin d'une requête de scan, et permet de mettre à jour les attributs
"finished_SearchAPI_indexing" ou "finished_TimelineAPI_indexing".

Si le dict du Tweet contient le champs "was_failed_tweet" et que son indexation
réussie, il sera supprimé de la table "reindex_tweets". Ceci est une bidouille
pour le thread de retentative d'indexation.

Si le dict du Tweet contient le champs "force_index", son éventuel
enregistrement dans la base de données sera écrasé.
Sinon, si le Tweet était déjà présent, il sera ignoré.

Note : Il n'y a aucun moyen pour empêcher deux threads indexeur (Donc éxécutant
en parallèle la fonction "index_tweets()") de traiter le même Tweet en même temps.
La probabilité que cela arrive est très faible, et implémenter des mesures contre
ferait perdre plus de temps qu'autre chose.
"""
class Tweets_Indexer :
    """
    Constructeur.
    Tous les paramètres sont optionnels, mais ils doivent correspondre
    à l'utilisation. Dans le cas d'un serveur AOTF, tous les paramètres
    doivent être utilisés.
    
    @param add_step_C_times Fonction de la mémoire partagée, objet
                            "Metrics_Container".
    @param keep_running Fonction de la mémoire partagée, objet "Shared_Memory".
    @param end_request Fonction de la mémoire partagée permettant de terminer
                       les requêtes de scan (Pipeline de traitement des
                       requêtes de scan).
    """
    def __init__( self, DEBUG : bool = False,
                        ENABLE_METRICS : bool = False,
                        add_step_C_times = None, # Fonction de la mémoire partagée
                        keep_running = None, # Fonction qui nous dit quand nous arrêter
                        end_request = None # Fonction de la mémoire partagée permettant de terminer les requêtes de scan
                 ) -> None :
        self._DEBUG = DEBUG
        self._ENABLE_METRICS = ENABLE_METRICS
        
        self._add_step_C_times = add_step_C_times
        self._keep_running = keep_running
        self._end_request_function = end_request
        
        self._bdd = SQLite_or_MySQL()
        self._cbir_engine = CBIR_Engine()
        
        if DEBUG or ENABLE_METRICS :
            self._times = [] # Liste des temps pour indexer un Tweet
            self._download_image_times = [] # Liste des temps pour télécharger les images d'un Tweet
            self._calculate_features_times = [] # Liste des temps pour d'éxécution du moteur CBIR pour une images d'un Tweet
            self._insert_into_times = [] # Liste des temps pour faire le INSERT INTO
    
    """
    Permet de gèrer les erreurs HTTP, et de les logger sans avoir a descendre
    dans le collecteur d'erreurs.
    
    @param image_url L'URL de l'image du Tweet.
    @param tweet_id L'ID du Tweet (Uniquement pour les "print()").
    
    @return L'empreinte de l'image, calculées par le moteur CBIR,
            OU None si il y a un un problème.
    
    Vraiment important : Faire "CAN_RETRY[0] = True" si jamais AOTF a une
    chance de réindexer cette image. A utiliser le plus possible, à part pour
    les erreurs insolvables, c'est à dire quand "get_tweet_image()" renvoit
    la valeur "None".
    Si l'erreur n'est pas connue comme insovable, "get_tweet_image()" fait un
    "raise" avec cette erreur.
    """
    def _get_image_hash ( self, image_url : str, tweet_id, CAN_RETRY = [False] ) -> int :
        retry_count = 0
        while True : # Solution très bourrin pour gèrer les rate limits
            try :
                if self._ENABLE_METRICS : start = time()
                image = get_tweet_image( image_url )
                if image == None : # Erreurs insolvables, 404 par exemple
                    return None
                if self._ENABLE_METRICS : self._download_image_times.append( time() - start )
                
                if self._ENABLE_METRICS : start = time()
                to_return = self._cbir_engine.index_cbir( binary_image_to_PIL_image( image ) )
                if self._ENABLE_METRICS : self._calculate_features_times.append( time() - start )
                return to_return
            
            # Envoyé par la fonction get_tweet_image() qui n'a pas réussi
            except urllib.error.HTTPError as error :
                print( f"[Tweets_Indexer] Erreur avec le Tweet ID {tweet_id} !" )
                print( error )
                print( "[Tweets_Indexer] Abandon !" )
                
                # Ne pas journaliser les erreurs connues qui arrivent souvent
                # Elles ne sont pas solutionnables, ce sont des problèmes chez Twitter
                # 502 = Bad Gateway
                # 504 = Gateway Timeout
                if not error.code in [502, 504] :
                    file = open( "method_Tweets_Indexer.get_image_hash_errors.log", "a" )
                    file.write( f"Erreur avec le Tweet ID {tweet_id} !\n" )
                    file.write( "Le Tweet va être inséré dans la table \"reindex_tweets\" (Sauf si une autre erreur se produit).\n" )
                    traceback.print_exc( file = file )
                    file.write( "\n\n\n" )
                    file.close()
                
                CAN_RETRY[0] = True
                return None
            
            except Exception as error :
                print( f"[Tweets_Indexer] Erreur avec le Tweet ID {tweet_id} !" )
                print( error )
                
                if retry_count < 1 : # Essayer un coup d'attendre
                    print( "[Tweets_Indexer] On essaye d'attendre 10 secondes..." )
                    sleep( 10 )
                    retry_count += 1
                
                else :
                    print( "[Tweets_Indexer] Abandon !" )
                    
                    file = open( "method_Tweets_Indexer.get_image_hash_errors.log", "a" )
                    file.write( f"Erreur avec le Tweet ID {tweet_id} !\n" )
                    file.write( "Le Tweet va être inséré dans la table \"reindex_tweets\" (Sauf si une autre erreur se produit).\n" )
                    traceback.print_exc( file = file )
                    file.write( "\n\n\n" )
                    file.close()
                    
                    CAN_RETRY[0] = True
                    return None
    
    """
    Extraire l'empreinte des images d'un Tweet et l'indexer dans la BDD.
    Cette fonction ne déclare pas quel Tweet elle est en train de traiter.
    
    @param tweet Le dictionnaire du Tweet, au format de la fonction
                 "analyse_tweet_json()".
    
    @return True si le dictionnaire passé était une Tweet et qu'il a été
            indexé.
            False si ce n'était pas un Tweet, ou qu'il n'a pas été indexé.
    """
    def _index_tweet ( self, tweet : dict ) -> bool :
        if not "tweet_id" in tweet :
            return False
        
        if self._DEBUG :
            print( f"[Tweets_Indexer] Indexation Tweet ID {tweet['tweet_id']} du compte ID {tweet['user_id']}." )
        if self._DEBUG or self._ENABLE_METRICS :
            start = time()
        
        # Pas besoin de tester si le Tweet est en train d'être traité en
        # parallèle, car la file "Tweets_to_Index_Queue" empêche qu'un Tweet
        # y soit présent deux fois
        
        # Tester avant d'indexer si le tweet n'est pas déjà dans la BDD
        # Ne jamais enlever cette vérification, il y a pleins de raisons qui
        # justifient de passer un peu de temps à toujours vérifier que le Tweet
        # existe, car sinon on perd trop de temps à faire le calcul CBIR pour
        # pour rien. Exemples de raisons :
        # - Le parallélisme et le fait qu'il n'y a pas d'objet dans la mémoire
        #   partagée contenant tous les Tweets indexés,
        # - Le thread de reset des curseurs de listage avec SearchAPI.
        if self._bdd.is_tweet_indexed( tweet["tweet_id"] ) and not "force_index" in tweet :
            if self._DEBUG :
                print( "[Tweets_Indexer] Tweet déjà indexé !" )
            return False
        
        length = len( tweet["images"] )
        
        if length == 0 :
            if self._DEBUG :
                print( "[Tweets_Indexer] Tweet sans image, on le passe !" )
            return False
        
        image_1_url = None
        image_2_url = None
        image_3_url = None
        image_4_url = None
        
        image_1_hash = None
        image_2_hash = None
        image_3_hash = None
        image_4_hash = None
        
        image_1_name = None
        image_2_name = None
        image_3_name = None
        image_4_name = None
        
        # Mis à True si le Tweet aura besoin d'être réindexé
        # Dans une liste, car les listes sont passées par référence
        will_need_retry = [False]
        
        # Traitement des images du Tweet
        if length > 0 :
            image_1_url = tweet["images"][0]
            image_1_hash = self._get_image_hash( image_1_url, tweet["tweet_id"], CAN_RETRY = will_need_retry )
            image_1_name = image_1_url.replace( "https://pbs.twimg.com/media/", "" )
        if length > 1 :
            image_2_url = tweet["images"][1]
            image_2_hash = self._get_image_hash( image_2_url, tweet["tweet_id"], CAN_RETRY = will_need_retry )
            image_2_name = image_2_url.replace( "https://pbs.twimg.com/media/", "" )
        if length > 2 :
            image_3_url = tweet["images"][2]
            image_3_hash = self._get_image_hash( image_3_url, tweet["tweet_id"], CAN_RETRY = will_need_retry )
            image_3_name = image_3_url.replace( "https://pbs.twimg.com/media/", "" )
        if length > 3 :
            image_4_url = tweet["images"][3]
            image_4_hash = self._get_image_hash( image_4_url, tweet["tweet_id"], CAN_RETRY = will_need_retry )
            image_4_name = image_4_url.replace( "https://pbs.twimg.com/media/", "" )
        
        if self._DEBUG or self._ENABLE_METRICS :
            start_insert_into = time()
        
        # Stockage des résultats
        # On stocke même si toutes les images sont à None
        # Car cela veut dire que toutes les images ont étées perdues par Twitter
        self._bdd.insert_tweet(
            tweet["user_id"],
            tweet["tweet_id"],
            cbir_hash_1 = image_1_hash,
            cbir_hash_2 = image_2_hash,
            cbir_hash_3 = image_3_hash,
            cbir_hash_4 = image_4_hash,
            image_name_1 = image_1_name,
            image_name_2 = image_2_name,
            image_name_3 = image_3_name,
            image_name_4 = image_4_name,
            FORCE_INDEX = "force_index" in tweet
        )
        
        # Si une image a échoué, le Tweet devra être réindexé
        # On le fait après le vrai enregistrement si jamais le compte
        # utilisé pour réindexé est bloqué par le compte Twitter en cours
        # de scan
        if will_need_retry[0] :
            self._bdd.add_retry_tweet(
                tweet["tweet_id"],
                tweet["user_id"],
                image_1_url,
                image_2_url,
                image_3_url,
                image_4_url,
            )
        
        # Sinon, si c'était un Tweet échoué, on l'enlève de la table des
        # Tweets dont l'indexation a échouée
        # Ceci est la bidouille pour le thread de retentative d'indexation
        elif "was_failed_tweet" in tweet :
            self._bdd.remove_retry_tweet( tweet["tweet_id"] )
        
        if self._DEBUG or self._ENABLE_METRICS :
            self._insert_into_times.append( time() - start_insert_into )
            self._times.append( time() - start )
        
        return True
    
    """
    Enregistrer la date du Tweet listé le plus récent dans la base de données.
    Cette date est renvoyée par la méthode
    Tweet_Lister_with_SearchAPI.list_SearchAPI_tweets().
    
    @param last_tweet_date Date à enregistrer.
    @param account_id L'ID du compte Twitter.
    """
    def _save_last_tweet_date ( self, account_id : int, last_tweet_date : str ) -> None :
        self._bdd.set_account_SearchAPI_last_tweet_date( account_id, last_tweet_date )
    
    """
    Enregistrer l'ID Tweet listé le plus récent dans la base de données.
    Cet ID est renvoyé par la méthode
    Tweets_Lister_with_TimelineAPI.list_TimelineAPI_tweets().
    
    @param last_tweet_id ID de Tweet à enregistrer.
    @param account_id L'ID du compte Twitter.
    """
    def _save_last_tweet_id ( self, account_id : int, last_tweet_id : int ) -> None :
        self._bdd.set_account_TimelineAPI_last_tweet_id( account_id, last_tweet_id )
    
    """
    Appeler la fonction de la mémoire partagée pour mettre fin à une requête de
    scan, et traiter son ordre d'enregistrer les curseurs d'indexation.
    
    @param account_id L'ID du compte Twitter dont il faut enregistrer les
                      curseurs. On ne prend pas celui de la requête au cas où
                      il y aurait un bug.
    @param account_name Le nom du compte Twitter, juste pour faire des print().
    @param request La requête de scan à terminer. Le proxy doit être ouvert.
    """
    def _end_request ( self, account_id : int, account_name : str, request ) -> None :
        if self._end_request_function != None :
            # C'est la fonction end_request() qui donne l'ordre d'enregistrement des curseurs
            # Elle attend qu'il n'y a plus un Tweet en cours d'indexation pour ce compte
            cursors = self._end_request_function( request, get_stats = self._bdd.get_stats() )
            
            if cursors != None : # Il faut enregistrer les deux curseurs
                print( f"[Tweets_Indexer] Enregistrement des deux curseurs d'indexation pour le compte @{account_name}." )
                
                # ATTENTION : Il est possible que les curseurs soient à None, pour des comptes vides par exemple
                self._save_last_tweet_date( account_id, cursors[0] )
                self._save_last_tweet_id( account_id, cursors[1] )
        
        else :
            raise RuntimeError( "L'attribut \"end_request\" doit être défini pour des instructions d'enregistrement de curseurs qui renvoient \"request_uri\" !" )
    
    """
    Sauvegarder les curseurs dans la base de données
    Cette fonction permet de traiter les instructions de sauvegarde de curseurs
    envoyées par les threads de listage.
    
    @param instruction Instruction envoyée sous la forme d'un dictionnaire.
    
    @return True si le dictionnaire passé était une instruction d'enregistrement
            du curseurs et a été traitée.
            False sinon.
    """
    def _save_cursors ( self, instruction : dict ) -> bool :
        # Instruction de sauvegarde du curseur de l'API de recherche
        if "save_SearchAPI_cursor" in instruction :
            print( f"[Tweets_Indexer] Fin de l'indexation des Tweets de @{instruction['account_name']} trouvés avec l'API de recherche." )
            
            if "request_uri" in instruction :
                request = open_proxy( instruction["request_uri"] )
                request.cursor_SearchAPI = instruction["save_SearchAPI_cursor"]
                request.finished_SearchAPI_indexing = True # Après l'enregistrement du curseur
                self._end_request( instruction["account_id"], instruction["account_name"], request )
                request.release_proxy()
            
            else : # N'est pas censé être utilisé par le serveur AOTF
                if self._end_request_function != None :
                    raise RuntimeError( "L'attribut \"end_request\" est défini mais les instructions d'enregistrement de curseurs ne renvoient pas \"request_uri\" !" )
                self._save_last_tweet_date( instruction["account_id"], instruction["save_SearchAPI_cursor"] )
            
            return True
        
        # Instruction de sauvegarde du curseur de l'API de timeline
        if "save_TimelineAPI_cursor" in instruction :
            print( f"[Tweets_Indexer] Fin de l'indexation des Tweets de @{instruction['account_name']} trouvés avec l'API de timeline." )
            
            if "request_uri" in instruction :
                request = open_proxy( instruction["request_uri"] )
                request.cursor_TimelineAPI = instruction["save_TimelineAPI_cursor"]
                request.finished_TimelineAPI_indexing = True # Après l'enregistrement du curseur
                self._end_request( instruction["account_id"], instruction["account_name"], request )
                request.release_proxy()
           
            else : # N'est pas censé être utilisé par le serveur AOTF
                if self._end_request_function != None :
                    raise RuntimeError( "L'attribut \"end_request\" est défini mais les instructions d'enregistrement de curseurs ne renvoient pas \"request_uri\" !" )
                self._save_last_tweet_id( instruction["account_id"], instruction["save_TimelineAPI_cursor"] )
            
            return True
        
        return False
    
    """
    Afficher et enregistrer les mesures des temps d'éxécution (Si on a accès
    à la mémoire partagée).
    """
    def _display_and_save_metrics ( self ) -> None :
        print( f"[Tweets_Indexer] {len(self._times)} Tweets indexés avec une moyenne de {mean(self._times)} secondes par Tweet." )
        
        if len(self._download_image_times) > 0 :
            print( f"[Tweets_Indexer] Temps moyens de téléchargement : {mean(self._download_image_times)} secondes." )
        if len(self._calculate_features_times) > 0 :
            print( f"[Tweets_Indexer] Temps moyens de calcul dans le moteur CBIR : {mean(self._calculate_features_times)} secondes." )
        if len(self._insert_into_times) > 0 :
            print( f"[Tweets_Indexer] Temps moyens d'enregistrement dans la BDD : {mean(self._insert_into_times)} secondes." )
        
        if self._add_step_C_times != None :
            self._add_step_C_times( self._times, self._download_image_times, self._calculate_features_times, self._insert_into_times )
        
        self._times.clear()
        self._download_image_times.clear()
        self._calculate_features_times.clear()
        self._insert_into_times.clear()
    
    """
    Indexer les Tweets trouvés par les des deux méthodes de listage.
    Ce sont ces méthodes qui vérifient que "account_name" est valide !
    
    @param tweets_queue_get Fonction pour obtenir un Tweet dans la file
                            d'attente où sont stockés les Tweets trouvés par
                            les méthode de listage.
                            NE DOIT PAS ETRE BLOQUANTE !
    @param current_tweet Liste vide permettant d'y place le dict du Tweet en
                         cours d'indexation. Utile en cas de crash.
    """
    
    def index_tweets ( self, tweets_queue_get, # Fonction get() de la file d'attente d'entrée
                             current_tweet = [] # Permet de place le Tweet en cours d'indexation, utilisé en cas de crash
                       ) -> None :
        while self._keep_running == None or self._keep_running() :
            current_tweet.clear()
            try :
                # La fonction "get_tweet_to_index()" du pipeline de traitement
                # des requêtes de scan déclare automatiquement (Et de manière
                # sécurisée) le Tweet qu'on est en train de traiter.
                # Si il n'y en a pas, elle nous déclare automatiquement comme
                # en attente.
                tweet = tweets_queue_get()
            except queue.Empty :
                tweet = None
            if tweet == None :
                if self._keep_running == None : return
                sleep( 1 )
                continue
            
            # Si on a sorti un Tweet, il faut le déclarer le plus rapidement
            # possible à notre thread.
            if "tweet_id" in tweet :
                # D'abord pour notre thread, en cas de crash
                current_tweet.append( tweet )
            
            # Enregistrer les mesures des temps d'éxécution tous les 100
            # Tweets (Ces temps sont calculés par la méthode "_index_tweet()").
            if len(self._times) >= 100 :
                self._display_and_save_metrics()
            
            # Traiter les instructions d'enregistrement de curseurs
            # Cette fonction permet de vérifier que c'est bien une instruction
            if self._save_cursors( tweet ) :
                continue
            
            # A partir d'ici, on est certain qu'on traite le JSON d'un Tweet
            self._index_tweet( tweet )
