#!/usr/bin/python3
# coding: utf-8

"""
Ce script permet de vérifier si les API utilisées par les threads de listages
sont limitées par adresse IP ou par compte connecté. La méthode de test est
simple : On envoie pleins de requêtes avec un compte pour atteindre la
rate-limit, puis on fait une requête sur la même API avec un autre compte pour
voir s'il est lui aussi limité. Si oui, la rate-limit est par adresse IP, si
non, la rate-limit est par compte.

Réponse du 09 juillet 2022 : L'API de timeline (Via Tweepy) est limitée par
compte connecté, et impossible d'avoir un résultat pour l'API de recherche
(Via SNScrape), on atteint jamais la rate-limit (850k Tweets obtenus en 15
minutes (Ce qui est la période par défaut des rate-limits chez Twitter)).
"""

import sys
import tweepy
from threading import Thread
from time import time
import snscrape.modules.twitter

# On travaille dans le répertoire racine du serveur AOTF
# On bouge dedans, et on l'ajoute au PATH
from os.path import abspath as get_abspath
from os.path import dirname as get_dirname
from os import chdir as change_wdir
from os import getcwd as get_wdir
from sys import path
change_wdir(get_dirname(get_abspath(__file__)))
change_wdir( "../server" )
path.append(get_wdir())

import parameters as param
from tweet_finder.twitter.class_SNScrapeAbstraction import TwitterSearchScraper
from threads.network_crash import is_network_crash


"""
Avertir l'utilisateur sur ce que fait ce script.
"""
print( "Ce script permet de vérifier si l'API de timeline (Via la librairie \
Tweepy) et celle de recherche (Via la librairie SNScrape) utilisées par le \
serveur AOTF pour ses listages de Tweets (Repectivement les threads B et A) \
sont limitées par compte connecté ou par adresse IP (Avant d'atteindre une \
erreur HTTP 429)." )
print( "Votre fichier \"parameters.py\" doit être fonctionnel, sinon ce \
script va forcément planter. Le compte par défaut et deux comptes \
d'indexation doivent être correctement configurés. Vous pouvez démarrer le \
serveur AOTF pour vérifier ceci." )
while True :
    answer = input( "Voulez-vous continuer ? [y/n] " )
    if answer == "y" :
        break
    elif answer == "n" :
        sys.exit(0)


"""
Vérification rapide des paramètres.
"""
if len( param.TWITTER_API_KEYS ) < 2 :
    print( "Vous devez avoir au moins deux comptes d'indexation !" )
    sys.exit(0)

# On est obligé de vérifier que les clés d'accès à l'API de recherche
# fonctionnent bien, car on ne pourra pas différencier un crash sur une
# erreur HTTP 429 d'un crash parce que la clé n'est pas valable
for i in [ 0, 1 ] :
    scraper = TwitterSearchScraper( "from:@jack", retries = 1 )
    scraper.set_auth_token( param.TWITTER_API_KEYS[i]["AUTH_TOKEN"] )
    try :
        for tweet in scraper.get_items() : break
    except Exception :
        print( f"La clé d'accès au compte numéro {i+1} n'est pas valide !" )
        sys.exit(0)


"""
Procédure pour atteindre la rate-limit. Permet d'éviter une duplication de code
entre notre test avec Tweepy et notre test avec SNScrape.
Afin d'atteindre plus rapidement la rate-limit, on crée plusieurs threads.
@param thread_procedure Procédure à exécuter dans les threads. Cela permet de
                        paralléliser les requêtes, et donc d'atteindre plus
                        rapidement la rate-limit.
@param number_of_threads Nombre de threads à créer.
"""
# Variables passées en globales
results = []
count_tweets = 0
start = time()

def reach_rate_limit( thread_procedure, number_of_threads = 10 ) :
    global results, count_tweets, start
    
    # Indiquer si le tread a fini par atteindre l'erreur 429
    results = [ False ] * number_of_threads
    
    # Compter les Tweets obtenus
    count_tweets = 0
    
    # Ne pas dépasser la période de la rate-limit (15 minutes)
    start = time()
    
    # Démarrer les threads
    threads = []
    for thread_id in range( number_of_threads ) :
        threads.append(
            Thread( target = thread_procedure,
                    args = ( thread_id, ) ) )
        threads[-1].start()
    
    # Attendre la fin des threads
    for thread_id in range( number_of_threads ):
        threads[thread_id].join()
    
    # Afficher le nombre final de Tweets obtenus
    print( f"{count_tweets} Tweets obtenus." )
    
    # Si on a dépassé la période de la rate-limit (15 minutes)
    if time() - start > 900 :
        print( "La période de la rate-limit a été dépassée, il est donc \
impossible d'aller au bout de ce test." )
        sys.exit(0)
    
    # Vérifier que tous les threads soient arrivés à l'erreur 429
    for thread_id in range( number_of_threads ):
        if not results[thread_id] :
            print( "Un thread n'est pas arrivé à l'erreur HTTP 429 !" )
            sys.exit(0)


"""
Tester l'API de timeline via Tweepy (Utilisée par les threads B).
"""
print( "Test de l'API de timeline (Via la librairie Tweepy)..." )

# Procédure des threads de tests, pour atteindre plus vite le rate-limit
# Indiquera dans results[thread_id] s'il a bien atteint l'erreur HTTP 429
def thread_procedure ( thread_id ) :
    global results, count_tweets, start
    
    # Se connecter avec le compte par défaut
    # On le fait dans le thread, comme le ferait le serveur AOTF
    # De toutes manières, si on le fait hors, ça crash
    auth = tweepy.OAuthHandler( param.API_KEY, param.API_SECRET )
    auth.set_access_token( param.OAUTH_TOKEN, param.OAUTH_TOKEN_SECRET )
    api = tweepy.API( auth, wait_on_rate_limit = False )
    
    try :
        while True :
            for tweet in tweepy.Cursor( api.user_timeline,
                                        screen_name = "jack",
                                        trim_user = True ).items() :
                count_tweets += 1
                if count_tweets % 1000 == 0 :
                    print( f"{count_tweets} Tweets obtenus..." )
                # Au bout de 15 minutes (Période des rate-limits),
                # on considère que c'est mort
                if time() - start > 900 : return
    except tweepy.errors.TooManyRequests :
        results[thread_id] = True
    except Exception :
        print( "Une erreur s'est produite pour atteindre la rate-limit ! \
Est-ce que le compte par défaut est correctement configuré ?" )

# Atteindre la rate-limit avec le compte par défaut
reach_rate_limit( thread_procedure )
print( "La rate-limit de l'API de timeline a été atteinte !" )

# Se connecter avec un autre compte (Le compte numéro 1)
auth = tweepy.OAuthHandler( param.API_KEY, param.API_SECRET )
auth.set_access_token( param.TWITTER_API_KEYS[0]["OAUTH_TOKEN"],
                       param.TWITTER_API_KEYS[0]["OAUTH_TOKEN_SECRET"] )
api = tweepy.API( auth, wait_on_rate_limit = False )

# Tester avec cet autre compte (Le test est plus rapide, si on est limité par
# adresse IP, on recevrait une erreur HTTP 429 tout de suite).
try :
    for tweet in tweepy.Cursor( api.user_timeline,
                                screen_name = "jack",
                                trim_user = True ).items( 10 ) :
        break
except tweepy.errors.TooManyRequests :
    print( "Tweepy est limité par adresse IP !" )
except Exception :
    print( "Une erreur s'est produite lors du test ! Est-ce que le compte \
d'indexation numéro 1 est correctement configuré ?" )
    sys.exit(0)
else :
    print( "Tweepy est limité par compte connecté !" )


"""
Tester l'API de recherche via SNScrape (Utilisée par les threads A).
"""
print( "Test de l'API de recherche (Via la librairie SNScrape)..." )
print( "Attention, cela risque d'être très long voir impossible à conclure !" )

# Procédure des threads de tests, pour atteindre plus vite la rate-limit
# Indiquera dans results[thread_id] s'il a bien atteint l'erreur HTTP 429
def thread_procedure ( thread_id ) :
    global results, count_tweets, start
    
    # Se connecter avec le compte numéro 1
    # On le fait dans le thread, comme le ferait le serveur AOTF
    scraper = TwitterSearchScraper( "from:@jack", retries = 1 )
    scraper.set_auth_token( param.TWITTER_API_KEYS[0]["AUTH_TOKEN"] )
    
    try :
        while True :
            for tweet in scraper.get_items() :
                count_tweets += 1
                if count_tweets % 1000 == 0 :
                    print( f"{count_tweets} Tweets obtenus..." )
                # Au bout de 15 minutes (Période des rate-limits),
                # on considère que c'est mort
                if time() - start > 900 : return
    # On ne peut pas différencier une 429 d'un autre problème, d'où la
    # vérification au début de ce script
    except Exception as error :
        if is_network_crash( error ) : # On sort au moins les pbs réseau
            print( "L'accès au réseau a été rompu lors du test !" )
            return
        results[thread_id] = True

# Atteindre la rate-limit avec le compte numéro 1
reach_rate_limit( thread_procedure, number_of_threads = 20 )
print( "La rate-limit de l'API de recherche a été atteinte !" )

# Se connecter avec un autre compte (Le compte numéro 2)
scraper = TwitterSearchScraper( "from:@jack", retries = 1 )
scraper.set_auth_token( param.TWITTER_API_KEYS[1]["AUTH_TOKEN"] )

# Tester avec cet autre compte (Le test est plus rapide, si on est limité par
# adresse IP, on recevrait une erreur HTTP 429 tout de suite).
try :
    for tweet in scraper.get_items() : break
except Exception as error :
    if is_network_crash( error ) :
        print( "L'accès au réseau a été rompu lors du test !" )
        sys.exit(0)
    print( "SNScrape est limité par adresse IP !" )
else :
    print( "SNScrape est limité par compte connecté !" )

# Tester aussi si en non-connecté on est rate-limité
# Ne pas utiliser notre version modifiée, car elle n'est pas faite pour qu'on
# ne lui donne pas un token d'authentification ("auth_token")
scraper = snscrape.modules.twitter.TwitterSearchScraper( "from:@jack", retries = 1 )
try :
    for tweet in scraper.get_items() : break
except Exception as error :
    if is_network_crash( error ) :
        print( "L'accès au réseau a été rompu lors du test !" )
        sys.exit(0)
    print( "La recherche sans être connecté est elle aussi rate-limitée !" )
else :
    print( "La recherche sans être connecté n'est pas rate-limitée !" )
