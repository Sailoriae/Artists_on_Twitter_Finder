#!/usr/bin/python3
# coding: utf-8

import numpy as np
from typing import List

try :
    from class_ColorDescriptor import ColorDescriptor
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .class_ColorDescriptor import ColorDescriptor


# Seuil de distance maximale (Calculé par la fonction "chi2_distance") entre
# deux listes de caractéristiques d'images, pour dire que ces deux images sont
# similaires ou sont les mêmes
# TODO : Faire des recherches sur comment fonctionne la fonction index_cbir()
# pour affiner ce seuil
# Là on a pris une grosse marge
SEUIL = 4


"""
Moteur de recherche d'image par le contenu ("content-based image retrieval",
CBIR), généraliste, mais ne stocke rien !
"""
class CBIR_Engine :
    """
    Constructeur
    """
    def __init__( self ) :
        # Initialiser le moteur d'extraction de caractéristiques d'une image
        self.cd = ColorDescriptor( (8, 12, 3) )
    
    """
    Extraction des caractéristiques d'une image
    @param image Une image, au format de la librairie Python-OpenCV
    @return La liste des caractéristiques de l'image
    """
    def index_cbir( self, image : np.ndarray ) -> List[float] :  
        return self.cd.describe( image )

    """
    Test du khi-deux / khi carré
    https://fr.wikipedia.org/wiki/Test_du_%CF%87%C2%B2
    
    Plus précisemment, il s'agit du test du khi-deux de Pearson
    https://fr.wikipedia.org/wiki/Test_du_%CF%87%C2%B2_de_Pearson
    
    @return La différence entre les deux images
            Plus elle est faible, plus les images sont similaires
    """
    def chi2_distance( self, histA, histB, eps = 1e-10 ):
        # Calculer la distance avec le test du khi-deux
        d = 0.5 * np.sum([((a - b) ** 2) / (a + b + eps)
            for (a, b) in zip(histA, histB)])
        
        # Retourner cette distance
        return d
    
    """
    Recherche d'image inversé
    @param image Image de requête, au format de la librairie Python-OpenCV
    @param images_iterator Itérateur sur la base de données, revoyant des
                           objets contenant les attributs suivants :
                           - image_features : La liste des caractéristiques
                                              de l'image
                           - identifier : Un identifiant pour cette image
    @return Liste de tuples, contenant :
            - L'identifiant de l'image, qui est du même type que
              images_iterator.identifier
            - La distance calculée avec l'image de requête, de type float
            Cette liste ne contient pas toutes les images de la BDD, mais
            seulement celles qui ont une distance de l'image de requête
            inférieure à la variable SEUIL
    """
    def search_cbir( self, image : np.ndarray, images_iterator ) :
        # Liste d'identifiants d'images trouvées
        results : List[ ( type(images_iterator), float ) ] = []
        
        # On commence par calculer la liste des caractéristiques de l'image de
        # requête, afin de la comparer à celles de la base de données (Ou
        # plutôt celles proposées par l'itérateur)
        query_features = self.cd.describe(image)
        
        # On itére sur toutes les images que nous propose l'itérateur
        for image in images_iterator :
            # Calculer la distance avec le test du khi-deux entre l'image de
            # requête et l'image en cours sur l'itérateur
            features = image.image_features
            d = self.chi2_distance(features, query_features)
            
            # Si la distance est inférieure à un certain seuil, on ajoute
            # l'identifiant de l'image en cours sur l'itérateur à notre liste
            # de résultatts
            if d < SEUIL :
                results.append( (image.identifier, d) )
        
        # Retourner  la liste des résultats
        return results
