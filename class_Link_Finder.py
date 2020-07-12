#!/usr/bin/python3
# coding: utf-8

import re

from link_finder import DeviantArt
from link_finder import Pixiv
from link_finder import Danbooru

from link_finder.utils import filter_twitter_accounts_list
import parameters as param


#twitter_url = re.compile(
#    "http(?:s)?:\/\/(?:www\.)?twitter\.com" )

# ^ = Début de la chaine
deviantart_url = re.compile(
    "^http(?:s)?:\/\/(?:([a-zA-Z0-9]+)\.)?deviantart\.com" )
pixiv_url = re.compile(
    "^http(?:s)?:\/\/(?:www\.)?pixiv\.net" )
danbooru_url = re.compile(
    "^http(?:s)?:\/\/danbooru\.donmai\.us" )


"""
Moteur de recherche des comptes Twitter d'un artiste, à partir d'une
illustration postée sur l'un des sites supportés.

Les objets utilisés par cette classe gardent en cache leur dernier appel à
leurs API.
Ainsi, afin d'optimiser l'utilisation de cette classe, il faut :
- Initialiser un objet qu'une seule fois pour un thread, et le réutiliser.
- Ne surtout pas partager l'objet entre plusieurs threads.
- Et exécuter les deux méthodes get_image_url() et get_twitter_accounts() l'une
  après l'autre pour une même illustration (C'est à dire ne pas mélanger les
  illustrations).
"""
class Link_Finder :
    def __init__ ( self ) :
        self.deviantart = DeviantArt()
        self.pixiv = Pixiv( param.PIXIV_USERNAME, param.PIXIV_PASSWORD )
        self.danbooru = Danbooru()
    
    """
    @param illust_url L'URL d'une illustration postée sur l'un des sites
                      supportés.
    @return L'URL de l'image.
            None si l'URL est invalide (Mais que le site est supporté), c'est à
            dire que l'URL donnée ne mène pas à une illustration.
            False si le site n'est pas supporté.
    """
    def get_image_url ( self, illust_url : str ) -> str :
        # Ce sont les clases qui analysent les URL et vont dire si elles
        # mènent bien vers des illustrations.
        # Ici, on vérifie juste le domaine.
        if re.search( deviantart_url, illust_url ) != None :
            return self.deviantart.get_image_url( illust_url )
        
        elif re.search( pixiv_url, illust_url ) != None :
            return self.pixiv.get_image_url( illust_url )
        
        elif re.search( danbooru_url, illust_url ) != None :
            return self.danbooru.get_image_url( illust_url )
        
        else :
            return False # Oui c'est une bidouille
    
    """
    @param illust_url L'URL d'une illustration postée sur l'un des sites
                      supportés.
    @return Une liste de comptes Twitter.
            Ou une liste vide si aucun URL de compte Twitter valide n'a été
            trouvé.
            None si l'URL est invalide (Mais que le site est supporté), c'est à
            dire que l'URL donnée ne mène pas à une illustration.
            False si le site n'est pas supporté.
    """
    def get_twitter_accounts ( self, illust_url : str ) -> str :
        # Ce sont les clases qui analysent les URL et vont dire si elles
        # mènent bien vers des illustrations.
        # Ici, on vérifie juste le domaine.
        if re.search( deviantart_url, illust_url ) != None :
            return self.deviantart.get_twitter_accounts( illust_url )
        
        elif re.search( pixiv_url, illust_url ) != None :
            return self.pixiv.get_twitter_accounts( illust_url )
        
        elif re.search( danbooru_url, illust_url ) != None :
            # Pour beaucoup d'artistes sur Danbooru, on peut trouver leur
            # compte Pixiv, et donc s'assurer de touver leurs comptes Twitter.
            pixiv_accounts = self.danbooru.get_pixiv_accounts( illust_url )
            twitter_accounts = []
            if pixiv_accounts != None :
                for pixiv_account in pixiv_accounts :
                    accounts = self.pixiv.get_twitter_accounts(
                        None,
                        force_pixiv_account_id = pixiv_account )
                    if accounts != None :
                        twitter_accounts += accounts
            
            return filter_twitter_accounts_list(
                twitter_accounts + self.danbooru.get_twitter_accounts( illust_url ) )
        
        else :
            return False # Oui c'est une bidouille


"""
Test du bon fonctionnement de cette classe
"""
if __name__ == '__main__' :
    import link_finder_tester
