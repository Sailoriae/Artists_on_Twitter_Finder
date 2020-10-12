#!/usr/bin/python3
# coding: utf-8

import tweepy
import time

try :
    from class_Cursor_Iterator import Cursor_Iterator
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .class_Cursor_Iterator import Cursor_Iterator


"""
Couche d'abstraction à la librairie Tweepy.

Permet d'utiliser sur l'API publique de Twitter avec la librairie Tweepy.
Gère les limites de l'API Twitter et attend d'être débloqué en cas de bloquage.
"""
class TweepyAbstraction :
    def __init__ ( self,
                   api_key,
                   api_secret,
                   oauth_token,
                   oauth_token_secret ) :
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(oauth_token, oauth_token_secret)
        
        # Tweepy gère l'attente lors d'une rate limit !
        self.api = tweepy.API( auth, 
                               wait_on_rate_limit = True,
                               wait_on_rate_limit_notify  = True )
    
    """
    @param tweet_id L'ID du Tweet
    @return Un objet Status (= Tweet de la librairie Tweepy)
            None si il y a eu un problème
    """
    def get_tweet ( self, tweet_id ) :
        retry = True
        while retry :
            retry = False
            try :
                return self.api.get_status( tweet_id, tweet_mode = 'extended' )
            except tweepy.error.RateLimitError as error :
                print( "Limite atteinte en récupérant les informations du Tweet " + str(tweet_id) + "." )
                print( error.reason )
                print( "On va réessayer dans 60 secondes... ", end='' )
                time.sleep( 60 )
                print( "On réessaye !" )
                retry = True
            except tweepy.TweepError as error :
                print( "Erreur en récupérant les informations du Tweet " + str(tweet_id) + "." )
                print( error.reason )
                return None # Bien laisser le "return None" pour le check_parameters()
    
    """
    @param account_name Le nom d'utilisateur du compte dont on veut l'ID.
                        Attention : Le nom d'utilisateur est ce qu'il y a après
                        le @ ! Par exemple : Si on veut scanner @jack, il faut
                        entrer dans cette fonction la chaine "jack".
    @param invert_mode Inverser cette fonction, retourne le nom d'utilisateur
                       à partir de l'ID du compte.
    @return L'ID du compte
            Ou None s'il y a eu un problème, c'est à dire soit :
            - Le compte n'existe pas,
            - Le compte est désactivé,
            - Le compte est suspendu,
            - Ou le compte est privé
    """
    def get_account_id ( self, account_name : str, invert_mode = False ) -> int :
        retry = True
        while retry :
            retry = False
            try :
                if invert_mode :
                    json = self.api.get_user( user_id = account_name )
                    if json._json["protected"] == True :
                        if invert_mode :
                            print( "Erreur en récupérant le nom du compte " + str(account_name) + "." )
                        else :
                            print( "Erreur en récupérant l'ID du compte @" + str(account_name) + "." )
                        print( "Le compte est en privé / est protégé." )
                        return None
                    return json.screen_name
                else :
                    json = self.api.get_user( screen_name = account_name )
                    if json._json["protected"] == True :
                        if invert_mode :
                            print( "Erreur en récupérant le nom du compte " + str(account_name) + "." )
                        else :
                            print( "Erreur en récupérant l'ID du compte @" + str(account_name) + "." )
                        print( "Le compte est en privé / est protégé." )
                        return None
                    return json.id
            except tweepy.error.RateLimitError as error :
                if invert_mode :
                    print( "Limite atteinte en récupérant le nom du compte " + str(account_name) + "." )
                else :
                    print( "Limite atteinte en récupérant l'ID du compte @" + str(account_name) + "." )
                print( error.reason )
                print( "On va réessayer dans 60 secondes... ", end='' )
                time.sleep( 60 )
                print( "On réessaye !" )
                retry = True
            except tweepy.TweepError as error :
                if invert_mode :
                    print( "Erreur en récupérant le nom du compte " + str(account_name) + "." )
                else :
                    print( "Erreur en récupérant l'ID du compte @" + str(account_name) + "." )
                print( error.reason )
                if error.api_code == 50 : # User not found
                    return None
                raise error
    
    """
    Obtenir les Tweets d'un utilisateur.
    ATTENTION ! Contient tous les Tweets sauf les RT
    ATTENTION ! Est forcément limité à 3 200 Tweets maximum ! RT compris,
    même si l'API ne nous les envoie pas.
    
    @param account_id L'ID du compte Twitter (Ou son nom d'utilisateur)
    @param since_tweet_id L'ID du tweet depuis lequel scanner (OPTIONNEL)
    @return Un itérateur d'objets Status (= Tweet de la librairie Tweepy)
    """
    def get_account_tweets ( self, account_id : int, since_tweet_id : int = None ) :
        # Attention ! Ne pas supprimer les réponses, des illustrations peuvent
        # être dans des réponses ! Laisser le code tel qu'il est.
        if since_tweet_id == None :
            return Cursor_Iterator(
                tweepy.Cursor( self.api.user_timeline,
                               user_id = account_id,
                               tweet_mode = "extended",
                               include_rts = False,
                               trim_user = True # Supprimer les infos sur l'utilisateur, on en n'a pas besoin
                              ).items() )
        else :
            return Cursor_Iterator(
                tweepy.Cursor( self.api.user_timeline,
                               user_id = account_id,
                               since_id = since_tweet_id,
                               tweet_mode = "extended",
                               include_rts = False,
                               trim_user = True # Supprimer les infos sur l'utilisateur, on en n'a pas besoin
                              ).items() )
    
    """
    Regarder si un compte bloque le compte connecté à l'API.
    
    @param account_id L'ID du compte.
    @return True ou False.
    """
    # Note : On ne peut pas savoir via cette API si le compte est en privé.
    def blocks_me ( self, account_id : int ) :
        friendship = self.api.show_friendship( target_id = account_id )
        return friendship[0].blocked_by
