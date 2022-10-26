#!/usr/bin/python3
# coding: utf-8

import re

# Duplication de code vers "analyse_tweet_json.py"
tweet_image_regex = re.compile( r"^https://pbs\.twimg\.com/media/([A-Za-z0-9_\-]{15})\.(png|jpg)$" )


"""
Fonction permettant d'analyser les Tweets dans les objets Response de l'API v2
via Tweepy, et d'en sortir des dictionnaires pour faciliter l'indexation.

Cette fonction a été constuite de manière a émettre une erreur au moindre
changement dans ce que Tweepy et l'API v2 nous renvoient.

@param tweepy_response Objet Response de la librairie Tweepy.
@return Itérateur de dictionnaires contenant les champs suivants :
        - "images" : Liste des URLs des images contenues dans ce Tweet,
        - "tweet_id" : ID du Tweet,
        - "user_id" : ID de l'auteur du Tweet,
        Un Tweet qui ne contient pas d'image n'est pas retourné.
"""
def analyse_tweepy_response ( tweepy_response ) :
    # Aucun Tweet avec médias
    if not "media" in tweepy_response.includes :
        yield from []
        return # Pour bloquer la suite
    
    # Aucun Tweet retourné
    if not tweepy_response.data :
        yield from []
        return # Pour bloquer la suite
    
    for tweet in tweepy_response.data :
        tweet_dict = {}
        
        # Supprimer les tweets qui sont des retweets
        # Ne supprime pas les Tweets citant un autre Tweet (Et donc pouvant
        # contenir des images)
        if ( "referenced_tweets" in tweet and
             tweet["referenced_tweets"][0]["type"] == "retweeted" ) :
            # L'API v2 peut nous sortir des RTs de comptes suspendus, mais on
            # peut les détecter avec le texte, mais rien d'autre
            if tweet["text"][-95:] == "'s account is temporarily unavailable because it violates the Twitter Media Policy. Learn more." :
                return None
            
            # Il est possible qu'un retweet soit inaccessible pour des raisons
            # de copyrights
            if ( "withheld" in tweet and
                 tweet["withheld"]["scope"] in [ "user", "status" ] ) :
                return None
            
            if tweet["text"][:4] != "RT @" :
                raise Exception( f"Le Tweet ID {tweet.id} a été interprété comme un retweet alors qu'il n'y ressemble pas" ) # Doit tomber dans le collecteur d'erreurs
            continue
        
        # ID du Tweet
        tweet_dict["tweet_id"] = tweet["id"]
    
        # ID de l'auteur du Tweet
        tweet_dict["user_id"] = tweet["author_id"]
    
        # Liste des URLs des images contenues dans ce Tweet
        if not "attachments" in tweet : continue # Tweet sans média
        tweet_medias_keys = tweet["attachments"]["media_keys"]
        tweet_medias = []
        for media in tweepy_response.includes["media"] :
            if media["media_key"] in tweet_medias_keys :
                tweet_medias.append( media )
        if len( tweet_medias_keys ) != len( tweet_medias ) :
            raise Exception( f"Impossible de trouver tous les médias du Tweet ID {tweet.id}" )
        
        tweet_dict["images"] = []
        for tweet_media in tweet_medias :
            if tweet_media["type"] == "photo" :
                # Sortir les vignettes de vidéos (De toutes manières, la BDD ne
                # peut pas stocker leur URL, car différent des images)
                if tweet_media["url"][:42] == "https://pbs.twimg.com/amplify_video_thumb/" :
                    continue
                
                tweet_dict["images"].append( tweet_media["url"] )
    
        if len(tweet_dict["images"]) == 0 :
            continue
        
        for image_url in tweet_dict["images"] :
            if not re.fullmatch( tweet_image_regex, image_url ) :
                raise Exception( f"Le Tweet ID {tweet_dict['tweet_id']} a une URL d'image non-reconnue\n{image_url}" )
        
        if len(tweet_dict["images"]) > 4 :
            raise Exception( f"Le Tweet ID {tweet_dict['tweet_id']} a été analysé avec plus de 4 images" ) # Doit tomber dans le collecteur d'erreurs
        
        yield tweet_dict
