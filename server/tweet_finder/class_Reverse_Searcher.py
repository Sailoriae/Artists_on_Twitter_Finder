#!/usr/bin/python3
# coding: utf-8

from cv2 import error as ErrorOpenCV
from time import time

try :
    from cbir_engine import CBIR_Engine
    from database import SQLite_or_MySQL
    from twitter import TweepyAbstraction
    from utils import url_to_cv2_image, binary_image_to_cv2_image
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .cbir_engine import CBIR_Engine
    from .database import SQLite_or_MySQL
    from .twitter import TweepyAbstraction
    from .utils import url_to_cv2_image, binary_image_to_cv2_image

# Ajouter le répertoire parent au PATH pour pouvoir importer les paramètres
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))
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
                             add_step_3_times = None,
                             query_image_binary : bytes = None ) :
        if account_name != None :
            account_id = self.twitter.get_account_id( account_name )
            if account_id == None :
                print( "Compte @", account_name, "inexistant, ou désactivé, ou privé !" )
                return None
        else :
            account_id = 0
        
        try :
            if query_image_binary == None :
                image = url_to_cv2_image( image_url )
            else :
                image = binary_image_to_cv2_image( query_image_binary )
        except Exception as error :
            print( "L'URL \"" + str(image_url) + "\" ne mène pas à une image !" )
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
            print( "La recherche s'est faite en", time() - start, "secondes." )
        
        # Suppression des attributs "image_features" pour gagner un peu de
        # mémoire
        for image in to_return :
            image.image_features = []
        
        # Retourner
        return to_return
