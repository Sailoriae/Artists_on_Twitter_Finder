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
from tweet_finder.analyse_tweet_json import analyse_tweet_json


class Unfound_Account_on_Lister_with_TimelineAPI ( Exception ) :
    pass
class Blocked_by_User_with_TimelineAPI ( Exception ) :
    pass


"""
Classe permettant de lister les Tweets d'un compte Twitter avec l'API
de timeline de Twitter, via la librairie Tweepy.
"""
class Tweets_Lister_with_TimelineAPI :
    def __init__( self, api_key, api_secret, oauth_token, oauth_token_secret,
                        DEBUG : bool = False, ENABLE_METRICS : bool = False ) :
        self._DEBUG = DEBUG
        self._ENABLE_METRICS = ENABLE_METRICS
        self._bdd = SQLite_or_MySQL()
        self._twitter = TweepyAbstraction( api_key,
                                           api_secret,
                                           oauth_token,
                                           oauth_token_secret )
    
    """
    Lister les Tweets du compte Twitter @account_name.
    Si le compte est déjà dans la base de données, cette fonction liste à
    partir de l'ID du Tweet indexé de ce compte le plus récent, stocké dans la
    base.
    
    Seuls les tweets avec des image(s) seront ajoutés dans la file queue, sous
    la forme d'un dictionnaire.
    Plus d'informations sur ce dictionnaire dans la fonction suivante :
    fonction analyse_tweet_json()
    On ne met pas le JSON complet renvoyé par l'API afin de gagner de la
    mémoire vive.
    
    Cette méthode utlise l'API de timeline, limitée aux 3200 premiers Tweets du
    compte, retweets compris !
    
    param account_name Le nom de compte, uniquement pour faire des print().
    @param queue Objet queue.Queue() pour y stocker les Tweets trouvés.
                 Un Tweet est représenté par le dictionnaire retourné par la
                 fonction analyse_tweet_json().
    @param account_id ID du compte, vérifié récemment !
    @param add_step_B_time Fonction de la mémoire partagée.
    @param request_uri URI de la requête de scan associée. Permet d'être passée
                       dans l'instruction de fin d'indexation.
    
    Lorsque le listage sera terminé, une instruction d'enregistrement de
    curseur dans la base de données sera ajoutée.
    Cette instruction est un dictionnaire contenant les champs suivants :
    - "save_TimelineAPI_cursor" : L'ID du Tweet le plus récent, à enregistrer
      dans la base lorsque l'indexation pour ce compte sera terminée ou None si
      aucun Tweet n'a jamais été trouvé (Donc enregistrement "NULL" pour ce
      compte si il était déjà dans la base).
    - "account_id" : L'ID du compte Twitter concerné.
    - "account_name" : Le nom de compte Twitter concerné.
    - "request_uri" : L'URI de la requête de scan à terminer.
    Les curseurs doivent toujours être enregistrés après l'indexation de tous
    les Tweets listés. Cela permet de garder une base de données intègre en cas
    de crash.
    
    Peut émettre une exception "Unfound_Account_on_Lister_with_TimelineAPI" si
    le compte est introuvable.
    Peut émettre des "Blocked_by_User_with_TimelineAPI" si le compte nous
    bloque.
    """
    def list_TimelineAPI_tweets ( self, account_name, queue, account_id = None,
                                  add_step_B_time = None, request_uri = None ) :
        if account_id == None :
            account_id = self._twitter.get_account_id( account_name ) # TOUJOURS AVEC CETTE API
        if account_id == None :
            print( f"[List_TimelineAPI] Compte @{account_name} introuvable !" )
            raise Unfound_Account_on_Lister_with_TimelineAPI
        
        if self._twitter.blocks_me( account_id ) :
            print( f"[List_TimelineAPI] Le compte @{account_name} nous bloque, impossible de le scanner !" )
            raise Blocked_by_User_with_TimelineAPI
        
        if self._DEBUG :
            print( f"[List_TimelineAPI] Listage des Tweets de @{account_name}." )
        if self._DEBUG or self._ENABLE_METRICS :
            start = time()
        
        since_tweet_id = self._bdd.get_account_TimelineAPI_last_tweet_id( account_id )
        last_tweet_id = None
        count = 0
        
        # Lister tous les Tweets depuis celui enregistré dans la base
        for tweet in self._twitter.get_account_tweets( account_id, since_tweet_id ) :
            # Le premier tweet est forcément le plus récent
            if last_tweet_id == None :
                last_tweet_id = tweet.id
            
            tweet_dict = analyse_tweet_json( tweet._json )
            if tweet_dict != None :
                # Re-filtrer au cas où
                if int( tweet_dict["user_id"] ) == int ( account_id ) :
                    queue.put( tweet_dict )
            count += 1
        
        if self._DEBUG or self._ENABLE_METRICS :
            print( f"[List_TimelineAPI] Il a fallu {time() - start} secondes pour lister {count} Tweets de @{account_name}." )
            if add_step_B_time != None :
                if count > 0 :
                    add_step_B_time( (time() - start) / count )
        
        # Indiquer qu'on a fini le listage en donnant une instruction
        # d'enregistrement de curseur dans la base de données. Ce curseur est
        # l'ID du Tweet trouvé le plus récent, ou celui enregistré dans la base
        # de données si aucun Tweet n'a été trouvé.
        # La BDD peut retourner None si elle ne connait pas le compte (Donc aucun
        # Tweet n'est enregistré pour ce compte), c'est pas grave.
        if last_tweet_id == None :
            queue.put( {"save_TimelineAPI_cursor" : self._bdd.get_account_TimelineAPI_last_tweet_id( account_id ),
                        "account_id" : account_id,
                        "account_name" : account_name, # Pour faire des print()
                        "request_uri" : request_uri} )
        else :
            queue.put( {"save_TimelineAPI_cursor" : last_tweet_id,
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
    
    engine = Tweets_Lister_with_TimelineAPI( param.API_KEY,
                                             param.API_SECRET,
                                             param.TWITTER_API_KEYS[0]["OAUTH_TOKEN"],
                                             param.TWITTER_API_KEYS[0]["OAUTH_TOKEN_SECRET"],
                                             DEBUG = True )
    engine.list_TimelineAPI_tweets( "rikatantan2nd", test )
