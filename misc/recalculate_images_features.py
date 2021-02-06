#!/usr/bin/python3
# coding: utf-8


import sys
print( "Ne pas exécuter ce script sans savoir ce qu'il fait." )
sys.exit(0)


"""
Ce script permet de recalculer la liste des caractéristiques CBIR pour toutes
les images dans la base de données.
Attention : Il crée de nouvelles tables d'images, et garde les anciennes
intactes.

LE SERVEUR DOIT ETRE ETEINT !

NOTE IMPORTANTE : Ne pas utiliser ce script !
Il vaut mieux créer une nouvelle BDD propre, copier-coller la colonne
"accounts.account_id", et laisser le thread de MàJ auto faire son travail. Cela
permet beaucoup plus de souplesse !
Puis, comme l'indexation de Tweets sur le moteur de recherche de Twitter est
très changeante, ajouter avec un script les Tweets manquants de l'ancienne BDD,
qui les indexe comme le fait le script "extract_tweets_ids_from_error_file.py".
"""


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

from tweet_finder import CBIR_Engine_for_Tweets_Images
from tweet_finder.database import SQLite_or_MySQL
from tweet_finder.database.sql_requests_dict import sql_requests_dict

# Toujours la même erreur :
# [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1123)
# Ce fix est dangereux car désactive la vérication des certificats
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# Protection pour le multiprocessing
if __name__ == "__main__" :
    # Multiprocessing, sinon c'est trop long
    import multiprocessing
    
    from time import time
    
    
    """
    Connexion à la BDD et renommage des tables d'images.
    """
    bdd = SQLite_or_MySQL()
    
#    c = bdd.get_cursor()
#    c.execute( "RENAME TABLE tweets_images_1 TO tweets_images_1_old" )
#    c.execute( "RENAME TABLE tweets_images_2 TO tweets_images_2_old" )
#    c.execute( "RENAME TABLE tweets_images_3 TO tweets_images_3_old" )
#    c.execute( "RENAME TABLE tweets_images_4 TO tweets_images_4_old" )
#    bdd.conn.commit()
    
    # Il faut donc redémarrer la connexion pour qu'elle recrée les tables
    bdd.__init__()
    
    
    """
    Recalculer la liste des caractéristiques pour toutes les images.
    """
    def recalculate ( image_id, tweet_id, image_name ) :
        image_url = "https://pbs.twimg.com/media/" + image_name
        engine = CBIR_Engine_for_Tweets_Images()
        features = engine.get_image_features( image_url, tweet_id )
        if features != None :
            bdd = SQLite_or_MySQL()
            c = bdd.get_cursor()
            c.execute( sql_requests_dict["insert_tweet_image_" + image_id],
                       tuple( [tweet_id, image_name] + [ float(v) for v in features ] ) )
            bdd.conn.commit()
    
    threads = []
    start = time()
    
    for image_id in ["4", "3", "2", "1"] :
        c = bdd.get_cursor()
        table_name = "tweets_images_" + image_id
        c.execute( """SELECT tweet_id, image_name
                      FROM """ + table_name + """_old
                      WHERE NOT EXISTS (
                          SELECT *
                          FROM """ + table_name + """
                          WHERE """ + table_name + """.tweet_id = """ + table_name + """_old.tweet_id
                      )""" )
        images = c.fetchall()
        
        count_str = str(len(images))
        for i in range(len(images)) :
            tweet_id = images[i][0]
            image_name = images[i][1]
            print( table_name + " " + str(i+1) + "/" + count_str + " : " + image_name + " (Tweet ID " + str(tweet_id) + ")" )
            threads.append(
                multiprocessing.Process( name = image_name,
                                         target = recalculate,
                                         args = ( image_id, tweet_id, image_name, ) ) )
            threads[-1].start()
            
            # Attendre tous les 48 threads
            if len(threads) >= 48 :
                print( "Tourne depuis " + str(time()-start) + " secondes")
                for thread in threads :
                    thread.join()
                threads = []
        
        for thread in threads :
            thread.join()
