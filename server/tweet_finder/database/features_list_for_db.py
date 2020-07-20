#!/usr/bin/python3
# coding: utf-8


"""
Etendre ou couper une liste à une longueur fixée.
En profite pour convertir la liste de numpy.float32 et liste de float.
"""
def features_list_for_db ( some_list ) :
    target_len = 240
    # Le moteur CBIR renvoit des listes de numpy.float32, donc il faut les
    # convertir en float() Python
    for i in range(len(some_list)) :
        some_list[i] = float( some_list[i] )
    return some_list[:target_len] + [None] *  ( target_len - len( some_list ) )
