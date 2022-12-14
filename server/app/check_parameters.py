#!/usr/bin/python3
# coding: utf-8

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
    change_wdir( ".." )
    path.append(get_wdir())

import parameters as param
#from tweet_finder.analyse_tweet_json import analyse_tweet_json
from tweet_finder.twitter.class_SNScrapeAbstraction import SNScrapeAbstraction
from tweet_finder.twitter.class_SNScrapeAbstraction import TwitterSearchScraper
from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction
from tweet_finder.database.class_SQLite_or_MySQL import SQLite_or_MySQL

# Après SNScrapeAbstraction, car on y vérifie que SNScrape soit à jour
from snscrape.modules.twitter import _TwitterAPIType


"""
Fonction de vérification des paramètres.
Cette fonction est aussi responsable de l'installation de la base de données.
@return True si on peut démarrer, False sinon.
"""
def check_parameters () :
    print( "Vérification des types des paramètres..." )
    
    # Tester le type d'une variable
    def test_parameter_type ( name : str, # Sert uniquement à faire des "print()"
                              value, # Valeur dont on veut tester le type
                              expected_type : type, # Type que l'on doit obtenir
                              can_be_none : bool = False # Autoriser la valeur None
                             ) -> bool :
        if type( value ) == expected_type :
            return True
        if can_be_none and type( value ) == type( None ) :
            return True
        print( f"Le paramètre \"{name}\" est de type \"{type( value )}\" alors qu'il doit être de type \"{expected_type}\" !" )
        return False
    
    # Tester l'existence et le type d'un paramètre
    def test_parameter ( name : str, # Nom du paramètre dont on veut tester le type
                         expected_type : type, # Type que l'on doit obtenir
                         can_be_none : bool = False # Autoriser la valeur None
                        ) -> bool :
        try :
            value = getattr( param, name )
        except AttributeError :
            print( f"Le paramètre \"{name}\" n'existe pas !" )
            return False
        return test_parameter_type( name, value, expected_type, can_be_none = can_be_none )
    
    # Tester l'existence, le type, et la positivé stricte d'un paramètre
    def test_strictly_postive_int_parameter ( name : str, # Nom du paramètre à tester
                                              can_be_none : bool = False # Autoriser la valeur None
                                             ) -> bool :
        if not test_parameter ( name, int, can_be_none = can_be_none ) : return False
        if can_be_none and getattr( param, name ) == None : return True
        if getattr( param, name ) > 0 : return True
        print( f"Le paramètre \"{name}\" doit être strictement positif !" )
        return False
    
    # Tester l'existence d'une clé dans un dictionnaire, ainsi que le type de son contenu
    def test_dict_content ( dict_name : str, # Sert uniquement à faire des "print()"
                            dict_obj : dict, # Dictionnaire à tester
                            key : str, # Clé dont il faut déterminer l'existence
                            expected_type : type # Type du contenu de cette clé
                           ) -> bool :
        if not key in dict_obj :
            print( f"Le dictionnaire \"{dict_name}\" doit contenir une clé \"{key}\" !" )
            return False
        return test_parameter_type( f"{dict_name}[\"{key}\"", dict_obj[key], expected_type )
    
    check_list = []
    check_list.append( test_parameter( "ENABLE_MULTIPROCESSING", bool ) )
    
    check_list.append( test_parameter( "API_KEY", str ) )
    check_list.append( test_parameter( "API_SECRET", str ) )
    check_list.append( test_parameter( "OAUTH_TOKEN", str ) )
    check_list.append( test_parameter( "OAUTH_TOKEN_SECRET", str ) )
    
    check_list.append( test_parameter( "TWITTER_API_KEYS", list ) )
    if check_list[-1] : # Eviter de crash si ce n'est pas une liste
        for i in range( len( param.TWITTER_API_KEYS ) ) :
            creds = param.TWITTER_API_KEYS[i]
            check_list.append( test_parameter_type( f"TWITTER_API_KEYS[{i}]", creds, dict ) )
            if check_list[-1] : # Eviter de crash si ce n'est pas un dict
                check_list.append( test_dict_content( f"TWITTER_API_KEYS[{i}]", creds, "OAUTH_TOKEN", str ) )
                check_list.append( test_dict_content( f"TWITTER_API_KEYS[{i}]", creds, "OAUTH_TOKEN_SECRET", str ) )
                check_list.append( test_dict_content( f"TWITTER_API_KEYS[{i}]", creds, "AUTH_TOKEN", str ) )
    
    check_list.append( test_parameter( "SQLITE_DATABASE_NAME", str ) )
    check_list.append( test_parameter( "USE_MYSQL_INSTEAD_OF_SQLITE", bool ) )
    check_list.append( test_parameter( "MYSQL_ADDRESS", str ) )
    check_list.append( test_strictly_postive_int_parameter( "MYSQL_PORT" ) )
    check_list.append( test_parameter( "MYSQL_USERNAME", str ) )
    check_list.append( test_parameter( "MYSQL_PASSWORD", str ) )
    check_list.append( test_parameter( "MYSQL_DATABASE_NAME", str ) )
    
    check_list.append( test_strictly_postive_int_parameter( "HTTP_SERVER_PORT" ) )
    
    check_list.append( test_parameter( "DEBUG", bool ) )
    check_list.append( test_parameter( "ENABLE_METRICS", bool ) )
    check_list.append( test_strictly_postive_int_parameter( "DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE", can_be_none = True ) )
    check_list.append( test_strictly_postive_int_parameter( "RESET_SEARCHAPI_CURSORS_PERIOD", can_be_none = True ) )
    check_list.append( test_parameter( "STRICTLY_ENFORCE_PERIODS", bool ) )
    check_list.append( test_strictly_postive_int_parameter( "MAX_PROCESSING_REQUESTS_PER_IP_ADDRESS" ) )
    
    check_list.append( test_parameter( "UNLIMITED_IP_ADDRESSES", list ) )
    if check_list[-1] : # Eviter de crash si ce n'est pas une liste
        for i in range( len( param.UNLIMITED_IP_ADDRESSES ) ) :
            ip_address = param.UNLIMITED_IP_ADDRESSES[i]
            check_list.append( test_parameter_type( f"UNLIMITED_IP_ADDRESSES[{i}]", ip_address, str ) )
    
    check_list.append( test_parameter( "ADVANCED_IP_ADDRESSES", list ) )
    if check_list[-1] : # Eviter de crash si ce n'est pas une liste
        for i in range( len( param.ADVANCED_IP_ADDRESSES ) ) :
            ip_address = param.ADVANCED_IP_ADDRESSES[i]
            check_list.append( test_parameter_type( f"ADVANCED_IP_ADDRESSES[{i}]", ip_address, str ) )
    
    check_list.append( test_parameter( "ENABLE_LOGGING", bool ) )
    
    if all( check_list ) :
        print( "Vos paramètres sont utilisables !" )
    else :
        return False
    
    # ========================================================================
    
    if len( param.TWITTER_API_KEYS ) < 1 :
        print( "Vous devez donner l'accès à au moins un compte Twitter via la liste \"TWITTER_API_KEYS\"." )
        return False
    
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
    
    # Numéro du compte -> (Nom du compte, ID du compte)
    # Pour vérifier après que les couples de clés OAUTH_TOKEN et la clé
    # AUTH_TOKEN mènent bien au même compte
    account_names = {}
    
    def test_twitter ( api, account_number ) :
        if account_number == 0 : account = "par défaut"
        else : account = f"numéro {account_number}"
        
        # On essaye d'avoir le premier Tweet sur Twitter
        # https://twitter.com/jack/status/20
        if twitter.get_tweet( 20 ) == None :
            print( f"Echec de connexion à l'API publique Twitter pour le compte {account} !")
            print( "Veuillez vérifier votre fichier \"parameters.py\" !" )
            print( "Notamment les clés suivantes : API_KEY, API_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET" )
            return False
        
        # Obtenir le nom ainsi que l'ID du compte
        verify_creds = twitter._api.verify_credentials()._json
        account += f" (@{verify_creds['screen_name']})"
        account_names[ account_number ] = ( verify_creds['screen_name'], verify_creds['id'] )
        
        # Vérifier que le compte ne masque pas les médias sensibles
        settings = twitter._api.get_settings()
        if not settings["display_sensitive_media"] :
            print( f"Le compte {account} doit pouvoir voir les médias sensibles !" )
            print( "Merci de vous connecter à ce compte et de cocher la case \"Afficher les médias au contenu potentiellement sensible\" dans \"Paramètres\" -> \"Confidentialité et sécurité\" -> \"Contenu que vous voyez\"." )
            return False
        
        print( f"Connexion à l'API publique réussie pour le compte {account} !")
        return True
    
    twitter = TweepyAbstraction( param.API_KEY,
                                 param.API_SECRET,
                                 param.OAUTH_TOKEN,
                                 param.OAUTH_TOKEN_SECRET )
    if not test_twitter( twitter, 0 ) :
        return False
    
    # Vérifier au passage l'API v2
    if twitter.get_tweet( 20, use_api_v2 = True ) == None :
        print( "Votre application n'a pas accès à l'API Twitter v2 !" )
        return False
    print( "Votre application a bien accès à l'API Twitter v2 !" )
    
    account_number = 0
    for creds in param.TWITTER_API_KEYS :
        twitter = TweepyAbstraction( param.API_KEY,
                                     param.API_SECRET,
                                     creds["OAUTH_TOKEN"],
                                     creds["OAUTH_TOKEN_SECRET"] )
        account_number += 1
        if not test_twitter( twitter, account_number ) :
            return False
    
    # ========================================================================
    
    print( "Verification de la connexion à l'API de recherche Twitter..." )
    
    account_number = 0
    for creds in param.TWITTER_API_KEYS :
        account_number += 1
        account = f"numéro {account_number}"
        
        token = creds["AUTH_TOKEN"]
        snscrape = SNScrapeAbstraction( token )
        query = "from:@Twitter since:2020-08-11 until:2020-08-12"
        
        tweets_jsons = []
        try :
            for tweet in snscrape.search( query, RETRIES = 0 ) :
                tweets_jsons.append( tweet._json )
        except Exception as error :
            print( f"Echec de connexion à l'API de recherche de SNScrape pour le compte {account}...")
#            print( f"{type(error).__name__}: {error}" ) # SNScrape log déjà
            print( "Veuillez vérifier votre fichier \"parameters.py\" !" )
            print( "Notamment les clés suivantes : AUTH_TOKEN" )
            return False
        
        # Obtenir le nom du compte
        scraper = TwitterSearchScraper( "nothing" )
        scraper.set_auth_token( token )
        settings = scraper._get_api_data( "https://twitter.com/i/api/1.1/account/settings.json", _TwitterAPIType.V2, {} )
        
        # Vérifier que le nom du compte soit le même qu'avec Tweepy
        if settings['screen_name'] != account_names[ account_number ][0] :
            print( f"Les clés du compte {account} doivent donner accès au même compte !" )
            print( f"Or, le couple de clés OAUTH_TOKEN donnent accès à @{account_names[ account_number ]}, et la clé AUTH_TOKEN à @{settings['screen_name']} !" )
            return False
        
        # On ajoute le nom du compte une fois qu'on a vérifié qu'il corresponde
        account += f" (@{settings['screen_name']})"
        
        # Vérifier que la recherche affiche les médias sensibles
        scraper = TwitterSearchScraper( "nothing" )
        scraper.set_auth_token( token )
        settings = scraper._get_api_data( f"https://twitter.com/i/api/1.1/strato/column/User/{account_names[ account_number ][1]}/search/searchSafetyReadonly", _TwitterAPIType.V2, {} )
        if settings["optInFiltering"] :
            print( f"Le compte {account} ne doit pas masquer les contenus offensants dans les recherches !" )
            print( "Merci de vous connecter à ce compte et de décocher la case \"Masquer les contenus offensants\" dans \"Paramètres\" -> \"Confidentialité et sécurité\" -> \"Contenu que vous voyez\" -> \"Paramètres de recherche\"." )
            return False
        
        print( f"Connexion à l'API de recherche réussie pour le compte {account} !")
    
    # Ca serait intéressant de tester avec un Tweet qui apparait dans une
    # recherche avec un compte Twitter, et pas dans une recherche en tant
    # que invité. Sauf que j'en ai pas (encore) trouvé.
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
        print( "L'API de recherche via SNScrape n'a pas accès aux images des Tweets !" )
        print( "Ou alors le Tweet ID 1293239745695211520 n'existe plus." )
        return False
    
    # ========================================================================
    
    # Plus besoin de faire ces tests, puisque le thread de listage B (Timeline)
    # utilise désormais l'API v2 (Car SNScrape loupe des Tweets à cause de son
    # API privée qu'il utilise)
    """
    print( "Vérifications d'analyse des Tweets via SNScrape..." )
    snscrape = SNScrapeAbstraction( param.TWITTER_API_KEYS[0]["AUTH_TOKEN"] )
    
    # Vérifier qu'on détecte bien les RTs de l'API de Timeline via SNScrape
    # Le compte @HootHootyBot est connu pour faire uniquement des retweets
    # On évite un éventuel Tweet épinglé en choisissant le deuxième Tweet
    tweets = list( snscrape.user_tweets( "HootHootyBot",
                                         since_tweet_id = 2**64 ) )
    if analyse_tweet_json( tweets[1]._json ) != None :
        print( "Impossible de détecter un retweet retourné par l'API de timeline via SNScrape !" )
        print( "Ou alors le compte @HootHootyBot a changé de contenu." )
        return False
    
    # Vérifier qu'on détecte bien les images de l'API de Timeline via SNScrape
    # Le compte @hourlypony est connu pour publier uniquement des images
    # On évite un éventuel Tweet épinglé en choisissant le deuxième Tweet
    tweets = list( snscrape.user_tweets( "hourlypony",
                                         since_tweet_id = 2**64 ) )
    if analyse_tweet_json( tweets[1]._json ) == None :
        print( "Impossible de détecter un Tweet avec médias retourné par l'API de timeline via SNScrape !" )
        print( "Ou alors le compte @hourlypony a changé de contenu." )
        return False
    
    print( "Les retweets et les images sont bien détectables !" )
    """
    
    # ========================================================================
    
    accounts_count = 0 # Sert pour le test suivant
    
    if param.USE_MYSQL_INSTEAD_OF_SQLITE :
        print( "Vérification de la connexion à la BDD MySQL..." )
        try :
            bdd = SQLite_or_MySQL()
        except Exception as error:
            print( "Impossible de se connecter à la base de donées MySQL !" )
            print( f"{type(error).__name__}: {error}" )
            print( "Veuillez vérifier votre fichier \"parameters.py\" !" )
            print( "Notamment les clés suivantes : MYSQL_ADDRESS, MYSQL_PORT, MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_DATABASE_NAME")
            print( "Vérifiez aussi que ce serveur MySQL soit bien accessible !")
            return False
        else :
            print( "Connexion à la BDD MySQL réussie !" )
            bdd.install_database()
            tweets_count, accounts_count = bdd.get_stats()
    
    else :
        bdd = SQLite_or_MySQL()
        bdd.install_database()
        tweets_count, accounts_count = bdd.get_stats()
    
    # ========================================================================
    
    # API "GET users/show"
    # Estimation du nombre de requêtes qu'on va faire par fenêtres de 15 mins
    # Une fenêtre correspond à la période des rate-limits sur l'API Twitter
    # On est limité à 900 requêtes toutes les 15 minutes
    # Nombre de fenêtres dans une journée (24h) : 24*60 / 15 = 96
    # Nombre de requêtes par jours sur l'API :    900 * 96 = 86400
    estimation = 0
    if param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE != None :
        estimation = accounts_count / param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE
    if param.RESET_SEARCHAPI_CURSORS_PERIOD != None :
        estimation += accounts_count / param.RESET_SEARCHAPI_CURSORS_PERIOD
    if estimation > 86400 :
        print( f"Votre base de données a trop de comptes pour mettre à jour ses comptes tous les {param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE} jours et reset les curseurs d'indexation tous les {param.RESET_SEARCHAPI_CURSORS_PERIOD} jours." )
        print( "Merci d'augmenter la valeur des clés suivantes : DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE, RESET_SEARCHAPI_CURSORS_PERIOD" )
        return False
    
    # ========================================================================
    
    # Avertissement si désactivation de fonctionnalités
    if param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE == None :
        print( "Vous avez choisi de désactiver la mise à jour automatique des comptes indexés dans votre base de données." )
    if param.RESET_SEARCHAPI_CURSORS_PERIOD == None :
        print( "Vous avez choisi de désactiver le relistage complet et périodique des Tweets avec l'API de recherche." )
        if param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE != None :
            print( "Cependant, ce n'est pas logique de ne pas désactiver aussi la mise à jour automatique." )
            return False
    
    # ========================================================================
    
    # Avertissement si utilisation de SQLite
    if not param.USE_MYSQL_INSTEAD_OF_SQLITE :
        print( "Attention, vous utilisez SQLite. Pour de meilleure performances, il est très vivement conseillé d'utiliser MySQL !" )
    
    # ========================================================================
    
    print( "Tous les tests ont réussi ! Démarrage du serveur..." )
    
    return True
