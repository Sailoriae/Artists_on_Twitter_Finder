#!/usr/bin/python3
# coding: utf-8

import numpy as np
from typing import List
import cv2

try :
    from class_ColorDescriptor import ColorDescriptor
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .class_ColorDescriptor import ColorDescriptor


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
#        self.cd = ColorDescriptor( (8, 12, 3) ) # 5 * 288 valeurs = 1440 car 5 zones
        self.cd = ColorDescriptor( (4, 6, 2) ) # 5* 48 valeurs = 240 car 5 zones
        # 1440 / 240 = 6 donc l'espace pris est divisé par 6
        
        # SI CE PARAMETRE EST CHANGE, IL FAUT RESET LA BASE DE DONNEES !
        # Changer aussi le calcul dans le stockage (Module database)
        
        # Valeur baissée pour les raisons suivantes :
        # - Gros gain d'espace dans la base de données
        # - Gain de temps et de mémoire vive lors des calculs
        # - Pas besoin d'une grande précision car on réduit les tweets comparés
        #   à ceux des comptes de l'artiste. On ne recherche jamais dans toute
        #   la BDD, cela serait trop lent en plus
    
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
    
    Puis on multiplie cette valeur par la distance de Bhattacharyya
    https://fr.wikipedia.org/wiki/Distance_de_Bhattacharyya
    
    @return La différence entre les deux images
            Plus elle est faible, plus les images sont similaires
    """
    def chi2_distance( self, histA, histB ):
        # Calculer la distance avec le test du khi-deux
        # Documentation : https://docs.opencv.org/2.4/modules/imgproc/doc/histograms.html#comparehist
        d = cv2.compareHist( np.float32(histA), np.float32(histB), cv2.HISTCMP_CHISQR )
        
        # On calcul ausi la distance de Bhattacharyya (Qui est la même que la
        # distance de Hellinger dans OpenCV)
        # Permet d'être plus certain du résultat
        # Ce résultat est compris entre 0 et 1, avec 0 les images sont les
        # mêmes, et 1 les images sont complétement différentes
        d = d * cv2.compareHist( np.float32(histA), np.float32(histB), cv2.HISTCMP_BHATTACHARYYA )
        
        # Retourner cette distance
        return d
    
    """
    Recherche d'image inversé
    @param image Image de requête, au format de la librairie Python-OpenCV
    @param images_iterator Itérateur sur la base de données, revoyant des
                           objets contenant les attributs suivants :
                           - image_features : La liste des caractéristiques
                                              de l'image
                           - distance : Un attribut pour stocker la distance
                             avec l'image de requête
    @param SEUIL Seuil de distance entre deux images pour considérer qu'elles
                 sont les mêmes (OPTIONNEL). Permet de réduire la taille de la
                 liste retournée !
    @return Liste d'objets renvoyés par l'itérateur
            Cette liste ne contient pas toutes les images de la BDD, mais
            seulement celles qui ont une distance de l'image de requête
            inférieure à la variable SEUIL
    """
    def search_cbir( self, image : np.ndarray, images_iterator, SEUIL = None ) :
        # Liste d'identifiants d'images trouvées
        results = []
        
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
            if SEUIL == None or d < SEUIL :
                image.distance = d
                results.append( image )
        
        # Retourner  la liste des résultats
        return results
