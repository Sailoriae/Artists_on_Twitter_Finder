#!/usr/bin/python3
# coding: utf-8

from bs4 import BeautifulSoup
from json import loads as json_loads
from typing import List
import re
from dateutil import parser

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
    change_wdir( "../.." )
    path.append(get_wdir())

from link_finder.supported_websites.utils.get_with_rate_limits import get_with_rate_limits
from link_finder.supported_websites.utils.validate_twitter_account_url import validate_twitter_account_url


# ^ = Début de la chaine
pixiv_artwork_id_regex_new = re.compile(
    r"^http(?:s)?:\/\/(?:www\.)?pixiv\.net\/(?:en\/)?artworks\/([0-9]+)(?:\/)?" )
pixiv_artwork_id_regex_old = re.compile(
    r"^http(?:s)?:\/\/(?:www\.)?pixiv\.net\/(?:en\/)?member_illust\.php\?(?:[a-zA-Z0-9=_\-&]+)?illust_id=([0-9]+)(?:\/)?" )

"""
Couche d'abstraction à la librairie PixivPy3 pour utiliser l'API publique de
Pixiv.

Cette classe garde en cache le dernier appel à l'API.
Ainsi, afin d'optimiser l'utilisation de cette classe, il faut :
- Initialiser un objet qu'une seule fois pour un thread, et le réutiliser.
- Ne surtout pas partager l'objet entre plusieurs threads.
- Et exécuter les deux méthodes get_image_url() et get_twitter_accounts() l'une
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
        self.cache_illust_url = None
        self.cache_illust_id = None
        self.cache_illust_url_json = None
    
    """
    Permet d'extraire l'ID de l'URL d'une illustration postée sur Pixiv.
    @param artwork_url L'URL à examiner.
    @return L'ID de l'illustration postée sur Pixiv.
            Ou None si ce n'est pas un artwork Pixiv.
    """
    def artwork_url_to_id ( self, artwork_url : str ) -> int :
        result_new = re.match( pixiv_artwork_id_regex_new, artwork_url )
        result_old = re.match( pixiv_artwork_id_regex_old, artwork_url )
        if result_new != None :
            try :
                return int( result_new.group( 1 ) )
            except ValueError :
                return None
        if result_old != None :
            try :
                return int( result_old.group( 1 ) )
            except ValueError :
                return None
        return None
    
    """
    METHODE PRIVEE, NE PAS UTILISER !
    Mettre en cache le résultat de l'appel à l'API de l'illustration si ce
    n'est pas déjà fait.
    Permet de MàJ le cache, si l'URL mène bien vers une illustration.
    
    @param illust_id L'URL de l'illustration Pixiv.
    @return True si l'URL donné est utilisable.
            False sinon.
    """
    def cache_or_get ( self, illust_url : int ) -> bool :
        if illust_url != self.cache_illust_url :
            illust_id = self.artwork_url_to_id( illust_url )
            
            if illust_id == None :
                return False
            
            response = get_with_rate_limits( "https://www.pixiv.net/en/artworks/" + str(illust_id) )
            
            if response.status_code == 404 :
                return False
            
            soup = BeautifulSoup( response.text, "html.parser" )
            meta = soup.find( "meta", id="meta-preload-data" )
            json = json_loads( meta["content"] )
            
            self.cache_illust_url = illust_url
            self.cache_illust_id = illust_id
            self.cache_illust_url_json = json
        
        return True
    
    """
    Obtenir l'URL de l'image source à partir de l'URL de l'illustration postée.
    
    @param illust_url L'URL de l'illustration Pixiv.
    @return L'URL de l'image.
            Ou None si il y a eu un problème, c'est à dire que l'ID donné n'est
            pas une illustration sur Pixiv.
    """
    def get_image_url ( self, illust_url : int ) -> str :
        # On met en cache si ce n'est pas déjà fait
        if not self.cache_or_get( illust_url ) :
            return None
        
        # On retourne le résultat voulu
        # 
        # Problème avec Pixiv : Il peut y avoir plusieurs illustrations dans
        # une même page ! C'est chiant. On se contente donc de retourner que la
        # principale, c'est à dire la première.
        #
        # Comme l'utilisateur entre l'URL de la page, et non de l'image, on
        # devrait donc retourner ici une liste d'URL, et donc scanner plusieurs
        # images dans notre moteur CBIR.
        # Ce qui fait que plusieurs tweets seraient retournés, et ça serait à
        # l'utilisateur de choisir quel est le tweet qui contient l'image
        # qu'il voulait.
        # 
        # Cela serait impossible dans le cas d'un robot qui utilise notre
        # système !
        # Il faudrait donc revoir beaucoup de choses...
        return self.cache_illust_url_json["illust"][str(self.cache_illust_id)]["urls"]["original"]
    
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
            if not self.cache_or_get( illust_url ) :
                return None
            user_id = self.cache_illust_url_json["illust"][str(self.cache_illust_id)]["userId"]
        
        twitter_accounts = []
        response = get_with_rate_limits( "https://www.pixiv.net/en/users/" + str(user_id) )
            
        if response.status_code == 404 :
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
                    get_multiplex = multiplexer( temp, source = "pixiv" )
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
        if not self.cache_or_get( illust_url ) :
            return None
        
        # On retourne le résultat voulu
        return parser.isoparse( self.cache_illust_url_json["illust"][str(self.cache_illust_id)]["createDate"] )
