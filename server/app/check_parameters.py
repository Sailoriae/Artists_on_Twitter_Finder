#!/usr/bin/python3
# coding: utf-8

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

import parameters as param
from tweet_finder.twitter.class_SNScrapeAbstraction import SNScrapeAbstraction
from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction


"""
Fonction de vérification des paramètres.
@return True si on peut démarrer, False sinon.
"""
def check_parameters () :
    print( "Vérification des types des paramètres..." )
    try :
        check_list = []
        check_list.append( type( param.ENABLE_MULTIPROCESSING ) == bool )
        check_list.append( type( param.API_KEY ) == str )
        check_list.append( type( param.API_SECRET ) == str )
        check_list.append( type( param.OAUTH_TOKEN ) == str )
        check_list.append( type( param.OAUTH_TOKEN_SECRET ) == str )
        for creds in param.TWITTER_API_KEYS :
            check_list.append( type( creds["OAUTH_TOKEN"] ) == str )
            check_list.append( type( creds["OAUTH_TOKEN_SECRET" ]) == str )
            check_list.append( type( creds["AUTH_TOKEN" ]) == str )
        check_list.append( type( param.SQLITE_DATABASE_NAME ) == str )
        check_list.append( type( param.USE_MYSQL_INSTEAD_OF_SQLITE ) == bool )
        check_list.append( type( param.MYSQL_ADDRESS ) == str )
        check_list.append( type( param.MYSQL_PORT ) == int and param.MYSQL_PORT > 0 )
        check_list.append( type( param.MYSQL_USERNAME ) == str )
        check_list.append( type( param.MYSQL_PASSWORD ) == str )
        check_list.append( type( param.MYSQL_DATABASE_NAME ) == str )
        check_list.append( type( param.HTTP_SERVER_PORT ) == int and param.HTTP_SERVER_PORT > 0 )
        check_list.append( type( param.NUMBER_OF_STEP_1_LINK_FINDER_THREADS ) == int and param.NUMBER_OF_STEP_1_LINK_FINDER_THREADS > 0 )
        check_list.append( type( param.NUMBER_OF_STEP_2_TWEETS_INDEXER_THREADS ) == int and param.NUMBER_OF_STEP_2_TWEETS_INDEXER_THREADS > 0 )
        check_list.append( type( param.NUMBER_OF_STEP_3_REVERSE_SEARCH_THREADS ) == int and param.NUMBER_OF_STEP_3_REVERSE_SEARCH_THREADS > 0 )
        check_list.append( type( param.NUMBER_OF_STEP_A_SEARCHAPI_LIST_ACCOUNT_TWEETS_THREADS ) == int and param.NUMBER_OF_STEP_A_SEARCHAPI_LIST_ACCOUNT_TWEETS_THREADS > 0 )
        check_list.append( type( param.NUMBER_OF_STEP_B_TIMELINEAPI_LIST_ACCOUNT_TWEETS_THREADS ) == int and param.NUMBER_OF_STEP_B_TIMELINEAPI_LIST_ACCOUNT_TWEETS_THREADS > 0 )
        check_list.append( type( param.NUMBER_OF_STEP_C_INDEX_ACCOUNT_TWEETS ) == int and param.NUMBER_OF_STEP_C_INDEX_ACCOUNT_TWEETS > 0 )
        check_list.append( type( param.MAX_FILE_DESCRIPTORS ) == int and param.MAX_FILE_DESCRIPTORS > 0 )
        check_list.append( type( param.DEBUG ) == bool )
        check_list.append( type( param.ENABLE_METRICS ) == bool )
        check_list.append( type( param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE ) == int and param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE > 0 )
        check_list.append( type( param.RESET_SEARCHAPI_CURSORS_PERIOD ) == int and param.RESET_SEARCHAPI_CURSORS_PERIOD > 0 )
        check_list.append( type( param.MAX_PROCESSING_REQUESTS_PER_IP_ADDRESS ) == int and param.MAX_PROCESSING_REQUESTS_PER_IP_ADDRESS > 0 )
        check_list.append( type( param.UNLIMITED_IP_ADDRESSES ) == list )
        check_list.append( type( param.ENABLE_LOGGING ) == bool )
        
        if all( check_list ) :
            print( "Vérification réussie !" )
        else :
            print( "Veuillez réinitialiser votre fichier \"parameters.py\" et le re-configurer !")
            return False
    
    except (NameError, AttributeError) as error :
        print( "Il y a un paramètre manquant !" )
        print( error )
        print( "Veuillez réinitialiser votre fichier \"parameters.py\" et le re-configurer !")
        return False
    
    # ========================================================================
    
    if len( param.TWITTER_API_KEYS ) < 1 :
        print( "Vous devez donner l'accès à au moins un compte Twitter via la liste \"TWITTER_API_KEYS\"." )
        return False
    
    # ========================================================================
    
    if ( param.NUMBER_OF_STEP_A_SEARCHAPI_LIST_ACCOUNT_TWEETS_THREADS != len(param.TWITTER_API_KEYS) and
         param.NUMBER_OF_STEP_B_TIMELINEAPI_LIST_ACCOUNT_TWEETS_THREADS != len(param.TWITTER_API_KEYS) ) :
        print( "Il doit y avoir autant de threads de listage que de clés d'API dans \"TWITTER_API_KEYS\"." )
    
    # ========================================================================
    
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("localhost", param.HTTP_SERVER_PORT)) == 0 :
            print( f"Le port {param.HTTP_SERVER_PORT} est déjà utilisé. Veuillez changer la valeur de \"HTTP_SERVER_PORT\"." )
            print( "Vérifier que le serveur AOTF ne tourne pas déjà." )
            return False
    
    # ========================================================================
    
    # Source : https://www.sqlite.org/faq.html#q5
    # "Multiple processes can be doing a SELECT at the same time. But only one
    # process can be making changes to the database at any moment in time."
    if param.ENABLE_MULTIPROCESSING and not param.USE_MYSQL_INSTEAD_OF_SQLITE :
        print( "Vous utilisez SQLite en mode multi-processus, ce qui est impossible !" )
        print( "Veuillez utiliser MySQL (\"USE_MYSQL_INSTEAD_OF_SQLITE\"), ou bien désactiver le multi-processus (\"ENABLE_MULTIPROCESSING\")." )
        return False
    
    # ========================================================================
    
    print( "Verification de la connexion à l'API publique Twitter..." )
    
    def test_twitter ( api ) :
        # On essaye d'avoir le premier Tweet sur Twitter
        # https://twitter.com/jack/status/20
        if twitter.get_tweet( 20 ) == None :
            print( "Echec de connexion à l'API publique Twitter !")
            print( "Veuillez vérifier votre fichier \"parameters.py\" !" )
            print( "Notamment les clés suivantes : API_KEY, API_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET" )
            return False
        else :
            print( "Connexion à l'API publique Twitter réussie !")
            return True
    
    twitter = TweepyAbstraction( param.API_KEY,
                                 param.API_SECRET,
                                 param.OAUTH_TOKEN,
                                 param.OAUTH_TOKEN_SECRET )
    if not test_twitter( twitter ) :
        return False
    
    for creds in param.TWITTER_API_KEYS :
        twitter = TweepyAbstraction( param.API_KEY,
                                     param.API_SECRET,
                                     creds["OAUTH_TOKEN"],
                                     creds["OAUTH_TOKEN_SECRET"] )
        if not test_twitter( twitter ) :
            return False
    
    # ========================================================================
    
    for creds in param.TWITTER_API_KEYS :
        token = creds["AUTH_TOKEN"]
        snscrape = SNScrapeAbstraction( token )
        query = "from:@Twitter since:2020-08-11 until:2020-08-12"
        
        tweets_jsons = []
        def save_tweet( tweet_json ) :
            tweets_jsons.append( tweet_json )
        
        try :
            snscrape.search( query, save_tweet )
        except Exception as error :
            print( "Echec de connexion à l'API de recherche de SNScrape...")
            print( error )
            print( "Veuillez vérifier votre fichier \"parameters.py\" !" )
            print( "Notamment les clés suivantes : AUTH_TOKEN" )
            return False
        else :
            print( "Connexion à l'API de recherche de SNScrape réussie !")
    
    print( "Verification de l'accès aux images avec SNScrape..." )
    ok = False
    for tweet_json in tweets_jsons :
        if tweet_json['id_str'] == "1293239745695211520" : # On test avec un seul tweet
            images = []
            for tweet_media in tweet_json["extended_entities"]["media"] :
                if tweet_media["type"] == "photo" :
                    images.append( tweet_media["media_url_https"] )
            if images == ["https://pbs.twimg.com/media/EfJ-C-JU0AAQL_C.jpg",
                          "https://pbs.twimg.com/media/EfJ-aHlU0AAU1kq.jpg"] :
                ok = True
                print( "SNScrape a bien accès aux images des Tweets !" )
    
    if not ok :
        print( "SNScrape n'a pas accès aux images des Tweets !" )
        print( "Il faut revoir son code !" )
        print( "Ou alors le Tweet ID 1293239745695211520 n'existe plus." )
        return False
    
    # ========================================================================
    
    if param.USE_MYSQL_INSTEAD_OF_SQLITE :
        print( "Vérification de la connexion à la BDD MySQL..." )
        try :
            import mysql
            mysql.connector.connect(
                    host = param.MYSQL_ADDRESS,
                    port = param.MYSQL_PORT,
                    user = param.MYSQL_USERNAME,
                    password = param.MYSQL_PASSWORD,
                    database = param.MYSQL_DATABASE_NAME
                )
        except Exception as error:
            print( "Impossible de se connecter à la base de donées MySQL !" )
            print( error )
            print( "Veuillez vérifier votre fichier \"parameters.py\" !" )
            print( "Notamment les clés suivantes : MYSQL_ADDRESS, MYSQL_PORT, MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_DATABASE_NAME")
            print( "Vérifiez aussi que ce serveur MySQL soit bien accessible !")
            return False
        else :
            print( "Connexion à la BDD MySQL réussie !" )
    
    print( "Tous les tests ont réussi ! Démarrage du serveur..." )
    
    return True
