#!/usr/bin/python3
# coding: utf-8

import numpy as np
from typing import List
import cv2

try :
    from class_ColorDescriptor import ColorDescriptor
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .class_ColorDescriptor import ColorDescriptor

# On met un seuil élevé, car à cause de la compression de Twitter, des images
# identiques peut être très éloignées
# Et le laisser élevé, car c'est le thread 4 qui filtre derrière
# 0 = Les images sont les mêmes, puis tend vers l'infini
SEUIL_CHI2 = 20 # L'image doit être en dessous
# Exemple d'image qui met une grosse distance (11,9) :
# https://danbooru.donmai.us/posts/4057141
# Autre exemple (16,8) :
# https://danbooru.donmai.us/posts/4059649

# Idem pour ce seuil, mais le laisser par trop haut non plus, car ce test de
# distance filtre très bien les sketchs et dessins en noir et blanc
# 0 = Les images sont les mêmes, 1 = ne sont absolument pas les mêmes
SEUIL_BHATTACHARYYA = 0.2 # L'image doit être en dessous


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
    Recherche d'image inversé
    @param image Image de requête, au format de la librairie Python-OpenCV
    @param images_iterator Itérateur sur la base de données, revoyant des
                           objets contenant les attributs suivants :
                           - image_features : La liste des caractéristiques
                                              de l'image
                           - distance : Un attribut pour stocker la distance
                             avec l'image de requête
    @return Liste d'objets renvoyés par l'itérateur
            Cette liste ne contient pas toutes les images de la BDD, mais
            seulement celles qui ont une distance de l'image de requête
            inférieure à la variable SEUIL
    """
    def search_cbir( self, image : np.ndarray, images_iterator ) :
        # Liste d'identifiants d'images trouvées
        results = []
        
        # On commence par calculer la liste des caractéristiques de l'image de
        # requête, afin de la comparer à celles de la base de données (Ou
        # plutôt celles proposées par l'itérateur)
        query_features = np.float32( self.cd.describe(image) )
        
        # On itére sur toutes les images que nous propose l'itérateur
        for image in images_iterator :
            features = np.float32( image.image_features)
            
            # Calculer les distances entre l'image de requête et l'image en
            # cours sur l'itérateur
            # Documentation :
            # https://docs.opencv.org/2.4/modules/imgproc/doc/histograms.html#comparehist
            
            # - Test du khi-deux
            #   https://fr.wikipedia.org/wiki/Test_du_%CF%87%C2%B2
            # Plus la distance est faible, plus les images sont proches
            # Compris entre 0 et l'infini
            d1 = cv2.compareHist( query_features, features, cv2.HISTCMP_CHISQR )
            
            # - Distance de Bhattacharyya (Qui est aussi la distance de
            #   Hellinger dans OpenCV)
            #   https://fr.wikipedia.org/wiki/Distance_de_Bhattacharyya
            # Plus la distance est faible, plus les images sont proches
            # Compris entre 0 et 1
            d2 = cv2.compareHist( query_features, features, cv2.HISTCMP_BHATTACHARYYA )
            
            # Si les distances sont inférieures à un certain seuil, on ajoute
            # l'identifiant de l'image en cours sur l'itérateur à notre liste
            # de résultats
            if d1 < SEUIL_CHI2 and d2 < SEUIL_BHATTACHARYYA :
                image.distance_chi2 = d1
                image.distance_bhattacharyya = d2
                results.append( image )
        
        # Retourner  la liste des résultats
        return results
