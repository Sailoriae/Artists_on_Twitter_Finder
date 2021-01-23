#!/usr/bin/python3
# coding: utf-8

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendemment (Notemment pour des
# tests), il faut que son répertoire de travail soit ce même répertoire
if __name__ == "__main__" :
    from os.path import abspath as get_abspath
    from os.path import dirname as get_dirname
    from os import chdir as change_wdir
    change_wdir(get_dirname(get_abspath(__file__)))
    change_wdir( "../.." )

import parameters as param

CBIR_LIST_LENGHT = 240


"""
Dictionnaire des grosses requêtes SQL à ne pas recalculer à chaque fois.
"""

sql_requests_dict = {}

insert_tweet_image_1 = "INSERT INTO tweets_images_1 VALUES ( ?, ?," + " ?," * CBIR_LIST_LENGHT
insert_tweet_image_1 = insert_tweet_image_1[:-1] # Suppression de la virgule finale

insert_tweet_image_2 = "INSERT INTO tweets_images_2 VALUES ( ?, ?," + " ?," * CBIR_LIST_LENGHT
insert_tweet_image_2 = insert_tweet_image_2[:-1] # Suppression de la virgule finale

insert_tweet_image_3 = "INSERT INTO tweets_images_3 VALUES ( ?, ?," + " ?," * CBIR_LIST_LENGHT
insert_tweet_image_3 = insert_tweet_image_3[:-1] # Suppression de la virgule finale

insert_tweet_image_4 = "INSERT INTO tweets_images_4 VALUES ( ?, ?," + " ?," * CBIR_LIST_LENGHT
insert_tweet_image_4 = insert_tweet_image_4[:-1] # Suppression de la virgule finale


if param.USE_MYSQL_INSTEAD_OF_SQLITE :
    insert_tweet_image_1 = insert_tweet_image_1.replace( "?", "%s" )
    insert_tweet_image_1 += " ) ON DUPLICATE KEY UPDATE tweets_images_1.tweet_id = tweets_images_1.tweet_id"
    
    insert_tweet_image_2 = insert_tweet_image_2.replace( "?", "%s" )
    insert_tweet_image_2 += " ) ON DUPLICATE KEY UPDATE tweets_images_2.tweet_id = tweets_images_2.tweet_id"
    
    insert_tweet_image_3 = insert_tweet_image_3.replace( "?", "%s" )
    insert_tweet_image_3 += " ) ON DUPLICATE KEY UPDATE tweets_images_3.tweet_id = tweets_images_3.tweet_id"
    
    insert_tweet_image_4 = insert_tweet_image_4.replace( "?", "%s" )
    insert_tweet_image_4 += " ) ON DUPLICATE KEY UPDATE tweets_images_4.tweet_id = tweets_images_4.tweet_id"


else :
    insert_tweet_image_1 += " ) ON CONFLICT ( tweet_id ) DO NOTHING"
    
    insert_tweet_image_2 += " ) ON CONFLICT ( tweet_id ) DO NOTHING"
    
    insert_tweet_image_3 += " ) ON CONFLICT ( tweet_id ) DO NOTHING"
    
    insert_tweet_image_4 += " ) ON CONFLICT ( tweet_id ) DO NOTHING"


sql_requests_dict["insert_tweet_image_1"] = insert_tweet_image_1
sql_requests_dict["insert_tweet_image_2"] = insert_tweet_image_2
sql_requests_dict["insert_tweet_image_3"] = insert_tweet_image_3
sql_requests_dict["insert_tweet_image_4"] = insert_tweet_image_4
