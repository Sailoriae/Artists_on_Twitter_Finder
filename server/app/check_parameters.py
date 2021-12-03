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
from tweet_finder.twitter.class_SNScrapeAbstraction import SNScrapeAbstraction
from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction


"""
Fonction de vérification des paramètres.
@return True si on peut démarrer, False sinon.
"""
def check_parameters () :
    print( "Vérification des types des paramètres..." )
    
    # Tester le type d'une variable
    def test_parameter_type ( name : str, # Sert uniquement à faire des "print()"
                              value, # Valeur dont on veut tester le type
                              expected_type : type # Type que l'on doit obtenir
                             ) -> bool :
        if type( value ) == expected_type :
            return True
        print( f"Le paramètre \"{name}\" est de type \"{type( value )}\" alors qu'il doit être de type \"{expected_type}\" !" )
        return False
    
    # Tester l'existence et le type d'un paramètre
    def test_parameter ( name : str, # Nom du paramètre dont on veut tester le type
                         expected_type : type # Type que l'on doit obtenir
                        ) -> bool :
        try :
            value = getattr( param, name )
        except AttributeError :
            print( f"Le paramètre \"{name}\" n'existe pas !" )
            return False
        return test_parameter_type( name, value, expected_type )
    
    # Tester l'existence, le type, et la positivé stricte d'un paramètre
    def test_strictly_postive_int_parameter ( name : str # Nom du paramètre à tester
                                             ) -> bool :
        if not test_parameter ( name, int ) : return False
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
    
    check_list.append( test_strictly_postive_int_parameter( "NUMBER_OF_STEP_1_LINK_FINDER_THREADS" ) )
    check_list.append( test_strictly_postive_int_parameter( "NUMBER_OF_STEP_2_TWEETS_INDEXER_THREADS" ) )
    check_list.append( test_strictly_postive_int_parameter( "NUMBER_OF_STEP_3_REVERSE_SEARCH_THREADS" ) )
    check_list.append( test_strictly_postive_int_parameter( "NUMBER_OF_STEP_C_INDEX_ACCOUNT_TWEETS" ) )
    
    check_list.append( test_parameter( "DEBUG", bool ) )
    check_list.append( test_parameter( "ENABLE_METRICS", bool ) )
    check_list.append( test_parameter( "USER_AGENT", str ) )
    check_list.append( test_strictly_postive_int_parameter( "DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE" ) )
    check_list.append( test_strictly_postive_int_parameter( "RESET_SEARCHAPI_CURSORS_PERIOD" ) )
    check_list.append( test_strictly_postive_int_parameter( "MAX_PROCESSING_REQUESTS_PER_IP_ADDRESS" ) )
    
    check_list.append( test_parameter( "UNLIMITED_IP_ADDRESSES", list ) )
    if check_list[-1] : # Eviter de crash si ce n'est pas une liste
        for i in range( len( param.UNLIMITED_IP_ADDRESSES ) ) :
            ip_address = param.UNLIMITED_IP_ADDRESSES[i]
            check_list.append( test_parameter_type( f"UNLIMITED_IP_ADDRESSES[{i}]", ip_address, str ) )
    
    check_list.append( test_parameter( "ENABLE_LOGGING", bool ) )
    
    if all( check_list ) :
        print( "Vérification réussie !" )
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
