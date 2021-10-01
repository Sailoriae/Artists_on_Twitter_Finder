#!/usr/bin/python3
# coding: utf-8

import re
import inspect

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


# Profondeur maximale de recherche dans le multiplexeur de liens.
MAX_DEPTH = 2
# Le multiplexeur peut retourner un compte Twitter même si la profondeur est
# dépassée.
# Exemple : Illustration DeviantArt -> Multiplexeur -> Compte DeviantArt ->
# Mutliplexeur -> Page Patreon -> Multiplexeur -> Compte Twitter
# 
# Le mutliplexeur autorise une profondeur de plus si on part d'une source sur
# un site de republications (Un booru par exemple).
# Exemple : Illustration Derpibooru -> Multiplexeur -> Illustration DeviantArt
# -> Multiplexeur -> Compte DeviantArt -> Multiplexeur -> Page Linktree ->
# Multiplexeur -> Compte Twitter



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
    def __init__ ( self, DEBUG = False ) :
        self._DEBUG = DEBUG
        
        self._deviantart = DeviantArt()
        self._pixiv = Pixiv()
        self._danbooru = Danbooru()
        self._derpibooru = Philomena( site_ID = 1 )
        self._furbooru = Philomena( site_ID = 2 )
        
        # Dictionnaire permettant au multiplexeur de ne pas reboucler
        self._multiplexer_dict = {}
        
        # Profondeur maximal de recherche
        self.current_max_depth = MAX_DEPTH
    
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
        
        # Réintialiser la profondeur maximale de recherche, même le
        # multiplexeur est censé le faire
        self.current_max_depth = MAX_DEPTH
        
        # Remplacer les "&amp;" par des "&"
        illust_url = illust_url.replace( "&amp;", "&" )
        
        # Vérification que ce soit bien une URL
        if validate_url( illust_url ) == None :
            raise Not_an_URL
        
        # ====================================================================
        # DEVIANTART
        # ====================================================================
        elif re.match( deviantart_url, illust_url ) != None :
            twitter_accounts = self._deviantart.get_twitter_accounts( illust_url, 
                                                                      multiplexer = self._link_mutiplexer )
            if twitter_accounts != [] and twitter_accounts != None :
                image_urls = self._deviantart.get_image_urls( illust_url )
                publish_date = self._deviantart.get_datetime( illust_url )
        
        # ====================================================================
        # PIXIV
        # ====================================================================
        elif re.match( pixiv_url, illust_url ) != None :
            twitter_accounts = self._pixiv.get_twitter_accounts( illust_url,
                                                                 multiplexer = self._link_mutiplexer )
            if twitter_accounts != [] and twitter_accounts != None :
                image_urls = self._pixiv.get_image_urls( illust_url )
                publish_date = self._pixiv.get_datetime( illust_url )
        
        # ====================================================================
        # DANBOORU
        # ====================================================================
        elif re.match( danbooru_url, illust_url ) != None :
            twitter_accounts = self._danbooru.get_twitter_accounts( illust_url,
                                                                    multiplexer = self._link_mutiplexer )
            if twitter_accounts != [] and twitter_accounts != None :
                image_urls = self._danbooru.get_image_urls( illust_url )
                publish_date = self._danbooru.get_datetime( illust_url )
        
        # ====================================================================
        # DERPIBOORU
        # ====================================================================
        elif re.match( derpibooru_url, illust_url ) != None :
            twitter_accounts = self._derpibooru.get_twitter_accounts( illust_url,
                                                                      multiplexer = self._link_mutiplexer )
            if twitter_accounts != [] and twitter_accounts != None :
                image_urls = self._derpibooru.get_image_urls( illust_url )
                publish_date = self._derpibooru.get_datetime( illust_url )
        
        # ====================================================================
        # FURBOORU
        # ====================================================================
        elif re.match( furbooru_url, illust_url ) != None :
            twitter_accounts = self._furbooru.get_twitter_accounts( illust_url,
                                                                    multiplexer = self._link_mutiplexer )
            if twitter_accounts != [] and twitter_accounts != None :
                image_urls = self._furbooru.get_image_urls( illust_url )
                publish_date = self._furbooru.get_datetime( illust_url )
        
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
    @param from_booru_source Activer la reconnaissance d'URL d'une illustration
                             comme le ferait la méthode "get_data()". Réservé
                             au champs "source" des site de republications, par
                             exemple les boorus.
                             Autorise une profondeur de recherche de plus si ce
                             lien mène à une illustration sur un site supporté
                             qui n'est pas un site de republications.
    
    @return Liste de comptes Twitter.
            Ou None si la page n'est pas utilisable (Site non supporté, URL ne
            menant pas à une illustration ou un compte sur un des sites
            supportés). None peut aussi être renvoyé si on a atteint la
            profondeur maximale de recherche
    """
    def _link_mutiplexer ( self, url, from_booru_source = False ) :
        if self._DEBUG :
            print( f"[Link_Finder] Multiplexeur : {url}" )
        
        # TWITTER
        twitter = validate_twitter_account_url( url ) # Ne retourne pas de liste
        if twitter != None :
            return [ twitter ] # La fonction "filter_twitter_accounts_list()" est appelée à la fin du Link Finder
        
        
        # Déterminer le nombre de fois dans la pile d'appels qu'on a été appelé
        stack = inspect.stack()
        me = stack[0][3]
        call_count = 0
        for call in stack :
            if call[3] == me :
                call_count += 1
        if call_count > self.current_max_depth :
            return None
        
        # ====================================================================
        # DEVIANTART
        # ====================================================================
        
        # PROFIL SUR DEVIANTART
        deviantart = validate_deviantart_account_url( url )
        if deviantart != None :
            if not self._already_visited( "deviantart", deviantart ) :
                return self._deviantart.get_twitter_accounts( "", force_deviantart_account_name = deviantart,
                                                              multiplexer = self._link_mutiplexer )
            return []
        
        # ILLUSTRATION SUR DEVIANTART
        # Permet aux boorus d'envoyer leur champs "source"
        if from_booru_source and re.match( deviantart_url, url ) != None :
            if not self._already_visited( "deviantart", url ) :
                self.current_max_depth += 1 # Autoriser une profondeur de plus
                to_return = self._deviantart.get_twitter_accounts( url,
                                                                   multiplexer = self._link_mutiplexer )
                self.current_max_depth -= 1
                return to_return
        
        
        # ====================================================================
        # PIXIV
        # ====================================================================
        
        # PROFIL SUR PIXIV
        pixiv = validate_pixiv_account_url( url )
        if pixiv != None :
            if not self._already_visited( "pixiv", pixiv ) :
                return self._pixiv.get_twitter_accounts( "", force_pixiv_account_id = pixiv,
                                                         multiplexer = self._link_mutiplexer )
            return []
        
        # ILLUSTRATION SUR PIXIV
        # Permet aux boorus d'envoyer leur champs "source"
        if from_booru_source and re.match( pixiv_url, url ) != None :
            if not self._already_visited( "pixiv", url ) :
                self.current_max_depth += 1 # Autoriser une profondeur de plus
                to_return = self._deviantart.get_twitter_accounts( url,
                                                                   multiplexer = self._link_mutiplexer )
                self.current_max_depth -= 1
                return to_return
        
        
        # ====================================================================
        # SITES NON-SUPPORTES
        # Ils ne peuvent pas être des sites sources, mais on y cherche quand
        # même des comptes Twitter.
        # ====================================================================
        
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
    
    @param website Clé dans le dictionnaire (Nom du site).
    @param page Valeur dans la liste associée à la clé.
    """
    def _already_visited ( self, website : str, page : str ) :
        if website in self._multiplexer_dict :
            if page in self._multiplexer_dict[website] :
                return True
            self._multiplexer_dict[website].append( page )
            return False
        self._multiplexer_dict[website] = [page]
        return False
