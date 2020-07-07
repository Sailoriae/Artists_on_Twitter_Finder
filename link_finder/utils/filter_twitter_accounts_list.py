#!/usr/bin/python3
# coding: utf-8

# Liste des comptes Twitter officiels des sites qu'on explore
OFFICIAL_ACCOUNTS_LIST = [ "DeviantArt" ]

from typing import List


"""
Permet de filtrer une liste de comptes Twitter.
Supprime les doublons, et les comptes Twitter des sites qu'on explore.
"""
def filter_twitter_accounts_list ( accounts_list : List[str] ) -> List[str] :
    return_list : List[str] = []
    for account in accounts_list :
        if account not in OFFICIAL_ACCOUNTS_LIST and account not in return_list :
            return_list.append( account )
    return return_list
