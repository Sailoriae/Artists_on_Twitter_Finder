#!/usr/bin/python3
# coding: utf-8

import cv2
import numpy as np


# Taille des empreintes. La taille des empreintes en bits sera le carré de
# cette valeur. Si cette valeur est changé, la base de données doit être reset.
HASH_SIZE = 8

# Nombre maximum de bits de différence pour considérer que des images sont les
# mêmes. Cette valeur doit être ajustée en fonction de la taille des
# empreintes (Défini ci-dessus).
# Le choix de 10 bits pour des empreintes de 64 vient de l'article suivant :
# http://www.hackerfactor.com/blog/?/archives/529-Kind-of-Like-That.html
MAX_DIFFERENT_BITS = 10


"""
Moteur de recherche d'image par le contenu ("content-based image retrieval",
CBIR), généraliste, mais ne stocke rien ! La comparaison entre les images se
fait par calcul d'empreintes, grâce à l'algorithme dHash.
"""
class CBIR_Engine :
    """
    Calculer l'empreinte d'une image.
    https://www.pyimagesearch.com/2017/11/27/image-hashing-opencv-python/
    @param image Une image, au format de la librairie Python-OpenCV (BGR).
    @return Son empreinte.
    """
    def _dhash( self, image : np.ndarray ) -> int :
        # Convertir l'image en niveaux de gris (Noir et blanc)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Redimensionner l'image, en ajoutant une colonne (Largeur) par rapport
        # au lignes (Hauteur) pour pouvoir calculer le gradient horizontal
        resized = cv2.resize(gray, (HASH_SIZE + 1, HASH_SIZE))
        
        # Calculer le gradient horizontalement (Relatif) entre les colonnes
        # adjacentes
        diff = resized[:, 1:] > resized[:, :-1]
        
        # Convertir cette liste en un nombre unique
        return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])
    
    """
    Comparaison bits à bits en calculant la distance de Hamming entre deux
    empreintes.
    @param hash_1 Première empreinte.
    @param hash_2 Seconde empreinte.
    @return Le nombre de bits de différence.
    """
    def _hamming_distance( self, hash_1 : int, hash_2 : int ) -> int :
        return bin( int( hash_1 ) ^ int( hash_2 ) ).count("1")
    
    """
    Calculer l'empreinte d'une image en vue de l'indexer.
    @param image Une image, au format de la librairie Python-OpenCV (BGR).
    @return Son empreinte.
    """
    def index_cbir( self, image : np.ndarray ) -> int :
        return self._dhash( image )
    
    """
    Recherche par image.
    
    @param image Image de requête, au format de la librairie Python-OpenCV.
    @param images_iterator Itérateur sur la base de données, revoyant des
                           objets contenant les attributs suivants :
                           - image_hash : L'empreinte de l'image,
                           - distance : Un attribut pour stocker la distance
                             avec l'image de requête.
    
    @return Liste d'objets renvoyés par l'itérateur.
            Cette liste ne contient pas toutes les images de la BDD, mais
            seulement celles qui ont des distances de l'image de requête
            inférieures à la variable de seuil (Voir ci-dessus).
    """
    def search_cbir( self, image : np.ndarray, images_iterator ) :
        # Liste des images de l'itérateur qu'on a validées
        results = []
        
        # On commence par calculer l'empreinte de l'image de requête, afin de
        # la comparer aux empreintes des images dans la base de données (Ou
        # plutôt celles proposées par l'itérateur)
        query_hash = self._dhash( image )
        
        # On itére sur toutes les images que nous propose l'itérateur
        for image in images_iterator :
            # Calcul de la distance de Hamming
            distance = self._hamming_distance( query_hash, image.image_hash )
            
            # Si la distance est inférieure à un certain seuil, on ajoute
            # l'identifiant de l'image en cours sur l'itérateur à notre liste
            # de résultats
            if distance <= MAX_DIFFERENT_BITS :
                image.distance = distance
                results.append( image )
        
        return results
