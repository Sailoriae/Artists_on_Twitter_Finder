#!/usr/bin/python3
# coding: utf-8

import tweepy
import time

# Vérifier que Tweepy est à une version supérieure à la 4.0.0
if int( tweepy.__version__.split(".")[0] ) < 4 :
    raise ModuleNotFoundError( "La version de la librairie Tweepy doit être supérieure à la 4.0.0 !" )

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendamment (Notamment pour des
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

from tweet_finder.twitter.class_Cursor_Iterator import Cursor_Iterator


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
        self._api = tweepy.API( auth, 
                                wait_on_rate_limit = True # Gérer les rate limits
                               )
        # Note : Ne pas utiliser l'option "retry_count"
        # Elle réessaye sur TOUTES les erreurs, pas seulement celles de connexion
        # Note : Tweepy met des timeouts de 60 secondes par défaut
    
    """
    Cette fonction est uniquement à utiliser dans "check_parameters()".
    
    @param tweet_id L'ID du Tweet
    @return Un objet Status (= Tweet de la librairie Tweepy)
            None si il y a eu un problème
    """
    def get_tweet ( self, tweet_id, trim_user = False ) :
        try :
            return self._api.get_status( tweet_id, trim_user = trim_user, tweet_mode = 'extended' )
        except tweepy.errors.HTTPException as error :
            print( f"[Tweepy] Erreur en récupérant les informations du Tweet ID {tweet_id}." )
            print( error )
            return None # Bien laisser le "return None" pour le check_parameters()
    
    """
    @param tweet_id Liste d'ID de Tweets
    @return Liste d'objet Status (= Tweet de la librairie Tweepy)
            None si il y a eu un problème
    """
    def get_multiple_tweets ( self, tweets_ids, trim_user = False ) :
        to_return = []
        
        # Séparer la liste "accounts_names" en sous-listes de 100 éléments
        for tweets_ids_sublist in [tweets_ids[i:i+100] for i in range(0,len(tweets_ids),100)] :
            to_return += self._api.lookup_statuses( tweets_ids_sublist, trim_user = trim_user, tweet_mode = "extended" )
        
        return to_return
    
    """
    @param account_name Le nom d'utilisateur du compte dont on veut l'ID.
                        Attention : Le nom d'utilisateur est ce qu'il y a après
                        le @ ! Par exemple : Si on veut scanner @jack, il faut
                        entrer dans cette fonction la chaine "jack".
    @param invert_mode Inverser cette fonction, retourne le nom d'utilisateur
                       à partir de l'ID du compte.
    @param retry_once Réessayer une fois sur une erreur de connexion.
    
    @return L'ID du compte
            Ou None s'il y a eu un problème, c'est à dire soit :
            - Le compte n'existe pas,
            - Le compte est désactivé,
            - Le compte est suspendu,
            - Ou le compte est privé
    """
    def get_account_id ( self, account_name : str, invert_mode = False, retry_once = True ) -> int :
        try :
            if invert_mode :
                json = self._api.get_user( user_id = account_name )
                if json._json["protected"] == True :
#                    print( f"[Tweepy] Erreur en récupérant le nom du compte ID {account_name}." )
#                    print( "[Tweepy] Le compte est en privé / est protégé." )
                    return None
                return json.screen_name
            else :
                json = self._api.get_user( screen_name = account_name )
                if json._json["protected"] == True :
#                    print( f"[Tweepy] Erreur en récupérant l'ID du compte @{account_name}." )
#                    print( "[Tweepy] Le compte est en privé / est protégé." )
                    return None
                return json.id
        except tweepy.errors.HTTPException as error :
#            if invert_mode :
#                print( f"[Tweepy] Erreur en récupérant le nom du compte ID {account_name}." )
#            else :
#                print( f"[Tweepy] Erreur en récupérant l'ID du compte @{account_name}." )
#            print( error )
            if 50 in error.api_codes : # User not found
                return None
            if 63 in error.api_codes : # User has been suspended
                return None
            if retry_once and error.api_codes == [] :
                time.sleep( 10 )
                return self.get_account_id( account_name, invert_mode = invert_mode, retry_once = False )
            raise error
    
    """
    @param account_name Liste de comptes Twitter dont on veut l'ID.
    @param retry_once Réessayer une fois sur une erreur de connexion.
    
    @return Liste de tuples contenant le nom du compte, et son ID.
            Un compte peut ne pas être présent dans la liste si :
            - Le compte n'existe pas,
            - Le compte est désactivé,
            - Le compte est suspendu,
            - Ou le compte est privé
    """
    def get_multiple_accounts_ids ( self, accounts_names, retry_once = True ) :
        to_return = []
        
        # Séparer la liste "accounts_names" en sous-listes de 100 éléments
        for accounts_names_sublist in [accounts_names[i:i+100] for i in range(0,len(accounts_names),100)] :
            try :
                for account in self._api.lookup_users( screen_name = accounts_names_sublist ) :
                    # Filtrer les comptes privés
                    if account._json["protected"] == False :
                        to_return.append( ( account.screen_name, account.id ) )
            
            # Gérer le cas où aucun compte dans la liste n'est trouvable
            except tweepy.errors.HTTPException as error :
                if 17 in error.api_codes : # No user matches for specified terms
                    continue
                if retry_once and error.api_codes == [] :
                    time.sleep( 10 )
                    return self.get_multiple_accounts_ids( accounts_names, retry_once = False )
                raise error
        
        return to_return

    
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
                tweepy.Cursor( self._api.user_timeline,
                               user_id = account_id,
                               tweet_mode = "extended",
                               include_rts = False,
                               count = 200, # 200 Tweets par page, c'est le maximum, donc 16 requêtes pour 3200 Tweets
                                            # Source : https://developer.twitter.com/en/docs/twitter-api/v1/tweets/timelines/api-reference/get-statuses-user_timeline
                               trim_user = True # Supprimer les infos sur l'utilisateur, on en n'a pas besoin
                              ).items() )
        else :
            return Cursor_Iterator(
                tweepy.Cursor( self._api.user_timeline,
                               user_id = account_id,
                               since_id = since_tweet_id,
                               tweet_mode = "extended",
                               include_rts = False,
                               count = 200, # 200 Tweets par page, c'est le maximum, donc 16 requêtes pour 3200 Tweets
                                            # Source : https://developer.twitter.com/en/docs/twitter-api/v1/tweets/timelines/api-reference/get-statuses-user_timeline
                               trim_user = True # Supprimer les infos sur l'utilisateur, on en n'a pas besoin
                              ).items() )
    
    """
    Regarder si un compte bloque le compte connecté à l'API.
    
    @param account_id L'ID du compte.
    @param append_twitter_account Permet de retourner en même temps le nom du
                                  compte Twitter. Ceci est une bidouille pour
                                  le listage avec l'API de recherche, afin de
                                  vérifier que l'ID corresponde au nom.
    @param retry_once Réessayer une fois sur une erreur de connexion.
    @return True ou False.
            Ou None s'il y a eu un problème, c'est à dire soit :
            - Le compte n'existe pas,
            - Le compte est désactivé,
            - Ou le compte est suspendu
            Ne détecte pas si le compte est privé.
    """
    # Note : On ne peut pas savoir via cette API si le compte est en privé.
    def blocks_me ( self, account_id : int, append_account_name = False, retry_once = True ) :
        try :
            friendship = self._api.get_friendship( target_id = account_id )
            if append_account_name :
                return friendship[0].blocked_by, friendship[1].screen_name
            else :
                return friendship[0].blocked_by
        except tweepy.errors.HTTPException as error :
            if 50 in error.api_codes : # User not found
                return None
            if 63 in error.api_codes : # User has been suspended
                return None
            if retry_once and error.api_codes == [] :
                time.sleep( 10 )
                return self.blocks_me( account_id, retry_once = False )
            raise error
