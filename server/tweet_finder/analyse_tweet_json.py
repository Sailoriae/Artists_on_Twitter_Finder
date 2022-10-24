#!/usr/bin/python3
# coding: utf-8


"""
Fonction permettant d'analyser le JSON d'un Tweet (API v1.1 ou v2), et d'en
sortir le dictionnaire pour faciliter l'indexation.

Cette fonction a été constuite de manière a émettre une erreur au moindre
changement dans les JSON de Tweets renvoyés par l'API de Twitter.

@param tweet_json Dictionnaire (JSON) d'entrée, renvoyé par l'API Twitter.
@return Dictionnaire contenant les champs suivants :
        - "images" : Liste des URLs des images contenues dans ce Tweet,
        - "tweet_id" : ID du Tweet,
        - "user_id" : ID de l'auteur du Tweet,
        Ou None si le Tweet ne contient pas d'image.
"""
def analyse_tweet_json ( tweet_json : dict ) -> dict :
    tweet_dict = {}
    
    # Supprimer les tweets qui sont des retweets
    # Ne supprime pas les Tweets citant un autre Tweet (Et donc pouvant
    # contenir des images)
    if ( "retweeted_status" in tweet_json or
         "retweeted_status_id_str" in tweet_json or
         "retweeted_status_result" in tweet_json # API GraphQL (SNScrape)
        ) :
        if tweet_json["full_text"][:4] != "RT @" :
            raise Exception( f"Le Tweet ID {tweet_json['id_str']} a été interprété comme un retweet alors qu'il n'y ressemble pas" ) # Doit tomber dans le collecteur d'erreurs
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
        # Il faut être très stricte en vérifiant que le Tweet n'ait
        # effectivement pas de médias
        if not "entities" in tweet_json :
            raise Exception( f"Le Tweet ID {tweet_json['id_str']} n'a pas de champs \"entities\"" ) # Doit tomber dans le collecteur d'erreurs
        if ( "media" in tweet_json["entities"] and
             len( tweet_json["entities"]["media"] > 0 ) ) :
            raise Exception( f"Le Tweet ID {tweet_json['id_str']} a des médias qui n'ont pas pu être trouvés" ) # Doit tomber dans le collecteur d'erreurs
        return None
    
    for tweet_media in tweet_medias :
        if tweet_media["type"] == "photo" :
            # Sortir les vignettes de vidéos (De toutes manières, la BDD ne
            # peut pas stocker leur URL, car différent des images)
            if tweet_media["media_url_https"][:42] == "https://pbs.twimg.com/amplify_video_thumb/" :
                continue
            
            tweet_dict["images"].append( tweet_media["media_url_https"] )
    
    if len(tweet_dict["images"]) == 0 :
        return None
    
    if len(tweet_dict["images"]) > 4 :
        raise Exception( f"Le Tweet ID {tweet_dict['tweet_id']} a été analysé avec plus de 4 images" ) # Doit tomber dans le collecteur d'erreurs
    
    return tweet_dict
