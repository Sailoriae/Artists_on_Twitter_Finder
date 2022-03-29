#!/usr/bin/python3
# coding: utf-8

from bs4 import BeautifulSoup
from json import loads as json_loads
from typing import List
import re
from dateutil import parser

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
    change_wdir( "../.." )
    path.append(get_wdir())

from link_finder.supported_websites.utils.get_with_rate_limits import get_with_rate_limits
from link_finder.supported_websites.utils.validate_twitter_account_url import validate_twitter_account_url


# ^ = Début de la chaine
pixiv_artwork_id_regex_new = re.compile(
    r"^http(?:s)?:\/\/(?:www\.)?pixiv\.net\/(?:en\/)?artworks\/([0-9]+)(?:#([0-9]+))?(?:\/)?" )
pixiv_artwork_id_regex_old = re.compile(
    r"^http(?:s)?:\/\/(?:www\.)?pixiv\.net\/(?:en\/)?member_illust\.php\?(?:[a-zA-Z0-9=_\-&]+)?illust_id=([0-9]+)(?:#([0-9]+))?(?:\/)?" )

"""
Couche d'abstraction à la librairie PixivPy3 pour utiliser l'API publique de
Pixiv.

Cette classe garde en cache le dernier appel à l'API.
Ainsi, afin d'optimiser l'utilisation de cette classe, il faut :
- Initialiser un objet qu'une seule fois pour un thread, et le réutiliser.
- Ne surtout pas partager l'objet entre plusieurs threads.
- Et exécuter les deux méthodes get_image_urls() et get_twitter_accounts() l'une
  après l'autre pour une même illustration (C'est à dire ne pas mélanger les
  illustrations).
"""
class Pixiv :
    """
    @param username Le nom d'utilisateur Pixiv du compte à utiliser pour l'API.
    @param password Le mot de passe du compte Pixiv à utiliser pour l'API.
    """
    def __init__  ( self ) :
        # On utilise ces attributs pour mettre en cache le résultat de l'appel
        # à l'API pour une illustration.
        # On met en cache car la demande de l'URL de l'image et la demande des
        # URLs des comptes Twitter sont souvent ensembles.
        self._cache_illust_url : str = None
        self._cache_illust_id : int = None
        self._cache_illust_position : int = 1 # Première image par défaut
        self._cache_illust_url_json : dict = None
    
    """
    Permet d'extraire l'ID de l'URL d'une illustration postée sur Pixiv.
    @param artwork_url L'URL à examiner.
    @return True si l'URL mène à une illustration sur Pixiv.
            False sinon.
    """
    def _artwork_url_to_id ( self, artwork_url : str ) -> int :
        # Reset les valeurs qu'on est censé écrire
        self._cache_illust_id = None
        self._cache_illust_position = 1
        
        result = re.match( pixiv_artwork_id_regex_new, artwork_url )
        if result == None :
            result = re.match( pixiv_artwork_id_regex_old, artwork_url )
        if result == None :
            return False
        
        try :
            self._cache_illust_id = int( result.group( 1 ) )
        except ValueError :
            return False
        else :
            if result.group( 2 ) != None :
                position = int( result.group( 2 ) )
                if position != 0 and position <= 200 : # Position impossible
                    self._cache_illust_position = position
            return True
    
    """
    Mettre en cache le résultat de l'appel à l'API de l'illustration si ce
    n'est pas déjà fait.
    Permet de MàJ le cache, si l'URL mène bien vers une illustration.
    
    @param illust_id L'URL de l'illustration Pixiv.
    @return True si l'URL mène à une illustration sur Pixiv.
            False sinon.
    """
    def _cache_or_get ( self, illust_url : int ) -> bool :
        if illust_url != self._cache_illust_url :
            # Reset les valeurs qu'on est censé écrire
            self._cache_illust_url = None
            self._cache_illust_url_json = None
            
            if not self._artwork_url_to_id( illust_url ) :
                return False
            
            response = get_with_rate_limits( "https://www.pixiv.net/en/artworks/" + str(self._cache_illust_id) )
            
            if response.status_code == 404 :
                return False
            
            soup = BeautifulSoup( response.text, "html.parser" )
            meta = soup.find( "meta", id="meta-preload-data" )
            json = json_loads( meta["content"] )
            
            self._cache_illust_url = illust_url
            self._cache_illust_url_json = json
        
        return True
    
    """
    Obtenir l'URL de l'image source à partir de l'URL de l'illustration postée.
    
    @param illust_url L'URL de l'illustration Pixiv.
    @return Liste contenant deux URL de l'image (La première est la résolution
            originale de l'image, la seconde est redimensionnée).
            Ou None si il y a eu un problème, c'est à dire que l'ID donné n'est
            pas une illustration sur Pixiv.
    """
    def get_image_urls ( self, illust_url : int ) -> List[str] :
        # On met en cache si ce n'est pas déjà fait
        if not self._cache_or_get( illust_url ) :
            return None
        
        image_dict = None
        
        # Sur Pixiv, il peut y avoir plusieurs illustrations sur une même page
        # On est obligé de refaire un GET pour avoir les URL de toutes les
        # illustrations sur cette page (Sauf si on veut la première)
        pages_count = self._cache_illust_url_json["illust"][str(self._cache_illust_id)]["pageCount"]
        if ( 2 <= self._cache_illust_position and
             self._cache_illust_position <= pages_count ) :
            response = get_with_rate_limits( f"https://www.pixiv.net/ajax/illust/{str(self._cache_illust_id)}/pages" )
            json = response.json()
            image_dict = json["body"][ self._cache_illust_position - 1 ]
        
        # Si on veut la première image, pas besoin de refaire un GET
        else :
            image_dict = self._cache_illust_url_json["illust"][str(self._cache_illust_id)]
        
        # On retourne le résultat voulu
        return [ image_dict["urls"]["original"],
                 image_dict["urls"]["regular"] ]
    
    """
    Retourne les noms des comptes Twitter trouvés.
    
    @param illust_url L'URL de l'illustration Pixiv.
    @param force_pixiv_account_id Forcer l'ID du compte Pixiv (OPTIONNEL).
    @param multiplexer Méthode "link_mutiplexer()" de la classe "Link_Finder"
                       (OPTIONNEL).
    
    @return Une liste de comptes Twitter.
            Ou une liste vide si aucun URL de compte Twitter valide n'a été
            trouvé.
            Ou None si il y a eu un problème, c'est à dire que l'ID donné n'est
            pas une illustration sur Pixiv.
    """
    def get_twitter_accounts ( self, illust_url : int,
                                     force_pixiv_account_id = None,
                                     multiplexer = None ) -> List[str] :
        if force_pixiv_account_id != None :
            user_id = force_pixiv_account_id
        
        else :
            # On met en cache si ce n'est pas déjà fait
            if not self._cache_or_get( illust_url ) :
                return None
            user_id = self._cache_illust_url_json["illust"][str(self._cache_illust_id)]["userId"]
        
        artist_pixiv_page = "https://www.pixiv.net/en/users/" + str(user_id)
        
        # Si on a le multiplexeur de liens (Et qu'on n'est pas appelé par lui),
        # il vaut mieux passer par lui pour scanner la page de l'artiste,
        # plutôt que de le faire nous-même. Cela  permet qu'il enregistre dans
        # son dictionnaire qu'il est bien passé par cette page, et donc empêche
        # d'y passer deux fois.
        if force_pixiv_account_id == None and multiplexer != None :
            return multiplexer( artist_pixiv_page )
        
        twitter_accounts = []
        response = get_with_rate_limits( artist_pixiv_page )
        
        # Les comptes suspendus retournent HTTP 403
        if response.status_code in [403, 404] :
            return None
        
        soup = BeautifulSoup( response.text, "html.parser" )
        meta = soup.find( "meta", id="meta-preload-data" )
        json = json_loads( meta["content"] )
        
        # On peut trouver un compte Twitter dans le champs "webpage"
        try :
            temp = json["user"][str(user_id)]["webpage"]
        except KeyError :
            pass
        else :
            if temp != None :
                if multiplexer != None :
                    get_multiplex = multiplexer( temp )
                    if get_multiplex != None :
                        twitter_accounts += get_multiplex
                else :
                    temp = validate_twitter_account_url( temp )
                    if temp != None :
                        twitter_accounts.append( temp )
        
        # Chercher dans le champs dédié au compte Twitter
        try :
            if json["user"][str(user_id)]["social"] != [] :
                temp = json["user"][str(user_id)]["social"]["twitter"]["url"]
            else :
                temp = None
        except KeyError :
            pass
        else :
            if temp != None :
                temp = validate_twitter_account_url( temp )
                if temp != None :
                    twitter_accounts.append( temp )
        
        # On peut aussi trouver un lien dans la bio de l'artiste, si vraiment
        # il n'a pas envie d'utiliser le champs dédié
        # Attention : La bio ne convertit pas les liens, on peut donc en
        # chercher qu'un seul
        try :
            temp = json["user"][str(user_id)]["comment"]
        except KeyError :
            pass
        else :
            temp = validate_twitter_account_url( temp )
            if temp != None :
                twitter_accounts.append( temp )
        
        return twitter_accounts
    
    """
    Obtenir la date de publication de l'illustration.
    
    @param illust_url L'URL de l'illustration postée sur Pixiv.
    @return L'objet datetime de la date de publication de l'image.
            Ou None si il y a  eu un problème, c'est à dire que l'URL donnée
            ne mène pas à une illustration sur Pixiv.
    """
    def get_datetime ( self, illust_url  : str ) -> str :
        # On met en cache si ce n'est pas déjà fait
        if not self._cache_or_get( illust_url ) :
            return None
        
        # On retourne le résultat voulu
        return parser.isoparse( self._cache_illust_url_json["illust"][str(self._cache_illust_id)]["createDate"] )
