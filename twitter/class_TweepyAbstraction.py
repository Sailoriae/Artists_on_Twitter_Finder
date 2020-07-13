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
    @return Un objet Tweet (Librairie Tweepy)
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
    @return L'ID du compte
            Ou None si le compte est introuvable
    """
    def get_account_id ( self, account_name : str ) -> int :
        retry = True
        while retry :
            retry = False
            try :
                return self.api.get_user( account_name ).id
            except tweepy.error.RateLimitError as error :
                print( "Limite atteinte en récupérant l'ID du compte @" + str(account_name) + "." )
                print( error.reason )
                print( "On va réessayer dans 60 secondes... ", end='' )
                time.sleep( 60 )
                print( "On réessaye !" )
                retry = True
            except tweepy.TweepError as error :
                print( "Erreur en récupérant l'ID du compte @" + str(account_name) + "." )
                print( error.reason )
                return None
