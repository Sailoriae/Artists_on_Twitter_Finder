#!/usr/bin/python3
# coding: utf-8

import traceback
import urllib
from time import sleep

try :
    from cbir_engine import CBIR_Engine
    from utils import url_to_cv2_image
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .cbir_engine import CBIR_Engine
    from .utils import url_to_cv2_image


class CBIR_Engine_for_Tweets_Images :
    def __init__( self, DEBUG : bool = False ) :
        self.DEBUG = DEBUG
        self.cbir_engine = CBIR_Engine()
    
    """
    Permet de gèrer les erreurs HTTP, et de les logger sans avoir a descendre
    dans le collecteur d'erreurs.
    
    @param image_url L'URL de l'image du Tweet.
    @param tweet_id L'ID du Tweet (Uniquement pour les "print()").
    @return La liste des caractéristiques calculées par le moteur CBIR,
            OU None si il y a un un problème.
    """
    def get_image_features ( self, image_url : str, tweet_id ) :
        retry_count = 0
        while True : # Solution très bourrin pour gèrer les rate limits
            try :
                return self.cbir_engine.index_cbir( url_to_cv2_image( image_url ) )
                break
            
            # Oui, c'est possible, Twitter n'est pas parfait
            # Exemple : https://twitter.com/apofissx/status/219051550696407040
            # Ce tweet est indiqué comme ayant une image, mais elle est en 404 !
            except urllib.error.HTTPError as error :
                if error.code == 404 or error.code == 500 or error.code == 403 : # Erreurs insolvables
                    print( "Erreur avec le Tweet : " + str(tweet_id) + " !" )
                    print( error )
                    return None
                else :
                    print( "Erreur avec le Tweet : " + str(tweet_id) + " !" )
                    print( error )
                    print( "On essaye d'attendre 10 secondes..." )
                    if error.code == 502 : # Il suffit d'attendre pour ce genre d'erreurs
                        if retry_count < 5 : # Essayer d'attendre, au maximum 5 coups
                            sleep( 10 )
                            retry_count += 1
                    elif retry_count < 1 : # Essayer un coup d'attendre
                        sleep( 10 )
                        retry_count += 1
                    else :
                        file = open( "class_CBIR_Engine_with_Database_errors.log", "a" )
                        file.write( "Erreur avec le Tweet : " + str(tweet_id) + " !\n" )
                        traceback.print_exc( file = file )
                        file.write( "\n\n\n" )
                        file.close()
                        return None
            
            except Exception as error :
                print( "Erreur avec le Tweet : " + str(tweet_id) + " !" )
                print( error )
                print( "On essaye d'attendre 10 secondes..." )
                if retry_count < 1 : # Essayer un coup d'attendre
                        sleep( 10 )
                        retry_count += 1
                else :
                    file = open( "class_CBIR_Engine_with_Database_errors.log", "a" )
                    file.write( "Erreur avec le Tweet : " + str(tweet_id) + " !\n" )
                    traceback.print_exc( file = file )
                    file.write( "\n\n\n" )
                    file.close()
                    return None
