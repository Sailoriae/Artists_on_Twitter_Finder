#!/usr/bin/python3
# coding: utf-8

import traceback
import urllib
from time import sleep, time

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

from tweet_finder.cbir_engine.class_CBIR_Engine import CBIR_Engine
from tweet_finder.utils.url_to_PIL_image import binary_image_to_PIL_image
from tweet_finder.utils.get_tweet_image import get_tweet_image


class CBIR_Engine_for_Tweets_Images :
    def __init__( self, DEBUG : bool = False ) :
        self.DEBUG = DEBUG
        self.cbir_engine = CBIR_Engine()
    
    """
    Permet de gèrer les erreurs HTTP, et de les logger sans avoir a descendre
    dans le collecteur d'erreurs.
    
    @param image_url L'URL de l'image du Tweet.
    @param tweet_id L'ID du Tweet (Uniquement pour les "print()").
    @param download_image_times Utilisé pour la classe "Tweets_Indexer".
    @param calculate_features_times Utilisé pour la classe "Tweets_Indexer".
    
    @return L'empreinte de l'image, calculées par le moteur CBIR,
            OU None si il y a un un problème.
    """
    def get_image_hash ( self, image_url : str, tweet_id, CAN_RETRY = [False],
                         download_image_times = None, calculate_features_times = None ) -> int :
        retry_count = 0
        while True : # Solution très bourrin pour gèrer les rate limits
            try :
                if download_image_times != None : start = time()
                image = get_tweet_image( image_url )
                if image == None : # Erreurs insolvables, 404 par exemple
                    return None
                if download_image_times != None : download_image_times.append( time() - start )
                
                if calculate_features_times != None : start = time()
                to_return = self.cbir_engine.index_cbir( binary_image_to_PIL_image( image ) )
                if calculate_features_times != None : calculate_features_times.append( time() - start )
                return to_return
            
            # Envoyé par la fonction get_tweet_image() qui n'a pas réussi
            except urllib.error.HTTPError as error :
                print( f"[get_image_hash] Erreur avec le Tweet ID {tweet_id} !" )
                print( error )
                print( "[get_image_hash] Abandon !" )
                
                # Ne pas journaliser les erreurs connues qui arrivent souvent
                # Elles ne sont pas solutionnables, ce sont des problèmes chez Twitter
                # 502 = Bad Gateway
                # 504 = Gateway Timeout
                if not error.code in [502, 504] :
                    file = open( "class_CBIR_Engine_for_Tweets_Images_errors.log", "a" )
                    file.write( f"Erreur avec le Tweet ID {tweet_id} !\n" )
                    traceback.print_exc( file = file )
                    file.write( "\n\n\n" )
                    file.close()
                
                CAN_RETRY[0] = True
                return None
            
            except Exception as error :
                print( f"[get_image_hash] Erreur avec le Tweet ID {tweet_id} !" )
                print( error )
                
                if retry_count < 1 : # Essayer un coup d'attendre
                    print( "[get_image_hash] On essaye d'attendre 10 secondes..." )
                    sleep( 10 )
                    retry_count += 1
                
                else :
                    print( "[get_image_hash] Abandon !" )
                    
                    file = open( "class_CBIR_Engine_for_Tweets_Images_errors.log", "a" )
                    file.write( f"Erreur avec le Tweet ID {tweet_id} !\n" )
                    traceback.print_exc( file = file )
                    file.write( "\n\n\n" )
                    file.close()
                    
                    CAN_RETRY[0] = True
                    return None
