#!/usr/bin/python3
# coding: utf-8

from typing import List
import re
from datetime import datetime

try :
    from utils import Webpage_to_Twitter_Accounts
    from utils import validate_pixiv_account_url
    from utils import get_with_rate_limits
    from utils import validate_url
except ImportError : # Si on a été exécuté en temps que module
    from .utils import Webpage_to_Twitter_Accounts
    from .utils import validate_pixiv_account_url
    from .utils import get_with_rate_limits
    from .utils import validate_url


# ^ = Début de la chaine
danbooru_post_id_regex = re.compile(
    r"^http(?:s)?:\/\/danbooru\.donmai\.us\/posts\/([0-9]+)(?:\/)?" )


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
                    print( "[Danbooru] Erreur :", json["message"] )
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
    @param multiplexer Méthode "link_mutiplexer()" de la classe "Link_Finder"
                       (OPTIONNEL).
    
    @return Une liste de comptes Twitter.
            Ou une liste vide si aucun URL de compte Twitter valide n'a été
            trouvé.
            Ou None si il y a eu un problème, c'est à dire que l'ID donné n'est
            pas une illustration sur Danbooru.
    """
    def get_twitter_accounts ( self, illust_url : int,
                                     multiplexer = None ) -> List[str] :
        # On met en cache si ce n'est pas déjà fait
        if not self.cache_or_get( illust_url ) :
            return None
        
        # Il peut y avoir plusieurs artistes
        # Dans ce cas, on cherche les comptes Twitter de tous les artistes
        artists_tags = self.cache_illust_url_json["tag_string_artist"].split(" ")
        
        if artists_tags == [""] :
            return []
        
        twitter_accounts = []
        
        # SCAN PAGE DU TAG DE L'ARTISTE
        
        for artist_tag in artists_tags :
            # Problème Danbooru : Le JSON d'une page sur un tag ne donne pas les
            # URL qu'ils ont trouvés. Donc on doit le faire sur une page HTML.
            scanner = Webpage_to_Twitter_Accounts(
                "https://danbooru.donmai.us/artists/show_or_new?name=" + artist_tag,
                )
            
            # Se concentrer que sur la div contenant les données.
            scanner.soup = scanner.soup.find("div", {"id": "c-artists"})
            
            # Rechercher (Désactiver car le multiplexeur les cherche aussi)
            if multiplexer == None :
                twitter_accounts += scanner.scan()
            
            # Envoyer dans le multiplexer les autres URL qu'on peut trouver
            if multiplexer != None :
                for link in scanner.scan( validator_function = validate_url ) :
                    get_multiplex = multiplexer( link, source = "danbooru" )
                    if get_multiplex != None :
                        twitter_accounts += get_multiplex
        
        return twitter_accounts
    
    """
    Obtenir la date de publication de l'illustration.
    
    @param illust_id L'URL de l'illustration postée sur Danbooru.
    @return L'objet datetime de la date de publication de l'image.
            Ou None si il y a  eu un problème, c'est à dire que l'URL donnée
            ne mène pas à une illustration sur Danbooru.
    """
    def get_datetime ( self, illust_url  : str ) -> str :
        # On met en cache si ce n'est pas déjà fait
        if not self.cache_or_get( illust_url ) :
            return None
        
        # On retourne le résultat voulu
        return datetime.fromisoformat( self.cache_illust_url_json["created_at"] )


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
