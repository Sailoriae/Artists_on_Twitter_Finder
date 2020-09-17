#!/usr/bin/python3
# coding: utf-8


"""
Obtenir le modèle du JSON d'une requête utilisateur.
"""
def get_user_request_json_model () :
    return {
        "status" : "",
        "has_first_time_scan" : False,
        "twitter_accounts" : [],
        "results" : [],
        "error" : None }


"""
Générer le JSON d'une requête utilisateur.
"""
def generate_user_request_json ( request, response_dict = None ) -> dict :
    if response_dict == None :
        response_dict = get_user_request_json_model()
    response_dict["status"] = request.get_status_string()
    
    if request.has_first_time_scan :
        response_dict["has_first_time_scan"] = True
    
    for account in request.twitter_accounts_with_id :
        account_dict = { "account_name" : account[0],
                         "account_id" : str(account[1]) }
        response_dict["twitter_accounts"].append( account_dict )
    
    for result in request.founded_tweets :
        tweet_dict = { "tweet_id" : str(result.tweet_id),
                       "account_id" : str(result.account_id),
                       "image_position" : result.image_position,
                       "distance_chi2" : result.distance_chi2,
                       "distance_bhattacharyya" : result.distance_bhattacharyya }
        response_dict["results"].append( tweet_dict )
    
    response_dict["error"] = request.problem
    
    return response_dict
