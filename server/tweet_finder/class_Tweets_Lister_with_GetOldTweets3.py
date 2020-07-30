#!/usr/bin/python3
# coding: utf-8

from time import time

try :
    from lib_GetOldTweets3 import manager as GetOldTweets3_manager
    from database import SQLite_or_MySQL
    from twitter import TweepyAbtraction
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .lib_GetOldTweets3 import manager as GetOldTweets3_manager
    from .database import SQLite_or_MySQL
    from .twitter import TweepyAbtraction

# Ajouter le répertoire parent au PATH pour pouvoir importer les paramètres
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))
import parameters as param


"""
Classe permettant de lister les Tweets d'un compte Twitter avec la librairie
GetOldTweets3.
"""
class Tweets_Lister_with_GetOldTweets3 :
    def __init__( self, DEBUG : bool = False ) :
        self.DEBUG = DEBUG
        self.bdd = SQLite_or_MySQL()
        self.twitter = TweepyAbtraction( param.API_KEY,
                                         param.API_SECRET,
                                         param.OAUTH_TOKEN,
                                         param.OAUTH_TOKEN_SECRET )
    
    """
    Lister les Tweets du compte Twitter @account_name.
    Si le compte est déjà dans la base de données, cette fonction liste à
    partir de la date du Tweet indexé de ce compte le plus récent, stockée dans
    la base.
    
    @param queue Objet queue.Queue() pour y stocker les Tweets trouvés. Les
                 Tweets y sont stockés en paquets, sous la forme de listes.
                 Un Tweet est représenté par un objet
                 "GetOldTweets3.models.Tweet".
                 Lorsque le listage sera terminé, "None" sera ajouté.
    
    @return La date du Tweet le plus récent, à enregistrer dans la base lorsque
            l'indexation sera terminée.
            Ou None si le compte est introuvable.
    """
    def list_getoldtweets3_tweets ( self, account_name, queue ) :
        account_id = self.twitter.get_account_id( account_name )
        if account_id == None :
            print( "[List GOT3] Compte @" + account_name + " introuvable !" )
            return None
        
        if self.DEBUG :
            print( "[List GOT3] Listage des Tweets de @" + account_name + "." )
            start = time()
        
        since_date = self.bdd.get_account_last_scan( account_id )
        
        # Note importante : GOT3 ne peut pas voir les Tweets marqués comme
        # sensibles... Mais il peut voir les tweets non-sensibles de comptes
        # sensibles en désactivant le filtre "safe" et en étant connecté
        # à une session !
        # Cependant, désactiver le filtre "safe" masque les tweets de comptes
        # non-sensibles, il faut donc faire avec et sans !
        
        # On fait d'abord avec le filtre "safe"
        tweetCriteria = GetOldTweets3_manager.TweetCriteria()\
            .setQuerySearch( "from:" + account_name + " filter:media -filter:retweets (filter:safe OR -filter:safe)" )
        if since_date != None :
            tweetCriteria.setSince( since_date )
        
        # Note : Pas besoin de préciser "bufferLength", on aura forcément tous
        # les Tweets, par paquets de 100, puis le dernier paquet d'une taille
        # inférieure ou égale à 100.
        tweets_list_1 = GetOldTweets3_manager.TweetManager.getTweets( tweetCriteria,
                                                                      auth_token=param.TWITTER_AUTH_TOKEN,
                                                                      receiveBuffer = queue.put )
        
        # Second scan en désactivant complètement le filtre "safe"
        # Ce n'est pas grave si on scan deux fois, mais il vaut mieux le faire
        # Twitter sont beaucoup trop flou pour qu'on puisse faire des "if"
        tweetCriteria = GetOldTweets3_manager.TweetCriteria()\
            .setQuerySearch( "from:" + account_name + " filter:media -filter:retweets -filter:safe" )
        if since_date != None :
            tweetCriteria.setSince( since_date )
            
        tweets_list_2 = GetOldTweets3_manager.TweetManager.getTweets( tweetCriteria,
                                                                      auth_token=param.TWITTER_AUTH_TOKEN,
                                                                      receiveBuffer = queue.put )
        
        # Note : Le filtre "safe" filtre aussi les "gros-mots", par exemple :
        # "putain".
        # Ainsi, "(filter:safe OR -filter:safe)" permet de voir ces tweets,
        # mais pas les tweets de comptes marqués sensibles.
        # C'est pour cela qu'il y a le "if" avec une deuxième passe.
        #
        # Exemple de compte marqué sensible : "@rikatantan2nd"
        # (Compte pris au hasard pour tester, désolé)
        
        # Note 2 : J'y comprend plus rien, j'ai réussi à scanner les tweets de
        # "@Lewdlestia", qui est pourtant un compte marqué comme sensible, et
        # qui tweet que des médias sensibles (Complètement NSFW, ne pas aller
        # voir).
        # GOT3 en retourne 12 000 sur les 16 000 actuels. Normal que tous ne
        # soient pas indexés car c'est un bot qui Tweet toutes les heures.
        
        # Le problème c'est que Twitter sont très flous sur le sujet des
        # comptes et des tweets marqués sensibles...
        
        # Bref, ce système fonctionne.
        
        if self.DEBUG :
            print( "[List GOT3] Il a fallu", time() - start, "secondes pour lister", len(tweets_list_1 + tweets_list_2), "Tweets de @" + account_name + "." )
        
        # Indiquer qu'on a fini le listage
        queue.put( None )
        
        # Retourner la date du Tweet trouvé le plus récent, ou celui enregistré
        # dans la base de données si aucun Tweet n'a été trouvé
        if len( tweets_list_1 ) == 0 :
            if len( tweets_list_2 ) == 0 :
                return self.bdd.get_account_last_scan( account_id )
            else :
                return tweets_list_2[0].date.strftime('%Y-%m-%d')
        else :
            if len( tweets_list_2 ) == 0 :
                return tweets_list_1[0].date.strftime('%Y-%m-%d')
            else :
                min_date = min( tweets_list_1[0].date, tweets_list_2[0].date )
                return min_date.strftime('%Y-%m-%d')
