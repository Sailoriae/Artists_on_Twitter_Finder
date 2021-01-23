#!/usr/bin/python3
# coding: utf-8

from cv2 import error as ErrorOpenCV
from time import time

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendemment (Notemment pour des
# tests), il faut que son répertoire de travail soit ce même répertoire
if __name__ == "__main__" :
    from os.path import abspath as get_abspath
    from os.path import dirname as get_dirname
    from os import chdir as change_wdir
    change_wdir(get_dirname(get_abspath(__file__)))
    change_wdir( ".." )

from tweet_finder.cbir_engine.class_CBIR_Engine import CBIR_Engine
from tweet_finder.database.class_SQLite_or_MySQL import SQLite_or_MySQL
from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction
from tweet_finder.utils.url_to_cv2_image import url_to_cv2_image
from tweet_finder.utils.url_to_cv2_image import binary_image_to_cv2_image
import parameters as param


class Reverse_Searcher :
    def __init__ ( self, DEBUG : bool = False, ENABLE_METRICS : bool = False ) :
        self.DEBUG = DEBUG
        self.ENABLE_METRICS = ENABLE_METRICS
        self.cbir_engine = CBIR_Engine()
        self.bdd = SQLite_or_MySQL()
        self.twitter = TweepyAbstraction( param.API_KEY,
                                         param.API_SECRET,
                                         param.OAUTH_TOKEN,
                                         param.OAUTH_TOKEN_SECRET )
    
    """
    Rechercher un tweet dans la base de donnée grâce à une image
    @param image_url L'URL de l'image à chercher
    @param account_name Le nom du compte Twitter dans lequel chercher, c'est à
                        dire ce qu'il y a après le @ (OPTIONNEL)
    @param account_id ID du compte, vérifié récemment ! (OPTIONNEL)
                      Prime sur "account_name" si nen correspondent pas
    @param query_image_binary Ne pas faire de GET à l'URL passée, mais prendre
                              plutôt cette image déjà téléchargée (OPTIONNEL)
    @return Liste d'objets Image_in_DB, contenant les attributs suivants :
            - account_id : L'ID du compte Twitter
            - tweet_id : L'ID du Tweet contenant l'image
            - distance : La distance calculée avec l'image de requête
            - image_position : La position de l'image dans le Tweet (1-4)
            None si il y a eu un problème
    """
    def search_tweet ( self, image_url : str,
                             account_name : str = None,
                             account_id : int = None,
                             add_step_3_times = None,
                             query_image_binary : bytes = None ) :
        if account_name != None or account_id != None:
            if account_id == None :
                account_id = self.twitter.get_account_id( account_name )
            if account_id == None :
                print( f"Compte @{account_name} inexistant, ou désactivé, ou privé !" )
                return None
        else :
            account_id = 0
        
        try :
            if query_image_binary == None :
                image = url_to_cv2_image( image_url )
            else :
                image = binary_image_to_cv2_image( query_image_binary )
        except Exception as error :
            print( f"L'URL \"{image_url}\" ne mène pas à une image !" )
            print( error )
            return None
        
        if self.DEBUG or self.ENABLE_METRICS :
            start = time()
        
        iterator = self.bdd.get_images_in_db_iterator( account_id )
        iterator.add_step_3_times = add_step_3_times
        
        try :
            to_return = self.cbir_engine.search_cbir( image, iterator )
        # Si j'amais l'image passée a un format à la noix et fait planter notre
        # moteur CBIR
        except ErrorOpenCV :
            print( ErrorOpenCV )
            return None
        
        if self.DEBUG or self.ENABLE_METRICS :
            print( f"La recherche s'est faite en {time() - start} secondes." )
        
        # Suppression des attributs "image_features" pour gagner un peu de
        # mémoire
        for image in to_return :
            image.image_features = []
        
        # Retourner
        return to_return
