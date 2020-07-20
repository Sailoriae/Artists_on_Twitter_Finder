#!/usr/bin/python3
# coding: utf-8

from typing import List
import re

try :
    from utils import Webpage_to_Twitter_Accounts
    from utils import validate_pixiv_account_url
    from utils import get_with_rate_limits
except ImportError : # Si on a été exécuté en temps que module
    from .utils import Webpage_to_Twitter_Accounts
    from .utils import validate_pixiv_account_url
    from .utils import get_with_rate_limits


# ^ = Début de la chaine
danbooru_post_id_regex = re.compile(
    "^http(?:s)?:\/\/danbooru\.donmai\.us\/posts\/([0-9]+)(?:\/)?" )


"""
Couche d'abstraction à l'API de Danbooru.
Attention ! Danbooru est un site de repost !

Cette classe garde en cache le dernier appel à l'API.
Ainsi, afin d'optimiser l'utilisation de cette classe, il faut :
- Initialiser un objet qu'une seule fois pour un thread, et le réutiliser.
- Ne surtout pas partager l'objet entre plusieurs threads.
- Et exécuter les deux méthodes get_image_url() et get_twitter_accounts() l'une
  après l'autre pour une même illustration (C'est à dire ne pas mélanger les
  illustrations).
"""
class Danbooru :
    def __init__  ( self ) :
        # On utilise ces attributs pour mettre en cache le résultat de l'appel
        # à l'API pour une illustration.
        # On met en cache car la demande de l'URL de l'image et la demande des
        # URLs des comptes Twitter sont souvent ensembles.
        self.cache_illust_url = None
        self.cache_illust_url_json = None
    
    """
    Permet d'extraire l'ID de l'URL d'une illustration postée sur Danbooru.
    @param artwork_url L'URL à examiner.
    @return L'ID de l'illustration postée sur Danbooru.
            Ou None si ce n'est pas un post sur Danbooru.
    """
    def artwork_url_to_id ( self, artwork_url : str ) :
        result = re.match( danbooru_post_id_regex, artwork_url )
        if result != None :
            return result.group( 1 )
        return None
    
    """
    METHODE PRIVEE, NE PAS UTILISER !
    Mettre en cache le résultat de l'appel à l'API de l'illustration si ce
    n'est pas déjà fait.
    Permet de MàJ le cache, si l'URL mène bien vers une illustration.
    param illust_id L'URL de l'illustration Danbooru.
    
    @return True si l'URL donné est utilisable.
            False sinon.
    """
    def cache_or_get ( self, illust_url : int ) -> bool :
        if illust_url != self.cache_illust_url :
            # Pour être certain de l'URL, on sort l'ID, pour reconstruire juste
            # après la même URL, avec juste ".json" au bout.
            illust_id = self.artwork_url_to_id( illust_url )
            if illust_id == None :
                return False
            
            response = get_with_rate_limits( "https://danbooru.donmai.us/posts/" + illust_id + ".json" )
            
            json = response.json()
            
            # Si il y a une clé "success" à False, c'est que ce n'est pas bon
            try :
                if json["success"] == False :
                    return False
            except KeyError :
                pass
            
            self.cache_illust_url = illust_url
            self.cache_illust_url_json = json
        
        return True
    
    """
    Obtenir l'URL de l'image source à partir de l'URL de l'illustration postée.
    
    @param illust_id L'URL de l'illustration postée sur Danbooru.
    @return L'URL de l'image.
            Ou None si il y a eu un problème, c'est à dire que l'ID donné n'est
            pas une illustration sur Danbooru.
    """
    def get_image_url ( self, illust_url : int ) -> str :
        # On met en cache si ce n'est pas déjà fait
        if not self.cache_or_get( illust_url ) :
            return None
        
        # On retourne le résultat voulu
        return self.cache_illust_url_json["file_url"]
    
    """
    Retourne les noms des comptes Twitter trouvés.
    
    @param illust_id L'URL de l'illustration postée sur Danbooru.
    @return Une liste de comptes Twitter.
            Ou une liste vide si aucun URL de compte Twitter valide n'a été
            trouvé.
            Ou None si il y a eu un problème, c'est à dire que l'ID donné n'est
            pas une illustration sur Danbooru.
    """
    def get_twitter_accounts ( self, illust_url : int ) -> List[str] :
        # On met en cache si ce n'est pas déjà fait
        if not self.cache_or_get( illust_url ) :
            return None
        
        artist_tag = self.cache_illust_url_json["tag_string_artist"]
        
        if artist_tag == "" :
            return []
        
        twitter_accounts = []
        
        # SCAN PAGE DU TAG DE L'ARTISTE
        
        # Problème Danbooru : Le JSON d'une page sur un tag ne donne pas les
        # URL qu'ils ont trouvés. Donc on doit le faire sur une page HTML.
        scanner = Webpage_to_Twitter_Accounts(
            "https://danbooru.donmai.us/artists/show_or_new?name=" + artist_tag,
            )
        
        # Se concentrer que sur la div contenant les données.
        scanner.soup = scanner.soup.find("div", {"id": "c-artists"})
        
        # On met en mode STRICT
        twitter_accounts += scanner.scan( STRICT = True )
        
        return twitter_accounts
    
    """
    Pour beaucoup d'artistes sur Danboru, on peut trouver leur compte Pixiv, et
    donc aller y chercher leurs éventuels comptes Twitter.
    
    @param illust_id L'URL de l'illustration postée sur Danbooru.
    @return Une liste d'ID de comptes Pixiv.
            Ou une liste vide si aucun URL de compte Pixiv valide n'a été
            trouvé.
            Ou None si il y a eu un problème, c'est à dire que l'ID donné n'est
            pas une illustration sur Danbooru.
    """
    def get_pixiv_accounts ( self, illust_url : int ) -> List[str] :
        # On met en cache si ce n'est pas déjà fait
        if not self.cache_or_get( illust_url ) :
            return None
        
        artist_tag = self.cache_illust_url_json["tag_string_artist"]
        
        if artist_tag == "" :
            return []
        
        pixiv_accounts = []
        
        # SCAN PAGE DU TAG DE L'ARTISTE
        
        # Problème Danbooru : Le JSON d'une page sur un tag ne donne pas les
        # URL qu'ils ont trouvés. Donc on doit le faire sur une page HTML.
        scanner = Webpage_to_Twitter_Accounts(
            "https://danbooru.donmai.us/artists/show_or_new?name=" + artist_tag,
            )
        
        # Se concentrer que sur la div contenant les données.
        scanner.soup = scanner.soup.find("div", {"id": "c-artists"})
        
        # On met en mode STRICT
        pixiv_accounts += scanner.scan(
            STRICT = True,
            validator_function = validate_pixiv_account_url )
        
        return pixiv_accounts


"""
Test du bon fonctionnement de cette classe
"""
if __name__ == '__main__' :
    danbooru = Danbooru()
    test_twitter = []
    test_twitter.append(
        danbooru.get_twitter_accounts(
            "https://danbooru.donmai.us/posts/3994568" ) )
    
    test_pixiv = []
    test_pixiv.append(
        danbooru.get_pixiv_accounts(
            "https://danbooru.donmai.us/posts/3994568" ) )
    
    if test_twitter == [['brillewind']] :
        print( "Tests Twitter OK !" )
    else :
        print( "Tests Twitter échoués !" )
        
    if test_pixiv == [['9224174']] :
        print( "Tests Pixiv OK !" )
    else :
        print( "Tests Pixiv échoués !" )
