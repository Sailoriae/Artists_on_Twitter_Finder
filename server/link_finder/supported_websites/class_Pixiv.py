#!/usr/bin/python3
# coding: utf-8

import pixivpy3
from typing import List
import re

try :
    from utils import validate_twitter_account_url
except ImportError : # Si on a été exécuté en temps que module
    from .utils import validate_twitter_account_url


# ^ = Début de la chaine
pixiv_artwork_id_regex_new = re.compile(
    "^http(?:s)?:\/\/(?:www\.)?pixiv\.net\/(?:en\/)?artworks\/([0-9]+)(?:\/)?" )
pixiv_artwork_id_regex_old = re.compile(
    "^http(?:s)?:\/\/(?:www\.)?pixiv\.net\/(?:en\/)?member_illust\.php\?(?:[a-zA-Z0-9=_\-&]+)?illust_id=([0-9]+)(?:\/)?" )

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
    def __init__  ( self,
                   username : str,
                   password : str ) :
        self.api = pixivpy3.AppPixivAPI()
        self.api.login( username, password )
        
        # On utilise ces attributs pour mettre en cache le résultat de l'appel
        # à l'API pour une illustration.
        # On met en cache car la demande de l'URL de l'image et la demande des
        # URLs des comptes Twitter sont souvent ensembles.
        self.cache_illust_url = None
        self.cache_illust_url_json = None
    
    """
    Permet d'extraire l'ID de l'URL d'une illustration postée sur Pixiv.
    @param artwork_url L'URL à examiner.
    @return L'ID de l'illustration postée sur Pixiv.
            Ou None si ce n'est pas un artwork Pixiv.
    """
    def artwork_url_to_id ( self, artwork_url : str ) :
        result_new = re.match( pixiv_artwork_id_regex_new, artwork_url )
        result_old = re.match( pixiv_artwork_id_regex_old, artwork_url )
        if result_new != None :
            return result_new.group( 1 )
        if result_old != None :
            return result_old.group( 1 )
        return None
    
    """
    METHODE PRIVEE, NE PAS UTILISER !
    Mettre en cache le résultat de l'appel à l'API de l'illustration si ce
    n'est pas déjà fait.
    Permet de MàJ le cache, si l'URL mène bien vers une illustration.
    param illust_id L'URL de l'illustration Pixiv.
    
    @return True si l'URL donné est utilisable.
            False sinon.
    """
    def cache_or_get ( self, illust_url : int ) -> bool :
        if illust_url != self.cache_illust_url :
            illust_id = self.artwork_url_to_id( illust_url )
            json = self.api.illust_detail( illust_id )
            
            try :
                json["error"]
            # S'il n'y a pas d'erreur dans le JSON retourné, c'est que c'est OK
            except KeyError :
                self.cache_illust_url = illust_url
                self.cache_illust_url_json = json
                return True
            else :
                return False
        
        return True
    
    """
    Obtenir l'URL de l'image source à partir de l'URL de l'illustration postée.
    
    @param illust_id L'URL de l'illustration Pixiv.
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
        # Ce qui fait que plusieurs tweets séraient retournés, et ça serait à
        # l'utilisateur de choisir quel est le tweet qui contient l'image
        # qu'il voulait.
        # 
        # Cela serait impossible dans le cas d'un robot qui utilise notre
        # système !
        # Il faudrait donc revoir beaucoup de choses...
        return self.cache_illust_url_json["illust"]["image_urls"]["large"]
    
    """
    Retourne les noms des comptes Twitter trouvés.
    
    @param illust_id L'URL de l'illustration Pixiv.
    @param force_pixiv_account_id Forcer l'ID du compte Pixiv (OPTIONNEL).
    @return Une liste de comptes Twitter.
            Ou une liste vide si aucun URL de compte Twitter valide n'a été
            trouvé.
            Ou None si il y a eu un problème, c'est à dire que l'ID donné n'est
            pas une illustration sur Pixiv.
    """
    def get_twitter_accounts ( self, illust_url : int,
                               force_pixiv_account_id = None ) -> List[str] :
        if force_pixiv_account_id != None :
            user_id = force_pixiv_account_id
        
        else :
            # On met en cache si ce n'est pas déjà fait
            if not self.cache_or_get( illust_url ) :
                return None
            user_id = self.cache_illust_url_json["illust"]["user"]["id"]
        
        user_id_json = self.api.user_detail( user_id )
        
        twitter_accounts = []
        
        # On peut trouver un compte Twitter dans le champs "webpage"
        try :
            temp = user_id_json["profile"]["webpage"]
        except KeyError :
            pass
        else :
            if temp != None :
                temp = validate_twitter_account_url( temp )
                if temp != None :
                    twitter_accounts.append( temp )
        
        try :
            temp = user_id_json["profile"]["twitter_url"]
        except KeyError :
            pass
        else :
            if temp != None :
                temp = validate_twitter_account_url( temp )
                if temp != None :
                    twitter_accounts.append( temp )
        
        return twitter_accounts
