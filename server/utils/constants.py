#!/usr/bin/python3
# coding: utf-8

"""
Entête HTTP "User-Agent" qui est utilisé pour :
- Scrapper les sites supportés (Etape 1 : Link Finder),
- Obtenir les images des Tweets à indexer (Etape C : Indexation),
- Obtenir l'image de requête (Etape 3 : Recherche inversée).

Mettre ici un vrai navigateur, sinon Pixiv renverra une erreur HTTP !
On prend Firefox ESR comme valeur par défaut.
"""
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"
