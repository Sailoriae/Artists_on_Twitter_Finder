#!/usr/bin/python3
# coding: utf-8

import tweepy
import time


"""
Couche d'abstraction à la librairie Tweepy.

Permet d'utiliser sur l'API publique de Twitter avec la librairie Tweepy.
Gère les limites de l'API Twitter et attend d'être débloqué en cas de bloquage.
"""
class TweepyAbtraction :
    def __init__ ( self,
                   api_key,
                   api_secret,
                   oauth_token,
                   oauth_token_secret ) :
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(oauth_token, oauth_token_secret)
        self.api = tweepy.API(auth)
    
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
                return None
    
    """
    @param account_name Le nom d'utilisateur du compte dont on veut l'ID.
                        Attention : Le nom d'utilisateur est ce qu'il y a après
                        le @ ! Par exemple : Si on veut scanner @jack, il faut
                        entrer dans cette fonction la chaine "jack".
    @param invert_mode Inverser cette fonction, retourne le nom d'utilisateur
                       à partir de l'ID du compte.
    @return L'ID du compte
            Ou None si le compte est introuvable
    """
    def get_account_id ( self, account_name : str, invert_mode = False ) -> int :
        retry = True
        while retry :
            retry = False
            try :
                if invert_mode :
                    return self.api.get_user( account_name ).screen_name
                else :
                    return self.api.get_user( account_name ).id
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
                    print( "Erreur en récupérant le nom du compte" + str(account_name) + "." )
                else :
                    print( "Erreur en récupérant l'ID du compte @" + str(account_name) + "." )
                print( error.reason )
                return None
    
    """
    Obtenir les Tweets d'un utilisateur.
    ATTENTION ! Contient tous les Tweets sauf les RT
    ATTENTION ! Est forcément limité à 3 200 Tweets maximum ! RT compris,
    même si l'API ne nous les envoie pas.
    
    @param account_id L'ID du compte Twitter (Ou son nom d'utilisateur)
    @param since_tweet_id L'ID du tweet depuis lequel scanner (OPTIONNEL)
    @return Un liste d'objets Status (= Tweet de la librairie Tweepy)
    """
    def get_account_tweets ( self, account_id : int, since_tweet_id : int = None ) :
        # tweepy.Cursor gère les Rate Limits
        # Attention ! Ne pas supprimer les réponses, des illustrations peuvent
        # être dans des réponses ! Laisser le code tel qu'il est.
        if since_tweet_id == None :
            return tweepy.Cursor( self.api.user_timeline,
                                  id = account_id,
                                  tweet_mode = "extended",
                                  include_rts = False,
                                  trim_user = True # Supprimer les infos sur l'utilisateur, on en n'a pas besoin
                                 ).items()
        else :
            return tweepy.Cursor( self.api.user_timeline,
                                  id = account_id,
                                  since_id = since_tweet_id,
                                  tweet_mode = "extended",
                                  include_rts = False,
                                  trim_user = True # Supprimer les infos sur l'utilisateur, on en n'a pas besoin
                                 ).items()
