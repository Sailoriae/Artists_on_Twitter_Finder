#!/usr/bin/python3
# coding: utf-8

from cv2 import error as ErrorOpenCV
from typing import List
import traceback

try :
    from lib_GetOldTweets3 import manager as GetOldTweets3_manager
    from cbir_engine import CBIR_Engine
    from database import SQLite_or_MySQL
    from twitter import TweepyAbtraction
    from utils import url_to_cv2_image
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .lib_GetOldTweets3 import manager as GetOldTweets3_manager
    from .cbir_engine import CBIR_Engine
    from .database import SQLite_or_MySQL
    from .twitter import TweepyAbtraction
    from .utils import url_to_cv2_image

# Ajouter le répertoire parent au PATH pour pouvoir importer les paramètres
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))
import parameters as param

# On peut télécharger les images des tweets donnés par GetOldTweets3 en
# meilleure qualité. Cependant, cela n'améliore pas de beaucoup la précision du
# calcul de la distance entre les images indexées et l'image de requête.
# En effet, il y a 4 niveaux de qualité sur Twitter : "thumb", "small",
# "medium" et "large". Et par défaut, si rien n'est indiqué, le serveur nous
# envoit la qualité "medium". Donc il n'y a pas une grande différence
# Laisser désactiver, car on ne sait pas s'il y a une qualité "large" pour
# toutes les images !
# De plus, laisser désactiver nous fait gagner un peu de connexion internet !
# Ca se sent bien sur les gros comptes !
#from utils import add_argument_to_url


"""
Moteur de recherche d'image par le contenu ("content-based image retrieval",
CBIR) qui indexe des tweets et les stocke dans sa base de données.

Les tweets doivent contenir au moins une image, sinon, ils seront rejetés.
Chaque image est stocké dans la base de données, associée à l'ID de son tweet,
l'ID de l'auteur du tweet, et la liste des caractéristiques extraites par le
moteur CBIR.

Méthode disponibles :
- index_tweet() : Indexer un Tweet unique (A éviter).
- index_or_update_all_account_tweets() : Indexer tous les Tweets d'un compte.
- get_GOT3_list() : Faire l'étape de listage des Tweets de la méthode
                    ci-dessus. Passer son résultat à la méthode ci-dessus.
                    Permet de paralléliser les deux étapes longues de
                    l'indexation d'un compte Twitter.
- search_tweet() : Rechercher un Tweet dans la base de donnée qui contient une
                   image de requête.

- index_or_update_with_TwitterAPI() : Idem que index_or_update_all_account_tweets(), mais
                                      avec l'API publique de Twitter via la librairie
                                      Tweepy.
"""
class CBIR_Engine_with_Database :
    """
    Constructeur.
    Initialise le moteur CBIR, la couche d'abstraction à la base de données, et
    la couche d'abstraction à la librairie pour l'API Twitter.
    """
    def __init__( self, DEBUG : bool = False ) :
        self.DEBUG = DEBUG
        self.cbir_engine = CBIR_Engine()
        self.bdd = SQLite_or_MySQL()
        self.twitter = TweepyAbtraction( param.API_KEY,
                                         param.API_SECRET,
                                         param.OAUTH_TOKEN,
                                         param.OAUTH_TOKEN_SECRET )
    
    """
    Indexer les images d'un tweet dans la base de données.
    Chaque image est associée à l'ID de son tweet, l'ID de l'auteur du tweet
    et la liste des caractéristiques extraites par le moteur CBIR.
    
    @param tweet_id L'ID du tweet à indexer
    @param tweepy_Status_object L'objet Status de la librairie Tweepy, écrase
                                le paramètre tweet_id (OPTIONNEL)
    @return True si l'indexation a réussi
            False sinon
    """
    def index_tweet( self, tweet_id : int, tweepy_Status_object = None ) -> bool :
        if tweepy_Status_object == None :
            tweet = self.twitter.get_tweet( tweet_id )
            
            if tweet == None :
                if self.DEBUG :
                    print( "Impossible d'indexer le Tweet " + str( tweet_id ) + "." )
                return False
        else :
            tweet = tweepy_Status_object
            tweet_id = tweet.id
        
        if self.DEBUG :
            print( "Scan tweet " + str( tweet_id ) + "." )
        
        # Tester avant d'indexer si le tweet n'est pas déjà dans la BDD
        if self.bdd.is_tweet_indexed( tweet_id ) :
            if self.DEBUG :
                print( "Tweet déjà indexé !" )
            return True
        
        # Liste des URLs des images dans ce tweet
        tweet_images_url : List[str] = []
        
        try :
            for tweet_media in tweet._json["extended_entities"]["media"] :
                if tweet_media["type"] == "photo" :
                    tweet_images_url.append( tweet_media["media_url_https"] )
        except KeyError as error :
            if self.DEBUG :
                print( "Ce tweet n'a pas de médias." )
                print( error )
            return False
        
        if len( tweet_images_url ) == 0 :
            if self.DEBUG :
                print( "Ce tweet n'a pas de médias." )
            return False
        
        if self.DEBUG :
            print( "Images trouvées dans le tweet " + str( tweet_id ) + " :" )
            print( str( tweet_images_url ) )
        
        image_1 = None
        image_2 = None
        image_3 = None
        image_4 = None
        
        length = len( tweet_images_url )
        
        if length == 0 :
            if self.DEBUG :
                print( "Tweet sans image, on le passe !" )
            return False
        
        # Traitement des images du Tweet
        try :
            if length > 0 :
                image_1 = self.cbir_engine.index_cbir(
                              url_to_cv2_image( tweet_images_url[0] ) )
            if length > 1 :
                image_2 = self.cbir_engine.index_cbir(
                              url_to_cv2_image( tweet_images_url[1] ) )
            if length > 2 :
                image_3 = self.cbir_engine.index_cbir(
                              url_to_cv2_image( tweet_images_url[2] ) )
            if length > 3 :
                image_4 = self.cbir_engine.index_cbir(
                              url_to_cv2_image( tweet_images_url[3] ) )
        
        # Oui, c'est possible, Twitter n'est pas parfait
        # Exemple : https://twitter.com/apofissx/status/219051550696407040
        # Ce tweet est indiqué comme ayant une image, mais elle est en 404 !
        except Exception as error :
            print( "Erreur avec le Tweet : " + str(tweet_id) + " !" )
            print( error )
            file = open( "class_CBIR_Engine_with_Database_errors.log", "a" )
            file.write( "Erreur avec le Tweet : " + str(tweet_id) + " !\n" )
            traceback.print_exc( file = file )
            file.write( "\n\n\n" )
            file.close()
            return False
        
        # Prendre les hashtags
        try :
            hashtags = []
            for hashtag in tweet._json["entities"]["hashtags"] :
                # On ajoute le "#" car GOT3 le laisse, et l'API Twitter l'enlève
                # Donc on fait comme GOT3
                hashtags.append( "#" + hashtag["text"] )
        except KeyError as error :
            if self.DEBUG :
                print( "Erreur en récupérant les hashtags." )
                print( error )
            hashtags = None
        
        # Stockage des résultats
        self.bdd.insert_tweet(
            tweet._json["user"]["id"],
            tweet_id,
            image_1,
            image_2,
            image_3,
            image_4,
            hashtags
        )
        
        return True
    
    """
    Obtenir la liste des Tweets trouvés par GetOldTweets3.
    
    @param account_name Le nom d'utilisateur du compte à scanner
    @return La liste des tweets du compte à partir de la date du dernier scan.
            Associée à l'ID du compte Twitter.
            False si le nom du compte est introuvable, ou est suspendu, ou est
            désactivé, ou est privé.
    """
    def get_GOT3_list( self, account_name : str ) :
        # Prendre la date du dernier Tweet
        account_id = self.twitter.get_account_id( account_name )
        if account_id == None :
            print( "Compte @" + account_name + " introuvable !" )
            return False
        
        print( "Listage des Tweets de @" + account_name + "." )
        
        since_date = self.bdd.get_account_last_scan( account_id )
        
        # Note importante : GOT3 ne peut pas voir les Tweets marqués comme
        # sensibles... Mais il peut voir les tweets non-sensibles de comptes
        # sensibles en désactivant le filtre "safe" et en étant connecté
        # à une session !
        # Cependant, désactiver le filtre "safe" masque les tweets de comptes
        # non-sensibles, il faut donc faire avec et sans !
        
        # On fait d'abord avec le filtre "safe"
        tweetCriteria = GetOldTweets3_manager.TweetCriteria()\
            .setQuerySearch( "from:" + account_name + " filter:media -filter:retweets (filter:safe OR -filter:safe)" )
        if since_date != None :
            tweetCriteria.setSince( since_date )
        
        to_return = GetOldTweets3_manager.TweetManager.getTweets( tweetCriteria,
                                                                  auth_token=param.TWITTER_AUTH_TOKEN )
        
        # Second scan en désactivant complètement le filtre "safe"
        # Ce n'est pas grave si on scan deux fois, mais il vaut mieux le faire
        # Twitter sont beaucoup trop flou pour qu'on puisse faire des "if"
        tweetCriteria = GetOldTweets3_manager.TweetCriteria()\
            .setQuerySearch( "from:" + account_name + " filter:media -filter:retweets -filter:safe" )
        if since_date != None :
            tweetCriteria.setSince( since_date )
            
        to_return += GetOldTweets3_manager.TweetManager.getTweets( tweetCriteria,
                                                                   auth_token=param.TWITTER_AUTH_TOKEN )
        
        # Note : Le filtre "safe" filtre aussi les "gros-mots", par exemple :
        # "putain".
        # Ainsi, "(filter:safe OR -filter:safe)" permet de voir ces tweets,
        # mais pas les tweets de comptes marqués sensibles.
        # C'est pour cela qu'il y a le "if" avec une deuxième passe.
        #
        # Exemple de compte marqué sensible : "@rikatantan2nd"
        # (Compte pris au hasard pour tester, désolé)
        
        # Note 2 : J'y comprend plus rien, j'ai réussi à scanner les tweets de
        # "@Lewdlestia", qui est pourtant un compte marqué comme sensible, et
        # qui tweet que des médias sensibles (Complètement NSFW, ne pas aller
        # voir).
        # GOT3 en retourne 12 000 sur les 16 000 actuels. Normal que tous ne
        # soient pas indexés car c'est un bot qui Tweet toutes les heures.
        
        # Le problème c'est que Twitter sont très flous sur le sujet des
        # comptes et des tweets marqués sensibles...
        
        # Bref, ce système fonctionne.
        
        return ( to_return, account_id )
    
    """
    Scanner tous les tweets d'un compte (Les retweets ne comptent pas).
    Seuls les tweets avec des médias seront scannés.
    Et parmis eux, seuls les tweets avec 1 à 4 images seront indexés.
    Cette méthode n'utilise pas l'API publique de Twitter, mais la librairie
    GetOldTweets3, qui utilise l'API de https://twitter.com/search.
    
    Cette méthode ne recanne pas les tweets déjà scannés.
    En effet, elle commence sont analyse à la date du dernier scan.
    Si le compte n'a pas déjà été scanné, tous ses tweets le seront.
    
    C'est la méthode get_GOT3_list() qui vérifie si le nom de compte Twitter
    entré ici est valide !
    
    @param account_name Le nom d'utilisateur du compte à scanner
                        Attention : Le nom d'utilisateur est ce qu'il y a après
                        le @ ! Par exemple : Si on veut scanner @jack, il faut
                        entrer dans cette fonction la chaine "jack".
    @param get_GOT3_list_result Liste des tweets retournés par la méthode
                                get_GOT3_list() ci-dessus, associée à l'ID du
                                compte Twitter.
                                Permet de paralléliser cette opération sur un
                                autre thread.
                                (OPTIONNEL)
    @return True si tout s'est bien passé
            False si le compte est introuvable, ou est suspendu, ou est
            désactivé, ou est privé
    """
    
    def index_or_update_all_account_tweets( self, account_name : str,
                                            get_GOT3_list_result = None ) -> bool :
        if get_GOT3_list_result == None :
            get_GOT3_list_result = self.get_GOT3_list( account_name )
        if get_GOT3_list_result == False : # Si le nom du compte est introuvable
            return False
        
        tweets_to_scan, account_id = get_GOT3_list_result
        
        print( "Indexation / scan des Tweets de @" + account_name + " avec GetOldTweets3." )
        
        length = len( tweets_to_scan )
        
        # Si la liste est vide, c'est qu'il n'y a aucun Tweet à indexer
        if length == 0 :
            # On force la MàJ de la date local de scan pour que le thread de
            # MàJ automatique ne repasse pas de si tôt dessus
            self.bdd.set_account_last_scan(
                account_id,
                self.bdd.get_account_last_scan( account_id ) )
            return True
        
        # Stocker la date du premier tweet que l'on va scanner, c'est à dire le
        # plus récent
        scan_date = tweets_to_scan[0].date.strftime('%Y-%m-%d')
        
        print( str(length) + " Tweets à indexer." )
        
        for i in range( length ) :
            if self.DEBUG :
                print( "Indexation tweet %s (%d/%d)." % ( tweets_to_scan[i].id, i+1, length) )
            
            # Tester avant d'indexer si le tweet n'est pas déjà dans la BDD
            if self.bdd.is_tweet_indexed( tweets_to_scan[i].id ) :
                if self.DEBUG :
                    print( "Tweet déjà indexé !" )
                continue
            
            image_1 = None
            image_2 = None
            image_3 = None
            image_4 = None
            
            tweets_to_scan_length = len( tweets_to_scan[i].images )
            
            if tweets_to_scan_length == 0 :
                if self.DEBUG :
                    print( "Tweet sans image, on le passe !" )
                continue
            
            # Traitement des images du Tweet
            try :
                if tweets_to_scan_length > 0 :
                    image_1 = self.cbir_engine.index_cbir(
                              url_to_cv2_image(
    #                              add_argument_to_url( tweets_to_scan[i].images[0], "name=large" ) ) )
                                  tweets_to_scan[i].images[0] ) )
                if tweets_to_scan_length > 1 :
                    image_2 = self.cbir_engine.index_cbir(
                              url_to_cv2_image(
    #                              add_argument_to_url( tweets_to_scan[i].images[1], "name=large" ) ) )
                                  tweets_to_scan[i].images[0] ) )
                if tweets_to_scan_length > 2 :
                    image_3 = self.cbir_engine.index_cbir(
                              url_to_cv2_image(
    #                              add_argument_to_url( tweets_to_scan[i].images[2], "name=large" ) ) )
                                  tweets_to_scan[i].images[0] ) )
                if tweets_to_scan_length > 3 :
                    image_4 = self.cbir_engine.index_cbir(
                              url_to_cv2_image(
    #                              add_argument_to_url( tweets_to_scan[i].images[3], "name=large" ) ) )
                                  tweets_to_scan[i].images[0] ) )
            
            # Oui, c'est possible, Twitter n'est pas parfait
            # Exemple : https://twitter.com/apofissx/status/219051550696407040
            # Ce tweet est indiqué comme ayant une image, mais elle est en 404 !
            #
            # Permet aussi de gérer les images avec des formats à la noix
            except Exception as error :
                print( "Erreur avec le Tweet : " + str(tweets_to_scan[i].id) + " !" )
                print( error )
                file = open( "class_CBIR_Engine_with_Database_errors.log", "a" )
                file.write( "Erreur avec le Tweet : " + str(tweets_to_scan[i].id) + " !\n" )
                traceback.print_exc( file = file )
                file.write( "\n\n\n" )
                file.close()
                continue
            
            # Prendre les hashtags du Tweet
            # Fonctionne avec n'importe quel Tweet, même ceux entre 160 et 280
            # caractères (GOT3 les voit en entier)
            hashtags = tweets_to_scan[i].hashtags.split(" ")
            
            # Stockage des résultats
            self.bdd.insert_tweet(
                tweets_to_scan[i].author_id,
                tweets_to_scan[i].id,
                image_1,
                image_2,
                image_3,
                image_4,
                hashtags
            )
        
        # On met à jour la date du dernier scan dans la base de données
        if scan_date != None :
            self.bdd.set_account_last_scan( account_id, scan_date )
        
        # On force la MàJ de la date local de scan pour que le thread de
        # MàJ automatique ne repasse pas de si tôt dessus
        else :
            self.bdd.set_account_last_scan(
                account_id,
                self.bdd.get_account_last_scan( account_id ) )
        
        return True
    
    """
    Rechercher un tweet dans la base de donnée grâce à une image
    @param image_url L'URL de l'image à chercher
    @param account_name Le nom du compte Twitter dans lequel chercher, c'est à
                        dire ce qu'il y a après le @ (OPTIONNEL)
    @return Liste d'objets Image_in_DB, contenant les attributs suivants :
            - account_id : L'ID du compte Twitter
            - tweet_id : L'ID du Tweet contenant l'image
            - distance : La distance calculée avec l'image de requête
            - image_position : La position de l'image dans le Tweet (1-4)
            None si il y a eu un problème
    """
    def search_tweet( self, image_url : str, account_name : str = None ) :
        if account_name != None :
            account_id = self.twitter.get_account_id( account_name )
        else :
            account_id = 0
        
        try :
            image = url_to_cv2_image( image_url )
        except Exception :
            print( "L'URL \"" + str(image_url) + "\" ne mène pas à une image !" )
            return None
        
        try :
            to_return = self.cbir_engine.search_cbir(
                image,
                self.bdd.get_images_in_db_iterator( account_id )
            )
        # Si j'amais l'image passée a un format à la noix et fait planter notre
        # moteur CBIR
        except ErrorOpenCV :
            print( ErrorOpenCV )
            return None
        
        # Suppression des attributs "image_features" pour gagner un peu de
        # mémoire
        for image in to_return :
            image.image_features = []
        
        # Retourner
        return to_return
    
    """
    Scanner tous les tweets d'un compte (Les retweets ne comptent pas).
    Seuls les tweets avec des médias seront scannés.
    Et parmis eux, seuls les tweets avec 1 à 4 images seront indexés.
    Cette méthode utilise l'API publique de Twitter, et est donc limitée au
    3200 premiers tweets (RT compris) d'un compte.
    
    Cette méthode ne recanne pas les tweets déjà scannés.
    En effet, elle commence sont analyse à la date du dernier scan.
    Si le compte n'a pas déjà été scanné, tous ses tweets le seront.
    
    @param account_name Le nom d'utilisateur du compte à scanner
                        Attention : Le nom d'utilisateur est ce qu'il y a après
                        le @ ! Par exemple : Si on veut scanner @jack, il faut
                        entrer dans cette fonction la chaine "jack".
    @return True si tout s'est bien passé
            False si le compte est introuvable, ou est suspendu, ou est
            désactivé, ou est privé
    """
    def index_or_update_with_TwitterAPI( self, account_name : str ) -> bool :
        account_id = self.twitter.get_account_id( account_name )
        if account_id == None :
            print( "Compte @" + account_name + " introuvable !" )
            return False
        
        print( "Indexation / scan des Tweets de @" + account_name + " avec l'API Twitter." )
        
        since_tweet_id = self.bdd.get_account_last_scan_with_TwitterAPI( account_id )
        
        last_tweet_id = None
        
        for tweet in self.twitter.get_account_tweets( account_id, since_tweet_id ) :
            if self.DEBUG :
                print( "Indexation tweet %s." % ( tweet.id ) )
            
            # Le premier tweet est forcément le plus récent
            if last_tweet_id == None :
                last_tweet_id = tweet.id
            
            # Cela ne sert à rien ester avant d'indexer si le tweet n'est pas
            # déjà dans la BDD car la fonction index_tweet() le fait
            
            try :
                tweet.retweeted_status
            except AttributeError : # Le Tweet n'est pas un RT
                pass
            else : # Le Tweet est un RT
                continue
            
            self.index_tweet( 0, tweepy_Status_object = tweet )
        
        # On met à jour la date du dernier scan dans la base de données
        if last_tweet_id != None :
            self.bdd.set_account_last_scan_with_TwitterAPI( account_id, last_tweet_id )
        
        # On force la MàJ de la date local de scan pour que le thread de
        # MàJ automatique ne repasse pas de si tôt dessus
        else :
            self.bdd.set_account_last_scan_with_TwitterAPI(
                account_id,
                self.bdd.get_account_last_scan_with_TwitterAPI( account_id ) )
        
        return True


"""
Test du bon fonctionnement de cette classe

Note : Comment voir un tweet sur l'UI web avec son ID :
    https://twitter.com/any/status/1160998394887716864
"""
if __name__ == '__main__' :
    engine = CBIR_Engine_with_Database( DEBUG = True )
    index = engine.index_tweet( 1277396497789640704 )
    index = engine.index_tweet( 1160998394887716864 )
    index = engine.index_tweet( 1272649003570565120 )
    if index : print( "Test d'indexation OK." )
    else : print( "Erreur durant le test d'indexation !" )
    
    # Attention : Test vachement long, car il y a actuellement environ 2000
    # tweets sur ce compte, et que presque tous ont des médias
    engine.index_or_update_all_account_tweets( "MingjueChen" )
    
    founded_tweets = engine.search_tweet(
        "https://pbs.twimg.com/media/EByx4lXUcAEzrly.jpg"
    )
    print( "Tweets contenant une image recherchée :")
    print( founded_tweets )
    if 1160998394887716864 in [ data.tweet_id for data in founded_tweets ] :
        print( "Test de recherche OK." )
    else :
        print( "Problème durant le test de recherche !" )
