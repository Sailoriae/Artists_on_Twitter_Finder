#!/usr/bin/python3
# coding: utf-8


"""
Fonction permettant d'analyser le JSON d'un Tweet (API v1.1 ou v2), et d'en
sortir le dictionnaire pour faciliter l'indexation.

Cette fonction a été constuite de manière a émettre une erreur au moindre
changement dans les JSON de Tweets renvoyés par l'API de Twitter.

@param tweet_json Dictionnaire (JSON) d'entré, renvoyé par l'API Twitter.
@return Dictionnaire contenant les champs suivants :
        - "images" : Liste des URLs des images contenues dans ce Tweet,
        - "tweet_id" : ID du Tweet,
        - "user_id" : ID de l'auteur du Tweet,
        - "hashtags" : Liste des hashtags contenus dans ce Tweet.
        Ou None si le Tweet ne contient pas d'image.
"""
def analyse_tweet_json ( tweet_json : dict ) -> dict :
    tweet_dict = {}
    
    # Supprimer les tweets qui sont des retweets
    # Ne supprime pas les Tweets citant un autre Tweet (Et donc pouvant
    # contenir des images)
    if "retweeted_status" in tweet_json or "retweeted_status_id_str" in tweet_json :
        return None
    
    # ID du Tweet
    tweet_dict["tweet_id"] = tweet_json["id_str"] # ID du Tweet
    
    # ID de l'auteur du Tweet
    if "user_id_str" in tweet_json : # API v2
        tweet_dict["user_id"] = tweet_json["user_id_str"]
    else : # API v1.1
        tweet_dict["user_id"] = tweet_json["user"]["id_str"]
    
    # Liste des URLs des images contenues dans ce Tweet
    tweet_dict["images"] = []
    try :
        tweet_medias = tweet_json["extended_entities"]["media"]
    except KeyError : # Tweet sans média
        return None
    for tweet_media in tweet_medias :
        if tweet_media["type"] == "photo" :
            tweet_dict["images"].append( tweet_media["media_url_https"] )
    
    if len(tweet_dict["images"]) == 0 :
        return None
    
    if len(tweet_dict["images"]) > 4 :
        raise Exception( f"Le Tweet ID {tweet_dict['tweet_id']} a été analysé avec plus de 4 images" ) # Doit tomber dans le collecteur d'erreurs
    
    # Liste des hashtags contenus dans ce Tweet
    tweet_dict["hashtags"] = []
    try :
        for hashtag in tweet_json["entities"]["hashtags"] :
            tweet_dict["hashtags"].append( "#" + hashtag["text"] )
    except KeyError : # Tweet sans hashtag
        pass
    
    return tweet_dict
