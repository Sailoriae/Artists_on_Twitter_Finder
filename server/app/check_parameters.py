#!/usr/bin/python3
# coding: utf-8

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param
from tweet_finder.twitter import SNScrapeAbstraction


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
        for key in param.TWITTER_AUTH_TOKENS :
            check_list.append( type( key ) == str )
        check_list.append( type( param.PIXIV_USERNAME ) == str )
        check_list.append( type( param.PIXIV_PASSWORD ) == str )
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
        check_list.append( type( param.NUMBER_OF_STEP_C_SEARCHAPI_INDEX_ACCOUNT_TWEETS ) == int and param.NUMBER_OF_STEP_C_SEARCHAPI_INDEX_ACCOUNT_TWEETS > 0 )
        check_list.append( type( param.NUMBER_OF_STEP_D_TIMELINEAPI_INDEX_ACCOUNT_TWEETS ) == int and param.NUMBER_OF_STEP_D_TIMELINEAPI_INDEX_ACCOUNT_TWEETS > 0 )
        check_list.append( type( param.DEBUG ) == bool )
        check_list.append( type( param.ENABLE_METRICS ) == bool )
        check_list.append( type( param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE ) == int and param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE >= 0 )
        check_list.append( type( param.MAX_PENDING_REQUESTS_PER_IP_ADDRESS ) == int and param.MAX_PENDING_REQUESTS_PER_IP_ADDRESS > 0 )
        check_list.append( type( param.UNLIMITED_IP_ADDRESSES ) == list )
        check_list.append( type( param.ENABLE_LOGGING ) == bool )
        
        if all( check_list ) :
            print( "Vérification réussie !" )
        else :
            print( "Veuillez réinitialiser votre fichier \"parameters.py\" et le re-configurer !")
            return False
    
    except (NameError, AttributeError) :
        print( "Il y a un paramètre manquant !" )
        print( "Veuillez réinitialiser votre fichier \"parameters.py\" et le re-configurer !")
        return False
    
    # ========================================================================
    
    print( "Verification de la connexion à l'API publique Twitter..." )
    from tweet_finder.twitter import TweepyAbstraction
    
    def test_twitter ( api ) :
        # On essaye d'avoir le premier Tweet sur Twitter
        # https://twitter.com/jack/status/20
        if twitter.get_tweet( 20 ) == None :
            print( "Echec de connexion à l'API publique Twitter !")
            print( "Veuillez vérifier votre fichier \"parameters.py\" !" )
            print( "Notamment les clés suivantes : API_KEY, API_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET" )
            print( "Et la liste de clés suivante : TWITTER_API_KEYS")
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
    
    for token in param.TWITTER_AUTH_TOKENS :
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
            print( "Notamment la liste de clés suivante : TWITTER_AUTH_TOKENS" )
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
    
    print( "Vérification de la connexion à l'API Pixiv..." )
    from link_finder.supported_websites import Pixiv
    
    try :
        Pixiv( param.PIXIV_USERNAME, param.PIXIV_PASSWORD )
    except Exception :
        print( "Echec de connexion à l'API Pixiv !")
        print( "Veuillez vérifier votre fichier \"parameters.py\" !" )
        print( "Notamment les clés suivantes : PIXIV_USERNAME, PIXIV_PASSWORD")
        return False
    else :
        print( "Connexion à l'API Pixiv réussie !")
    
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
        except Exception :
            print( "Impossible de se connecter à la base de donées MySQL !" )
            print( "Veuillez vérifier votre fichier \"parameters.py\" !" )
            print( "Notamment les clés suivantes : MYSQL_ADDRESS, MYSQL_PORT, MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_DATABASE_NAME")
            print( "Vérifiez aussi que ce serveur MySQL soit bien accessible !")
            return False
        else :
            print( "Connexion à la BDD MySQL réussie !" )
    
    print( "Tous les tests ont réussi ! Démarrage du serveur..." )
    
    return True
