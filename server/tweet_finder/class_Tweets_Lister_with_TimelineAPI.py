#!/usr/bin/python3
# coding: utf-8

from time import time

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

from tweet_finder.database.class_SQLite_or_MySQL import SQLite_or_MySQL
from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction
from tweet_finder.analyse_tweepy_response import analyse_tweepy_response


class Unfound_Account_on_Lister_with_TimelineAPI ( Exception ) :
    pass
class Blocked_by_User_with_TimelineAPI ( Exception ) :
    pass


"""
Classe permettant de lister les Tweets d'un compte Twitter avec l'API
de timeline de Twitter, via la librairie Tweepy.
"""
class Tweets_Lister_with_TimelineAPI :
    """
    Constructeur.
    
    @param tweets_queue_put Fonction pour placer un Tweet dans la file
                            d'attente de sortie. Un Tweet est représenté par le
                            dictionnaire retourné par la fonction
                            "analyse_tweet_json()".
    @param add_step_B_time Fonction de la mémoire, objet
                           "Metrics_Container".
    """
    def __init__( self, api_key, api_secret, oauth_token, oauth_token_secret,
                        tweets_queue_put,
                        DEBUG : bool = False, ENABLE_METRICS : bool = False,
                        add_step_B_time = None, # Fonction de la mémoire partagée
                  ) -> None :
        self._tweets_queue_put = tweets_queue_put
        self._DEBUG = DEBUG
        self._ENABLE_METRICS = ENABLE_METRICS
        self._add_step_B_time = add_step_B_time
        
        self._bdd = SQLite_or_MySQL()
        self._twitter = TweepyAbstraction( api_key,
                                           api_secret,
                                           oauth_token,
                                           oauth_token_secret )
    
    """
    Indiquer qu'on a fini le listage en donnant une instruction
    d'enregistrement de curseur dans la base de données. Cette instruction sera
    traitée par un thread d'indexation, ce qui permet de vérifier que tous les
    Tweets trouvés ont bien étés enregistrés.
    Ce curseur est l'ID du Tweet trouvé le plus récent, ou celui enregistré
    dans la base de données si aucun Tweet n'a été trouvé.
    
    @param account_name Le nom de compte, uniquement pour faire des print().
    @param account_id ID du compte, vérifié récemment ! Le curseur est associé
                      à l'ID dans la base de données.
    @param request_uri URI de la requête de scan associée. Permet de terminer
                       proprement une requête de scan dans le serveur AOTF.
    @param cursor Curseur à enregistrer, qui est l'ID du Tweet le plus récent,
                  ou "None" pour mettre à "NULL" si aucun Tweet n'a jamais été
                  trouvé.
    @param unchange_cursor Permet d'outrepasser le paramètre précédent et
                           laisser le curseur tel quel. L'instruction servira
                           donc uniquement à terminer la requête de scan.
    
    La BDD peut retourner None si elle ne connait pas le compte (Donc aucun
    Tweet n'est enregistré pour ce compte), c'est pas grave. L'intruction
    mènera à la création de ce compte dans la base de données.
    """
    
    def _send_save_cursor_instruction( self, account_name, account_id, request_uri,
                                             cursor = None, unchange_cursor = False ) :
        if unchange_cursor :
            cursor = self._bdd.get_account_TimelineAPI_last_tweet_id( account_id )
        
        self._tweets_queue_put( {"save_TimelineAPI_cursor" : cursor,
                                 "account_id" : account_id,
                                 "account_name" : account_name, # Pour faire des print()
                                 "request_uri" : request_uri} )
    
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
    
    @param account_name Le nom de compte, uniquement pour faire des print().
    @param account_id ID du compte, vérifié récemment !
                      Si différence, c'est le compte avec cet ID qui sera listé.
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
    les Tweets listés. Cela permet de garder une base de données cohérente en
    cas de crash.
    
    Peut émettre une exception "Unfound_Account_on_Lister_with_TimelineAPI" si
    le compte est introuvable.
    Peut émettre des "Blocked_by_User_with_TimelineAPI" si le compte nous
    bloque.
    """
    def list_TimelineAPI_tweets ( self, account_name,
                                        account_id = None,
                                        request_uri = None ) -> None :
        if account_id == None :
            account_id = self._twitter.get_account_id( account_name ) # TOUJOURS AVEC CETTE API
        if account_id == None :
            print( f"[List_TimelineAPI] Compte @{account_name} introuvable !" )
            raise Unfound_Account_on_Lister_with_TimelineAPI
        
        blocks_me, real_account_name = self._twitter.blocks_me( account_id, append_account_name = True )
        if blocks_me == None :
            print( f"[List_TimelineAPI] Compte @{account_name} introuvable !" )
            raise Unfound_Account_on_Lister_with_TimelineAPI
        if blocks_me :
            print( f"[List_TimelineAPI] Le compte @{account_name} nous bloque, impossible de le scanner !" )
            raise Blocked_by_User_with_TimelineAPI
        
        # C'est important avec l'API de recherche, mais pas ici, puisqu'on
        # utilise uniquement l'ID du compte (Son screen name sert uniquement
        # aux messages affichés). Mais on le vérifie quand même (Et c'est
        # symétrique par rapport au listage avec l'API de recherche).
        if real_account_name != account_name :
            print( f"[List_TimelineAPI] Le compte ID {account_id} se nomme @{real_account_name} et non @{account_name}." )
            account_name = real_account_name
        
        if self._DEBUG :
            print( f"[List_TimelineAPI] Listage des Tweets de @{account_name}." )
        if self._DEBUG or self._ENABLE_METRICS :
            start = time()
        
        since_tweet_id = self._bdd.get_account_TimelineAPI_last_tweet_id( account_id )
        since_tweet_id = int( since_tweet_id ) if since_tweet_id else None
        last_tweet_id = None
        count = 0
        
        # L'API de Timeline v1.1 a un problème : Elle ne retourne que le
        # premier média des Tweets qui ont des photos et des videos (Possible
        # depuis le 05 octobre 2022, ça s'appelle les "mixed medias").
        # Les alternatives suivantes ont étés testées :
        # - Son équivalent sur l'API v2, mais elle est limité à 2 millions de
        #   Tweets par mois ("Tweet Cap"), c'est honteux et inutilisable.
        # - Son équivalent sur les API privées (Via SNScrape), mais c'est plus
        #   lent et surtout il manque des Tweets (Dans les longs threads).
        # Aucune de ces alternatives n'a été retenue. A la place, on va
        # rechercher le contenu des Tweets trouvés avec l'API de Timeline v1
        # sur l'API de Tweets v2, qui n'a pas de limitation honteuse. On perd
        # plus de temps, mais c'est la solution la plus viable.
        found_tweets = []
        
        # Lister tous les Tweets depuis celui enregistré dans la base
        for tweet in self._twitter.get_account_tweets( account_id,
                                                       since_tweet_id = since_tweet_id ) :
            # Le premier tweet est forcément le plus récent
            # CECI N'EST PAS VALABLE AVEC SNSCRAPE (Tweet épinglé)
            if last_tweet_id == None :
                last_tweet_id = tweet.id
            
            # Il compte les Tweets reçus (Idem dans Tweets_Lister_with_SearchAPI)
            count += 1
            
            # Ne pas utiliser "analyse_tweet_json()" car elle sort le Tweet si
            # son média est une vidéo (Or les "mixed medias" autorisent des
            # images après cette vidéo)
            if "retweeted_status" in tweet._json : # API v1.1
                if tweet._json["full_text"][:4] != "RT @" :
                    raise Exception( f"Le Tweet ID {tweet.id} a été interprété comme un retweet alors qu'il n'y ressemble pas" ) # Doit tomber dans le collecteur d'erreurs
                continue
            if int( tweet._json["user"]["id_str"] ) != int( account_id ) :
                continue
            if ( ( "media" in tweet._json["entities"] and
                   len( tweet._json["entities"]["media"] ) > 0 ) or
                 ( "extended_entities" in tweet._json and
                   "media" in tweet._json["extended_entities"] and
                   len( tweet._json["extended_entities"]["media"] ) > 0 ) ) :
                found_tweets.append( tweet.id )
        
        # Réobtenir les Tweets trouvés avec l'API v2, afin d'être certain
        # d'avoir toutes les images (En cas de "mixed medias")
        # Cette méthode n'a pas de limite supplémentaire par rapport à son
        # équivalent sur la v1.1 (Pas de "Tweet Cap")
        cursor = 0
        while True :
            hundred_tweets = found_tweets[ cursor : cursor + 100 ]
            if len( hundred_tweets ) == 0 : break
            cursor += len( hundred_tweets )
            
            for response in self._twitter.get_multiple_tweets( hundred_tweets,
                                                               use_api_v2 = True ) :
                if response.data == None :
                    if len( response.errors ) < len( hundred_tweets ) :
                        raise Exception( "Pas assez d'erreurs pour aucun Tweet retourné" )
                    continue
                
                for tweet_dict in analyse_tweepy_response( response ) :
                    if self._DEBUG :
                        tweet_dict["screen_name"] = account_name
                    
                    # L'ajout dans la file se fait sans vérifier que l'ID du
                    # Tweet y est déjà présent, parce que ça serait trop long
                    # (La file peut être très très grande), et que l'indexeur
                    # vérifie que le Tweet ne soit pas déjà dans la BDD avant
                    # de l'analyser et de l'indexeur (Voir "Tweet_Indexer")
                    self._tweets_queue_put( tweet_dict )
        
        if self._DEBUG or self._ENABLE_METRICS :
            print( f"[List_TimelineAPI] Il a fallu {time() - start :.5g} secondes pour lister {count} Tweets de @{account_name}." )
            if self._add_step_B_time != None :
                if count > 0 :
                    self._add_step_B_time( (time() - start) / count )
        
        # Indiquer qu'on a fini le listage en donnant une instruction
        # d'enregistrement de curseur dans la base de données. Ce curseur est
        # l'ID du Tweet trouvé le plus récent, ou celui enregistré dans la base
        # de données si aucun Tweet n'a été trouvé.
        # La BDD peut retourner None si elle ne connait pas le compte (Donc aucun
        # Tweet n'est enregistré pour ce compte), c'est pas grave.
        if last_tweet_id == None :
            self._send_save_cursor_instruction( account_name, # Pour faire des print()
                                                account_id,
                                                request_uri,
                                                unchange_cursor = True )
        else :
            self._send_save_cursor_instruction( account_name, # Pour faire des print()
                                                account_id,
                                                request_uri,
                                                cursor = last_tweet_id )


"""
Test du bon fonctionnement de cette classe
"""
if __name__ == '__main__' :
    import parameters as param
    
    engine = Tweets_Lister_with_TimelineAPI( param.API_KEY,
                                             param.API_SECRET,
                                             param.TWITTER_API_KEYS[0]["OAUTH_TOKEN"],
                                             param.TWITTER_API_KEYS[0]["OAUTH_TOKEN_SECRET"],
                                             param.TWITTER_API_KEYS[0]["AUTH_TOKEN"],
                                             print,
                                             DEBUG = True )
    engine.list_TimelineAPI_tweets( "rikatantan2nd" )
