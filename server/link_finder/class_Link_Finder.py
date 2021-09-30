#!/usr/bin/python3
# coding: utf-8

import re

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

from link_finder.supported_websites.class_DeviantArt import DeviantArt
from link_finder.supported_websites.class_Pixiv import Pixiv
from link_finder.supported_websites.class_Danbooru import Danbooru
from link_finder.supported_websites.class_Philomena import Philomena
from link_finder.supported_websites.utils.filter_twitter_accounts_list import filter_twitter_accounts_list
from link_finder.supported_websites.utils.class_Webpage_to_Twitter_Accounts import Webpage_to_Twitter_Accounts
from link_finder.supported_websites.utils.validate_url import validate_url
from link_finder.supported_websites.utils.validate_deviantart_account_url import validate_deviantart_account_url
from link_finder.supported_websites.utils.validate_pixiv_account_url import validate_pixiv_account_url
from link_finder.supported_websites.utils.validate_twitter_account_url import validate_twitter_account_url
from link_finder.supported_websites.utils.validate_linktree_account_url import validate_linktree_account_url
from link_finder.supported_websites.utils.validate_patreon_account_url import validate_patreon_account_url
from link_finder.class_Link_Finder_Result import Link_Finder_Result
from link_finder.class_Link_Finder_Result import Not_an_URL
from link_finder.class_Link_Finder_Result import Unsupported_Website
import parameters as param


# ^ = Début de la chaine, $ = Fin de la chaine
deviantart_url = re.compile(
    r"^http(?:s)?:\/\/(?:([a-zA-Z0-9]+)\.)?deviantart\.com(?:\/|$)" )
pixiv_url = re.compile(
    r"^http(?:s)?:\/\/(?:www\.)?pixiv\.net(?:\/|$)" )
danbooru_url = re.compile(
    r"^http(?:s)?:\/\/danbooru\.donmai\.us(?:\/|$)" )
derpibooru_url = re.compile(
    r"^http(?:s)?:\/\/(?:www\.)?derpibooru\.org(?:\/|$)" )
furbooru_url = re.compile(
    r"^http(?:s)?:\/\/(?:www\.)?furbooru\.org(?:\/|$)" )

# Bien mettre (?:\/|$) au bout pour s'assurer qu'il y a un "/" ou qu'on est à
# la fin de la chaine. Permet d'éviter de passer des sous domaines. Par exemple
# deviantart.com.example.tld, ce qui pourrait être une faille de sécurité.


"""
Moteur de recherche des comptes Twitter d'un artiste, à partir d'une
illustration postée sur l'un des sites supportés.

Les objets utilisés par cette classe gardent en cache leur dernier appel à
leurs API.
Ainsi, afin d'optimiser l'utilisation de cette classe, il faut :
- Initialiser un objet qu'une seule fois pour un thread, et le réutiliser.
- Ne surtout pas partager l'objet entre plusieurs threads.

Note importante : Si la source d'une image est un Tweet, ne jamais être tenté
de prendre le compte qui l'a posté pour le compte Twitter de l'artiste !
"""
class Link_Finder :
    def __init__ ( self ) :
        self.deviantart = DeviantArt()
        self.pixiv = Pixiv()
        self.danbooru = Danbooru()
        self.derpibooru = Philomena( site_ID = 1 )
        self.furbooru = Philomena( site_ID = 2 )
        
        # Dictionnaire permettant au multiplexeur de ne pas reboucler
        self.multiplexer_dict = {}
    
    """
    @param illust_url L'URL d'une illustration postée sur l'un des sites
                      supportés.
    
    @return Un objet "Link_Finder_Result" contenant les attributs suivants :
            - image_urls : Liste des URLs de l'image.  Si il y en a une, c'est
              l'image redimensionnée. Si il y en a deux, la première est la
              résolution originale de l'image, la seconde est redimensionnée.
            - twitter_accounts : Une liste de comptes Twitter, ou une liste 
              vide si aucun URL de compte Twitter valide n'a été trouvé.
            - publish_date : L'objet datetime de la date de publication de
              l'image.
    
            Ou None si l'URL est invalide (Mais que le site est supporté),
            c'est à dire que l'URL donnée ne mène pas à une illustration.
            
            Afin d'optimiser, si aucune compte Twitter n'a été trouvé,
            "image_url" et "publish_date" sont à None.

    Attention : Cette méthode émet des exceptions Unsupported_Website si le
    site n'est pas supporté !
    """
    def get_data ( self, illust_url : str ) -> Link_Finder_Result :
        # Ce sont les clases qui analysent les URL et vont dire si elles
        # mènent bien vers des illustrations.
        # Ici, on vérifie juste le domaine.
        
        # Vider le dictionnaire du multiplexeur de liens
        self._multiplexer_dict.clear()
        
        # Remplacer les "&amp;" par des "&"
        illust_url = illust_url.replace( "&amp;", "&" )
        
        # Vérification que ce soit bien une URL
        if validate_url( illust_url ) == None :
            raise Not_an_URL
        
        # ====================================================================
        # DEVIANTART
        # ====================================================================
        elif re.match( deviantart_url, illust_url ) != None :
            twitter_accounts = self.deviantart.get_twitter_accounts( illust_url, 
                                                                     multiplexer = self._link_mutiplexer )
            if twitter_accounts != [] and twitter_accounts != None :
                image_urls = self.deviantart.get_image_urls( illust_url )
                publish_date = self.deviantart.get_datetime( illust_url )
        
        # ====================================================================
        # PIXIV
        # ====================================================================
        elif re.match( pixiv_url, illust_url ) != None :
            twitter_accounts = self.pixiv.get_twitter_accounts( illust_url,
                                                                multiplexer = self._link_mutiplexer )
            if twitter_accounts != [] and twitter_accounts != None :
                image_urls = self.pixiv.get_image_urls( illust_url )
                publish_date = self.pixiv.get_datetime( illust_url )
        
        # ====================================================================
        # DANBOORU
        # ====================================================================
        elif re.match( danbooru_url, illust_url ) != None :
            twitter_accounts = self.danbooru.get_twitter_accounts( illust_url,
                                                                   multiplexer = self._link_mutiplexer )
            if twitter_accounts != [] and twitter_accounts != None :
                image_urls = self.danbooru.get_image_urls( illust_url )
                publish_date = self.danbooru.get_datetime( illust_url )
        
        # ====================================================================
        # DERPIBOORU
        # ====================================================================
        elif re.match( derpibooru_url, illust_url ) != None :
            twitter_accounts = self.derpibooru.get_twitter_accounts( illust_url,
                                                                     multiplexer = self._link_mutiplexer )
            if twitter_accounts != [] and twitter_accounts != None :
                image_urls = self.derpibooru.get_image_urls( illust_url )
                publish_date = self.derpibooru.get_datetime( illust_url )
        
        # ====================================================================
        # FURBOORU
        # ====================================================================
        elif re.match( furbooru_url, illust_url ) != None :
            twitter_accounts = self.furbooru.get_twitter_accounts( illust_url,
                                                                   multiplexer = self._link_mutiplexer )
            if twitter_accounts != [] and twitter_accounts != None :
                image_urls = self.furbooru.get_image_urls( illust_url )
                publish_date = self.furbooru.get_datetime( illust_url )
        
        # ====================================================================
        # Site non supporté
        # ====================================================================
        else :
            raise Unsupported_Website
        
        # ====================================================================
        # Retourner
        # ====================================================================
        
        # Le site est supporté mais l'URL ne mène pas à une illustration
        if twitter_accounts == None :
            return None
        
        # Illustration trouvée, mais aucun compte Twitter trouvé
        if twitter_accounts == [] :
            image_urls = None
            publish_date = None
        
        # Le site est supporté et l'URL mène à une illustration
        # La liste des comptes Twitter trouvés peut alors être vide
        return Link_Finder_Result( image_urls,
                                   filter_twitter_accounts_list( twitter_accounts ),
                                   publish_date )
    
    
    """
    Multiplexeur de liens.
    Rechercher des comptes Twitter dans des formats de pages webs connus.
    Par exemple, un profil DeviantArt, un profil Pixiv, ou un profil Linktree.
    Si l'URL est reconnue comme celle d'un compte Twitter, le compt sera
    retourné.
    
    @param url URL de la page web à analyser.
    
    @return Liste de comptes Twitter.
            Ou None la n'est pas utilisable (Site non supporté, URL ne menant
            pas à une illustration ou un compte sur un des sites supportés).
    """
    def _link_mutiplexer ( self, url ) :
        # TWITTER
        twitter = validate_twitter_account_url( url ) # Ne retourne pas de liste
        if twitter != None :
            return [ twitter ] # La fonction "filter_twitter_accounts_list()" est appelée à la fin du Link Finder
        
        # PROFIL SUR DEVIANTART
        deviantart = validate_deviantart_account_url( url )
        if deviantart != None :
            if not self._already_visited( "deviantart", deviantart ) :
                return self.deviantart.get_twitter_accounts( "", force_deviantart_account_name = deviantart,
                                                             multiplexer = self._link_mutiplexer )
            return []
        
        # ILLUSTRATION SUR DEVIANTART
        # Permet aux boorus d'envoyer leur champs "source"
        if re.match( deviantart_url, url ) != None :
            if not self._already_visited( "deviantart", url ) :
                return self.deviantart.get_twitter_accounts( url, 
                                                             multiplexer = self._link_mutiplexer )
        
        # PROFIL SUR PIXIV
        pixiv = validate_pixiv_account_url( url )
        if pixiv != None :
            if not self._already_visited( "pixiv", pixiv ) :
                return self.pixiv.get_twitter_accounts( "", force_pixiv_account_id = pixiv,
                                                            multiplexer = self._link_mutiplexer )
            return []
        
        # ILLUSTRATION SUR PIXIV
        # Permet aux boorus d'envoyer leur champs "source"
        if re.match( pixiv_url, url ) != None :
            if not self._already_visited( "pixiv", url ) :
                return self.deviantart.get_twitter_accounts( url, 
                                                             multiplexer = self._link_mutiplexer )
        
        # LINKTREE
        linktree = validate_linktree_account_url( url )
        if linktree != None :
            if not self._already_visited( "linktree", linktree ) :
                scanner = Webpage_to_Twitter_Accounts( "https://linktr.ee/" + linktree )
                twitter_accounts = []
                for link in scanner.scan( validator_function = validate_url ) :
                    get_multiplex = self._link_mutiplexer( link )
                    if get_multiplex != None :
                        twitter_accounts += get_multiplex
                return twitter_accounts
            return []
        
        # PATREON
        patreon = validate_patreon_account_url( url )
        if patreon != None :
            if not self._already_visited( "patreon", patreon ) :
                scanner = Webpage_to_Twitter_Accounts( "https://www.patreon.com/" + patreon )
                scanner.soup = scanner.soup.find("div", {"id": "renderPageContentWrapper"})
                twitter_accounts = []
                for link in scanner.scan( validator_function = validate_url ) :
                    get_multiplex = self._link_mutiplexer( link )
                    if get_multiplex != None :
                        twitter_accounts += get_multiplex
                return twitter_accounts
            return []
        
        # PAGE NON SUPPORTEE
        return None
    
    """
    Utiliser le dictionnaire du multiplexeur de liens pour empêcher de visiter
    deux fois la même page.
    """
    def _already_visited ( self, website, page ) :
        if website in self.multiplexer_dict :
            if page in self.multiplexer_dict[website] :
                return True
            self.multiplexer_dict[website].append( page )
            return False
        self.multiplexer_dict[website] = [page]
        return False
