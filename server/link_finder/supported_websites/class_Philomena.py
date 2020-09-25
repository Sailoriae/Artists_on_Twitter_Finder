#!/usr/bin/python3
# coding: utf-8

from typing import List
import re
from datetime import datetime

try :
    from utils import Webpage_to_Twitter_Accounts
    from utils import get_with_rate_limits
    from utils import validate_url
except ImportError : # Si on a été exécuté en temps que module
    from .utils import Webpage_to_Twitter_Accounts
    from .utils import get_with_rate_limits
    from .utils import validate_url


# ^ = Début de la chaine
derpibooru_post_id_regex = re.compile(
    r"^http(?:s)?:\/\/(?:www\.)?derpibooru\.org\/(?:images\/)?([0-9]+)(?:\/)?" )
furbooru_post_id_regex = re.compile(
    r"^http(?:s)?:\/\/(?:www\.)?furbooru\.org\/(?:images\/)?([0-9]+)(?:\/)?" )


"""
Couche d'abstraction à l'API de Philomena.
Philomena est un logiciel pour créer des Boorus, et non un site !
https://github.com/derpibooru/philomena
Le plus gros Booru utilisant Philomena est Derpibooru.
Attention ! un Booru est un site de repost !

Cette classe garde en cache le dernier appel à l'API.
Ainsi, afin d'optimiser l'utilisation de cette classe, il faut :
- Initialiser un objet qu'une seule fois pour un thread, et le réutiliser.
- Ne surtout pas partager l'objet entre plusieurs threads.
- Et exécuter les deux méthodes get_image_url() et get_twitter_accounts() l'une
  après l'autre pour une même illustration (C'est à dire ne pas mélanger les
  illustrations).
"""
class Philomena :
    """
    @param site_ID ID du site utilisant Philomena. Actuellement disponibles :
                   - 1 pour https://derpibooru.org/
                   - 2 pour https://furbooru.org/
    """
    def __init__  ( self, site_ID = 1 ) :
        self.site_ID = site_ID
        
        if site_ID == 1 :
            self.base_URL = "https://derpibooru.org/"
        elif site_ID == 2 :
            self.base_URL = "https://furbooru.org/"
        
        # On utilise ces attributs pour mettre en cache le résultat de l'appel
        # à l'API pour une illustration.
        # On met en cache car la demande de l'URL de l'image et la demande des
        # URLs des comptes Twitter sont souvent ensembles.
        self.cache_illust_url = None
        self.cache_illust_url_json = None
    
    """
    Permet d'extraire l'ID de l'URL d'une illustration postée sur un Booru
    utilisant Philomena.
    @param artwork_url L'URL à examiner.
    @return L'ID de l'illustration postée sur ce Booru.
            Ou None si ce n'est pas un post sur ce Booru.
    """
    def artwork_url_to_id ( self, artwork_url : str ) :
        if self.site_ID == 1 :
            result = re.match( derpibooru_post_id_regex, artwork_url )
        elif self.site_ID == 2 :
            result = re.match( furbooru_post_id_regex, artwork_url )
        
        if result != None :
            return result.group( 1 )
        return None
    
    """
    METHODE PRIVEE, NE PAS UTILISER !
    Mettre en cache le résultat de l'appel à l'API de l'illustration si ce
    n'est pas déjà fait.
    Permet de MàJ le cache, si l'URL mène bien vers une illustration.
    
    @param illust_id L'URL de l'illustration sur un Booru utilisant Philomena.
    @return True si l'URL donné est utilisable.
            False sinon.
    """
    def cache_or_get ( self, illust_url : int ) -> bool :
        if illust_url != self.cache_illust_url :
            # Pour être certain de l'URL, on sort l'ID, pour reconstruire juste
            # après la même URL.
            illust_id = self.artwork_url_to_id( illust_url )
            if illust_id == None :
                return False
            
            response = get_with_rate_limits( self.base_URL + "api/v1/json/images/" + illust_id )
            
            json = response.json()
            
            self.cache_illust_url = illust_url
            self.cache_illust_url_json = json
        
        return True
    
    """
    Obtenir l'URL de l'image source à partir de l'URL de l'illustration postée.
    
    @param illust_id L'URL de l'illustration postée sur un Booru utilisant
                     Philomena.
    @return L'URL de l'image.
            Ou None si il y a eu un problème, c'est à dire que l'ID donné n'est
            pas une illustration sur un Booru utilisant Philomena.
    """
    def get_image_url ( self, illust_url : int ) -> str :
        # On met en cache si ce n'est pas déjà fait
        if not self.cache_or_get( illust_url ) :
            return None
        
        # On retourne le résultat voulu
        return self.cache_illust_url_json["image"]["representations"]["large"] # Large ça suffit
    
    """
    Retourne les noms des comptes Twitter trouvés.
    
    @param illust_id L'URL de l'illustration postée sur un Booru utilisant
                     Philomena.
    @param multiplexer Méthode "link_mutiplexer()" de la classe "Link_Finder"
                       (OPTIONNEL).
    
    @return Une liste de comptes Twitter.
            Ou une liste vide si aucun URL de compte Twitter valide n'a été
            trouvé.
            Ou None si il y a eu un problème, c'est à dire que l'ID donné n'est
            pas une illustration sur un Booru utilisant Philomena.
    """
    def get_twitter_accounts ( self, illust_url : int,
                                     multiplexer = None ) -> List[str] :
        # On met en cache si ce n'est pas déjà fait
        if not self.cache_or_get( illust_url ) :
            return None
        
        # ATTENTION ! Il peut y avoir plusieurs artistes !
        artists_tags = []
        for tag in self.cache_illust_url_json["image"]["tags"] :
            if tag[0:7] == "artist:" :
                artists_tags.append( tag )
        
        if artists_tags == [] :
            return []
        
        twitter_accounts = []
        
        for tag in artists_tags :
            # SCAN PAGE DU TAG DE L'ARTISTE
            
            # Problème Philomena : Le JSON d'une page sur un tag ne donne pas tous
            # URL qu'ils ont trouvés. Donc on doit le faire sur une page HTML.
            scanner = Webpage_to_Twitter_Accounts(
                "https://derpibooru.org/search?q=" + tag,
                )
            
            # Se concentrer que sur la div contenant les données.
            scanner.soup = scanner.soup.find("div", {"class": "tag-info__more"})
            
            # Rechercher (Désactiver car le multiplexeur les cherche aussi)
            if multiplexer == None :
                twitter_accounts += scanner.scan()
            
            # Envoyer dans le multiplexer les autres URL qu'on peut trouver
            if multiplexer != None :
                for link in scanner.scan( validator_function = validate_url ) :
                    get_multiplex = multiplexer( link )
                    if get_multiplex != None :
                        twitter_accounts += get_multiplex
        
        return twitter_accounts
    
    """
    Comme les Boorus sont des sites de reposts, on peut trouver la source de
    l'illustration. Si c'est sur un site que l'on supporte, le Link Finder peut
    aller y faire un tour !
    
    @param illust_id L'URL de l'illustration postée sur Booru utilisant
                     Philomena.
    @return L'URL de la source.
            Ou une chaine vide si il n'y a pas de source.
            Ou None si il y a eu un problème, c'est à dire que l'ID donné n'est
            pas une illustration sur Danbooru.
    """
    def get_source ( self, illust_url : int ) -> str :
        # On met en cache si ce n'est pas déjà fait
        if not self.cache_or_get( illust_url ) :
            return None
        
        # On retourne le résultat voulu
        source = self.cache_illust_url_json["image"]["source_url"]
        if source == None :
            return ""
        else :
            return source
    
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
        return datetime.fromisoformat( self.cache_illust_url_json["image"]["created_at"] )


"""
Test du bon fonctionnement de cette classe
"""
if __name__ == '__main__' :
    derpibooru = Philomena()
    test_twitter = []
    test_twitter.append(
        derpibooru.get_twitter_accounts(
            "https://www.derpibooru.org/images/1731476" ) )
    
    if test_twitter == [['the_park_0111']] :
        print( "Tests Twitter OK !" )
    else :
        print( "Tests Twitter échoués !" )
        print( test_twitter )
