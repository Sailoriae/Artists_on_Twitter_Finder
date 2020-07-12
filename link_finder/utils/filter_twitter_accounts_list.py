#!/usr/bin/python3
# coding: utf-8

# Liste des comptes Twitter officiels des sites qu'on explore
# METTRE ENTIEREMENT EN MINUSCULE ! Twitter n'est pas sensible à la casse pour
# les noms d'utilisateurs.
OFFICIAL_ACCOUNTS_LIST = [ "deviantart" ]

from typing import List


"""
Permet de filtrer une liste de comptes Twitter.
Supprime les doublons, et les comptes Twitter des sites qu'on explore.

Met en minuscule pour être certain de supprimer les doublons, car Twitterr
n'est pas sensible à la casse pour les noms d'utilisateurs.
"""
def filter_twitter_accounts_list ( accounts_list : List[str] ) -> List[str] :
    return_list : List[str] = []
    for account in accounts_list :
        account_lower = account.lower()
        if account_lower not in OFFICIAL_ACCOUNTS_LIST and account_lower not in return_list :
            return_list.append( account_lower )
    return return_list
