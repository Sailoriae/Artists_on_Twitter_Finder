#!/usr/bin/python3
# coding: utf-8

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param


"""
Fonction de vérification des paramètres.
@return True si on peut démarrer, False sinon.
"""
def check_parameters () :
    print( "Vérification de l'importation des librairies...")
    try :
        import numpy
        import urllib3
        import imutils
        import cv2
        import mysql.connector
    except ModuleNotFoundError :
        print( "Il manque une librairie !" )
        print( "Veuillez exécuter : pip install -r requirements.txt" )
    else :
        print( "Toutes les librairies nécessaires sont présentes !" )
    
    
    print( "Verification de la connexion à l'API publique Twitter..." )
    from tweet_finder.twitter import TweepyAbtraction
    
    twitter = TweepyAbtraction( param.API_KEY,
                                param.API_SECRET,
                                param.OAUTH_TOKEN,
                                param.OAUTH_TOKEN_SECRET )
    
    # On essaye d'avoir le premier Tweet sur Twitter
    # https://twitter.com/jack/status/20
    if twitter.get_tweet( 20 ) == None :
        print( "Echec de connexion à l'API publique Twitter !")
        print( "Veuillez vérifier votre fichier \"parameters.py\" !" )
        return False
    else :
        print( "Connexion à l'API publique Twitter réussie !")
    
    
    print( "Vérification de la connexion à l'API Pixiv..." )
    from link_finder.supported_websites import Pixiv
    
    try :
        Pixiv( param.PIXIV_USERNAME, param.PIXIV_PASSWORD )
    except Exception :
        print( "Echec de connexion à l'API Pixiv !")
        print( "Veuillez vérifier votre fichier \"parameters.py\" !" )
        return False
    else :
        print( "Connexion à l'API Pixiv réussie !")
    
    
    if param.USE_MYSQL_INSTEAD_OF_SQLITE :
        print( "Vérification de la connexion à la BDD MySQL..." )
        try :
            mysql.connector.connect(
                    host = param.MYSQL_ADDRESS,
                    port = param.MYSQL_PORT,
                    user = param.MYSQL_USERNAME,
                    password = param.MYSQL_PASSWORD,
                    database = param.MYSQL_DATABASE_NAME
                )
        except Exception :
            print( "Impossible de se connecter à la base de donées MySQL !" )
            print( "Veuillez vérifier votre fichier \"parameters.py\" !" )
            return False
        else :
            print( "Connexion à la BDD MySQL réussie !" )
    
    print( "Tous les tests ont réussi ! Démarrage du serveur..." )
    
    return True
