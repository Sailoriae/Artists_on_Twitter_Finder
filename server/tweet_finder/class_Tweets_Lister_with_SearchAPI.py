#!/usr/bin/python3
# coding: utf-8

from time import time

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
from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction
from tweet_finder.twitter.class_SNScrapeAbstraction import SNScrapeAbstraction
from tweet_finder.analyse_tweet_json import analyse_tweet_json


class Unfound_Account_on_Lister_with_SearchAPI ( Exception ) :
    pass
class Blocked_by_User_with_SearchAPI ( Exception ) :
    pass


"""
Classe permettant de lister les Tweets d'un compte Twitter avec l'API
de recherche de Twitter, via la librairie SNScrape.
"""
class Tweets_Lister_with_SearchAPI :
    """
    Constructeur.
    
    @param add_step_A_time Fonction de la mémoire, objet
                           "Metrics_Container".
    """
    def __init__( self, api_key, api_secret, oauth_token, oauth_token_secret, auth_token,
                        DEBUG : bool = False, ENABLE_METRICS : bool = False,
                        add_step_A_time = None, # Fonction de la mémoire partagée 
                 ) -> None :
        self._DEBUG = DEBUG
        self._ENABLE_METRICS = ENABLE_METRICS
        self._add_step_A_time = add_step_A_time
        
        self._bdd = SQLite_or_MySQL()
        self._snscrape = SNScrapeAbstraction( auth_token )
        self._twitter = TweepyAbstraction( api_key,
                                           api_secret,
                                           oauth_token,
                                           oauth_token_secret )
    
    """
    Lister les Tweets du compte Twitter @account_name.
    Si le compte est déjà dans la base de données, cette fonction liste à
    partir de la date du Tweet indexé de ce compte le plus récent, stockée dans
    la base.
    
    Seuls les tweets avec des image(s) seront ajoutés dans la file queue, sous
    la forme d'un dictionnaire.
    Plus d'informations sur ce dictionnaire dans la fonction suivante :
    fonction analyse_tweet_json()
    On ne met pas le JSON complet renvoyé par l'API afin de gagner de la
    mémoire vive.
    
    @param account_name Le nom de compte, uniquement pour faire des print().
    @param tweets_queue_put Fonction pour placer un Tweet dans la file
                            d'attente de sortie. Un Tweet est représenté par le
                            dictionnaire retourné par la foncition
                            "analyse_tweet_json()".
    @param account_id ID du compte, vérifié récemment !
    @param request_uri URI de la requête de scan associée. Permet d'être passée
                       dans l'instruction de fin d'indexation.
    
    Lorsque le listage sera terminé, une instruction d'enregistrement de
    curseur dans la base de données sera ajoutée.
    Cette instruction est un dictionnaire contenant les champs suivants :
    - "save_SearchAPI_cursor" : La date du Tweet le plus récent, à enregistrer
      dans la base lorsque l'indexation pour ce compte sera terminée ou None si
      aucun Tweet n'a jamais été trouvé (Donc enregistrement "NULL" pour ce
      compte si il était déjà dans la base).
    - "account_id" : L'ID du compte Twitter concerné.
    - "account_name" : Le nom de compte Twitter concerné.
    - "request_uri" : L'URI de la requête de scan à terminer.
    Les curseurs doivent toujours être enregistrés après l'indexation de tous
    les Tweets listés. Cela permet de garder une base de données cohérente en
    cas de crash.
    
    Peut émettre une exception "Unfound_Account_on_Lister_with_TimelineAPI" si
    le compte est introuvable.
    Peut émettre des "Blocked_by_User_with_SearchAPI" si le compte nous bloque.
    """
    def list_searchAPI_tweets ( self, account_name, tweets_queue_put,
                                      account_id = None,
                                      request_uri = None ) -> None :
        if account_id == None :
            account_id = self._twitter.get_account_id( account_name ) # TOUJOURS AVEC CETTE API
        if account_id == None :
            print( f"[List_SearchAPI] Compte @{account_name} introuvable !" )
            raise Unfound_Account_on_Lister_with_SearchAPI
        
        if self._twitter.blocks_me( account_id ) :
            print( f"[List_SearchAPI] Le compte @{account_name} nous bloque, impossible de le scanner !" )
            raise Blocked_by_User_with_SearchAPI
        
        if self._DEBUG :
            print( f"[List_SearchAPI] Listage des Tweets de @{account_name}." )
        if self._DEBUG or self._ENABLE_METRICS :
            start = time()
        
        since_date = self._bdd.get_account_SearchAPI_last_tweet_date( account_id )
        
        
        # Fonction de converstion vers la fonction queue.put()
        # Permet de filtre les Tweets sans images, et de les formater pour la
        # fonction queue_put()
        def output_function ( tweet_json ) :
            tweet_dict = analyse_tweet_json( tweet_json )
            if tweet_dict != None :
                # Re-filtrer au cas où
                if int( tweet_dict["user_id"] ) == int ( account_id ) :
                    # L'ajout dans la file se fait sans vérifier que l'ID du
                    # Tweet y est déjà présent, parce que ça serait trop long
                    # (La file peut être très très grande), et que l'indexeur
                    # vérifie que le Tweet ne soit pas déjà dans la BDD avant
                    # de l'analyser et de l'indexeur (Voir "Tweet_Indexer")
                    tweets_queue_put( tweet_dict )
        
        # Note : Plus besoin de faire de bidouille avec "filter:safe"
        # On met le "@" à cause de @KIYOSATO_0928 qui renvoyait des erreurs 400
        # Laisser "-filter:retweets", ça ne supprime pas les Tweets citant
        query = f"from:@{account_name} filter:media -filter:retweets"
        if since_date != None :
            query += " since:" + since_date
        
        # Lancer la recherche
        first_tweet_date, count = self._snscrape.search( query, output_function )
        
        
        if self._DEBUG or self._ENABLE_METRICS :
            print( f"[List_SearchAPI] Il a fallu {time() - start} secondes pour lister {count} Tweets de @{account_name}." )
            if self._add_step_A_time != None :
                if count > 0 :
                    self._add_step_A_time( (time() - start) / count )
        
        # Indiquer qu'on a fini le listage en donnant une instruction
        # d'enregistrement de curseur dans la base de données. Ce curseur est
        # la date du Tweet trouvé le plus récent, ou celui enregistré dans la
        # base de données si aucun Tweet n'a été trouvé.
        # La BDD peut retourner None si elle ne connait pas le compte (Donc aucun
        # Tweet n'est enregistré pour ce compte), c'est pas grave.
        if count > 0 :
            tweets_queue_put( {"save_SearchAPI_cursor" : first_tweet_date.strftime('%Y-%m-%d'),
                               "account_id" : account_id,
                               "account_name" : account_name, # Pour faire des print()
                               "request_uri" : request_uri} )
        else :
            tweets_queue_put( {"save_SearchAPI_cursor" : self._bdd.get_account_SearchAPI_last_tweet_date( account_id ),
                               "account_id" : account_id,
                               "account_name" : account_name, # Pour faire des print()
                               "request_uri" : request_uri} )


"""
Test du bon fonctionnement de cette classe
"""
if __name__ == '__main__' :
    import parameters as param
    
    class Test :
        def put( self, tweet ) : print( tweet )
    test = Test()
    
    engine = Tweets_Lister_with_SearchAPI( param.API_KEY,
                                           param.API_SECRET,
                                           param.TWITTER_API_KEYS[0]["OAUTH_TOKEN"],
                                           param.TWITTER_API_KEYS[0]["OAUTH_TOKEN_SECRET"],
                                           param.TWITTER_API_KEYS[0]["AUTH_TOKEN"],
                                           DEBUG = True )
    engine.list_searchAPI_tweets( "rikatantan2nd", test )
