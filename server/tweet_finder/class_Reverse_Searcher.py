#!/usr/bin/python3
# coding: utf-8

from time import time
from PIL import Image

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

from tweet_finder.cbir_engine.class_CBIR_Engine import CBIR_Engine
from tweet_finder.database.class_SQLite_or_MySQL import SQLite_or_MySQL
from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction
import parameters as param


class Unfound_Account_on_Reverse_Searcher ( Exception ) :
    pass
class Account_Not_Indexed ( Exception ) :
    pass


class Reverse_Searcher :
    """
    Constructeur.
    
    @param add_step_3_times Fonction de la mémoire, objet
                            "Metrics_Container".
    """
    def __init__ ( self, DEBUG : bool = False, ENABLE_METRICS : bool = False,
                         add_step_3_times = None, # Fonction de la mémoire partagée
                  ) -> None :
        self._DEBUG = DEBUG
        self._ENABLE_METRICS = ENABLE_METRICS
        self._add_step_3_times = add_step_3_times
        
        self._cbir_engine = CBIR_Engine()
        self._bdd = SQLite_or_MySQL()
        self._twitter = TweepyAbstraction( param.API_KEY,
                                           param.API_SECRET,
                                           param.OAUTH_TOKEN,
                                           param.OAUTH_TOKEN_SECRET )
    
    """
    Recherche d'un Tweet dans la base de donnée à partir d'une image.
    
    @param pil_image L'image de requête, au format PIL.Image
    @param account_name Le nom du compte Twitter dans lequel chercher, c'est à
                        dire ce qu'il y a après le @ (OPTIONNEL)
    @param account_id ID du compte, vérifié récemment ! (OPTIONNEL)
                      Prime sur "account_name" si nen correspondent pas
    
    @return Liste d'objets Image_in_DB, contenant les attributs suivants :
            - account_id : L'ID du compte Twitter
            - tweet_id : L'ID du Tweet contenant l'image
            - distance : La distance calculée avec l'image de requête
            - image_position : La position de l'image dans le Tweet (1-4)
    
    Peut émettre une exception "Unfound_Account_on_Reverse_Searcher" si le
    compte est introuvable.
    Peut émettre des "Account_Not_Indexed" si le compte n'est pas indexé.
    """
    def search_tweet ( self, pil_image : Image,
                             account_name : str = None,
                             account_id : int = None ) :
        if account_name != None and account_id == None :
            account_id = self._twitter.get_account_id( account_name )
            if account_id == None :
                print( f"[Reverse_Searcher] Compte @{account_name} inexistant, ou désactivé, ou privé !" )
                raise Unfound_Account_on_Reverse_Searcher
            if not self._bdd.is_account_indexed( account_id ) :
                print( f"[Reverse_Searcher] Compte @{account_name} non-indexé !" )
                raise Account_Not_Indexed
        elif account_name == None :
            account_id = 0
        
        if self._DEBUG or self._ENABLE_METRICS :
            start = time()
        
        iterator = self._bdd.get_images_in_db_iterator( account_id = account_id,
                                                        add_step_3_times = self._add_step_3_times )
        
        to_return = self._cbir_engine.search_cbir( pil_image, iterator )
        
        if self._DEBUG or self._ENABLE_METRICS :
            print( f"[Reverse_Searcher] La recherche s'est faite en {time() - start :.5g} secondes." )
            if self._add_step_3_times != None :
                self._add_step_3_times( [ time() - start ], None, None, None )
        
        return to_return
    
    """
    Recherche exacte d'un Tweet dans la base de donnée à partir d'une image.
    A la différence de la méthode précédente, cette méthode fait une recherche
    exacte, c'est à dire que les images retournées ont la même empreinte que
    l'image de requête.
    
    Cette recherche est beaucoup plus rapide, permettant une recherche dans
    toute la base de données.
    Cependant, à cause de la compression Twitter, il y a environ 10% de faux
    négatifs (C'est à dire des résultats qui ont une distance > à 0 avec la
    méthode de recherche précédente).
    
    Cette méthode n'enregistre pas les temps de processus !
    
    ATTENTION : Malgré sa vitesse, cette méthode reste lente lors d'une
    recherche dans toute la base de données ! Ce n'est pas forcément une bonne
    idée de la proposer sur le front-end ou sur l'API.
    
    @param pil_image L'image de requête, au format PIL.Image
    @param account_name Le nom du compte Twitter dans lequel chercher, c'est à
                        dire ce qu'il y a après le @ (OPTIONNEL)
    @param account_id ID du compte, vérifié récemment ! (OPTIONNEL)
                      Prime sur "account_name" si nen correspondent pas
    
    @return Liste d'objets Image_in_DB, contenant les attributs suivants :
            - account_id : L'ID du compte Twitter
            - tweet_id : L'ID du Tweet contenant l'image
            - distance : La distance calculée avec l'image de requête
                         Ici, cette distance est forcément de 0
            - image_position : La position de l'image dans le Tweet (1-4)
    
    Peut émettre une exception "Unfound_Account_on_Reverse_Searcher" si le
    compte est introuvable.
    Peut émettre des "Account_Not_Indexed" si le compte n'est pas indexé.
    """
    def search_exact_tweet ( self, pil_image : Image,
                                   account_name : str = None,
                                   account_id : int = None ) :
        if account_name != None and account_id == None :
            account_id = self._twitter.get_account_id( account_name )
            if account_id == None :
                print( f"[Reverse_Searcher] Compte @{account_name} inexistant, ou désactivé, ou privé !" )
                raise Unfound_Account_on_Reverse_Searcher
            if not self._bdd.is_account_indexed( account_id ) :
                print( f"[Reverse_Searcher] Compte @{account_name} non-indexé !" )
                raise Account_Not_Indexed
        elif account_name == None :
            account_id = 0
        
        if self._DEBUG or self._ENABLE_METRICS :
            start = time()
        
        image_hash = self._cbir_engine.index_cbir( pil_image )
        to_return = list( self._bdd.exact_image_hash_search( image_hash, account_id = account_id ) )
        
        if self._DEBUG or self._ENABLE_METRICS :
            print( f"[Reverse_Searcher] La recherche exacte s'est faite en {time() - start :.5g} secondes." )
        
        return to_return
