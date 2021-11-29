#!/usr/bin/python3
# coding: utf-8

from typing import List
import re
from dateutil import parser
from urllib.parse import quote

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

from link_finder.supported_websites.utils.class_Webpage_to_Twitter_Accounts import Webpage_to_Twitter_Accounts
from link_finder.supported_websites.utils.get_with_rate_limits import get_with_rate_limits
from link_finder.supported_websites.utils.validate_url import validate_url


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
- Et exécuter les deux méthodes get_image_urls() et get_twitter_accounts() l'une
  après l'autre pour une même illustration (C'est à dire ne pas mélanger les
  illustrations).
"""
class Danbooru :
    def __init__  ( self ) :
        # On utilise ces attributs pour mettre en cache le résultat de l'appel
        # à l'API pour une illustration.
        # On met en cache car la demande de l'URL de l'image et la demande des
        # URLs des comptes Twitter sont souvent ensembles.
        self._cache_illust_url = None
        self._cache_illust_url_json = None
    
    """
    Permet d'extraire l'ID de l'URL d'une illustration postée sur Danbooru.
    @param artwork_url L'URL à examiner.
    @return L'ID de l'illustration postée sur Danbooru.
            Ou None si ce n'est pas un post sur Danbooru.
    """
    def _artwork_url_to_id ( self, artwork_url : str ) :
        result = re.match( danbooru_post_id_regex, artwork_url )
        if result != None :
            return result.group( 1 )
        return None
    
    """
    Mettre en cache le résultat de l'appel à l'API de l'illustration si ce
    n'est pas déjà fait.
    Permet de MàJ le cache, si l'URL mène bien vers une illustration.
    param illust_id L'URL de l'illustration Danbooru.
    
    @return True si l'URL donné est utilisable.
            False sinon.
    """
    def _cache_or_get ( self, illust_url : int ) -> bool :
        if illust_url != self._cache_illust_url :
            # Pour être certain de l'URL, on sort l'ID, pour reconstruire juste
            # après la même URL, avec juste ".json" au bout.
            illust_id = self._artwork_url_to_id( illust_url )
            if illust_id == None :
                return False
            
            response = get_with_rate_limits( "https://danbooru.donmai.us/posts/" + illust_id + ".json" )
            
            json = response.json()
            
            # Si il y a une clé "success" à False, c'est que ce n'est pas bon
            try :
                if json["success"] == False :
                    print( f"[Danbooru] Erreur : {json['message']}" )
                    return False
            except KeyError :
                pass
            
            self._cache_illust_url = illust_url
            self._cache_illust_url_json = json
        
        return True
    
    """
    Obtenir l'URL de l'image source à partir de l'URL de l'illustration postée.
    
    @param illust_id L'URL de l'illustration postée sur Danbooru.
    @return Liste contenant deux URL de l'image (La première est la résolution
            originale de l'image, la seconde est redimensionnée).
            Ou None si il y a eu un problème, c'est à dire que l'ID donné n'est
            pas une illustration sur Danbooru.
    """
    def get_image_urls ( self, illust_url : int ) -> List[str] :
        # On met en cache si ce n'est pas déjà fait
        if not self._cache_or_get( illust_url ) :
            return None
        
        # On retourne le résultat voulu
        return [ self._cache_illust_url_json["file_url"],
                 self._cache_illust_url_json["large_file_url"] ]
    
    """
    Retourne les noms des comptes Twitter trouvés.
    Cette fonction ne peut pas être appelée depuis le multiplexeur de liens !
    
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
        if not self._cache_or_get( illust_url ) :
            return None
        
        # Il peut y avoir plusieurs artistes
        # Dans ce cas, on cherche les comptes Twitter de tous les artistes
        artists_tags = self._cache_illust_url_json["tag_string_artist"].split(" ")
        
#        if artists_tags == [""] :
#            return []
        # Ne pas retourner tout de suite, il faut aller voir la source
        # Faire en sorte qu'il n'y ait aucune itération dans la boucle "for"
        if artists_tags == [""] :
            artists_tags = []
        
        twitter_accounts = []
        
        # SCAN PAGE DU TAG DE L'ARTISTE
        
        for artist_tag in artists_tags :
            # Problème Danbooru : Le JSON d'une page sur un tag ne donne pas les
            # URL qu'ils ont trouvés. Donc on doit le faire sur une page HTML.
            scanner = Webpage_to_Twitter_Accounts(
                "https://danbooru.donmai.us/artists/show_or_new?name=" + quote( artist_tag ),
                )
            
            # Se concentrer que sur la div contenant les données.
            scanner.soup = scanner.soup.find("div", {"id": "c-artists"})
            
            # Rechercher (Désactiver car le multiplexeur les cherche aussi)
            if multiplexer == None :
                twitter_accounts += scanner.scan()
            
            # Envoyer dans le multiplexer les autres URL qu'on peut trouver
            if multiplexer != None :
                for link in scanner.scan( validator_function = validate_url ) :
                    get_multiplex = multiplexer( link )
                    if get_multiplex != None :
                        twitter_accounts += get_multiplex
        
        # Comme les Boorus sont des sites de reposts, on peut trouver la source
        # de l'illustration. Si c'est sur un site que l'on supporte, le
        # multiplexeur de liens peut aller y faire un tour !
        if multiplexer != None :
            source = self._get_source( illust_url )
            if source != None and source != "" :
                get_multiplex = multiplexer( source, source = "booru_source" )
                if get_multiplex != None :
                    twitter_accounts += get_multiplex
        
        return twitter_accounts
    
    """
    Comme les Boorus sont des sites de reposts, on peut trouver la source de
    l'illustration. Si c'est sur un site que l'on supporte, le multiplexeur de
    liens peut y aller y faire un tour !
    
    @param illust_id L'URL de l'illustration postée sur Booru utilisant
                     Danbooru.
    @return L'URL de la source.
            Ou une chaine vide si il n'y a pas de source.
            Ou None si il y a eu un problème, c'est à dire que l'ID donné n'est
            pas une illustration sur Danbooru.
    """
    def _get_source ( self, illust_url : int ) -> str :
        # On met en cache si ce n'est pas déjà fait
        if not self._cache_or_get( illust_url ) :
            return None
        
        # Exception pour Pixiv (Je ne sais pas pourquoi l'API Danbooru fait ça)
        if ( "pixiv_id" in self._cache_illust_url_json and
             self._cache_illust_url_json["pixiv_id"] != None and
             self._cache_illust_url_json["pixiv_id"] != "" ) :
            source = "https://www.pixiv.net/en/artworks/" + str( self._cache_illust_url_json["pixiv_id"] )
        else :
            source = self._cache_illust_url_json["source"]
        
        # On retourne le résultat voulu
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
        if not self._cache_or_get( illust_url ) :
            return None
        
        # On retourne le résultat voulu
        return parser.isoparse( self._cache_illust_url_json["created_at"] )


"""
Test du bon fonctionnement de cette classe
"""
if __name__ == '__main__' :
    danbooru = Danbooru()
    test_twitter = []
    test_twitter.append(
        danbooru.get_twitter_accounts(
            "https://danbooru.donmai.us/posts/3994568" ) )
    
    if test_twitter == [['brillewind']] :
        print( "Tests Twitter OK !" )
    else :
        print( "Tests Twitter échoués !" )
