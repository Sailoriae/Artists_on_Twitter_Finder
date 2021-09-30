#!/usr/bin/python3
# coding: utf-8

from time import time
from PIL import Image

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
from tweet_finder.database.class_SQLite_or_MySQL import SQLite_or_MySQL
from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction
import parameters as param


class Reverse_Searcher :
    def __init__ ( self, DEBUG : bool = False, ENABLE_METRICS : bool = False ) :
        self._DEBUG = DEBUG
        self._ENABLE_METRICS = ENABLE_METRICS
        self._cbir_engine = CBIR_Engine()
        self._bdd = SQLite_or_MySQL()
        self._twitter = TweepyAbstraction( param.API_KEY,
                                           param.API_SECRET,
                                           param.OAUTH_TOKEN,
                                           param.OAUTH_TOKEN_SECRET )
    
    """
    Rechercher un tweet dans la base de donnée grâce à une image
    @param pil_image L'image de requête, au format PIL.Image
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
            None si "account_name" est inexistant, ou désactivé, ou privé
    """
    def search_tweet ( self, pil_image : Image,
                             account_name : str = None,
                             account_id : int = None,
                             add_step_3_times = None,
                             query_image_binary : bytes = None ) :
        if account_name != None or account_id != None:
            if account_id == None :
                account_id = self._twitter.get_account_id( account_name )
            if account_id == None :
                print( f"Compte @{account_name} inexistant, ou désactivé, ou privé !" )
                return None
        else :
            account_id = 0
        
        if self._DEBUG or self._ENABLE_METRICS :
            start = time()
        
        iterator = self._bdd.get_images_in_db_iterator( account_id = account_id,
                                                       add_step_3_times = add_step_3_times )
        
        to_return = self._cbir_engine.search_cbir( pil_image, iterator )
        
        if self._DEBUG or self._ENABLE_METRICS :
            print( f"[Reverse_Searcher] La recherche s'est faite en {time() - start} secondes." )
            add_step_3_times( [ time() - start ], [], [], [] )
        
        # Suppression des attributs "image_features" pour gagner un peu de
        # mémoire
        for image in to_return :
            image.image_features = []
        
        # Retourner
        return to_return
