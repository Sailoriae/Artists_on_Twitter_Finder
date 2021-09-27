#!/usr/bin/python3
# coding: utf-8

import numpy as np
from typing import List
import cv2

from class_ColorDescriptor import ColorDescriptor


# En téléchargeant les images de Tweets en qualité maximale, on est globalement
# plus précis, mais c'est toujours pas assez
# On ne peut donc pas baisser les seuils


# =============================================================================
# DISTANCE DU HKI-DEUX
# 0 = Les images sont les mêmes, puis tend vers l'infini
# =============================================================================

# SEUIL MAXIMUM
# On met un seuil élevé, car à cause de la compression de Twitter, des images
# identiques peut être très éloignées
# Et le laisser élevé, car c'est le thread 4 qui filtre derrière
SEUIL_CHI2 = 20 # La distance doit être en dessous

# Attention : Inverser les entrées change le résultat !
# Exemples d'images qui mettent une grosse distance dans un sens :
# https://danbooru.donmai.us/posts/4057141
# https://danbooru.donmai.us/posts/4059649
# https://derpibooru.org/2456926
# https://danbooru.donmai.us/posts/3933635


# =============================================================================
# DISTANCE DE BHATTACHARYYA
# 0 = Les images sont les mêmes, 1 = ne sont absolument pas les mêmes
# =============================================================================

# SEUIL MAXIMUM
# Ne pas mettre trop haut, car ce test de distance filtre très bien les sketchs
# et dessins en noir et blanc lors de la recherche d'une image en couleur
SEUIL_BHATTACHARYYA = 0.3 # La distance doit être en dessous

# Exemple d'image qui met une grosse distance :
# https://danbooru.donmai.us/posts/4158825


# =============================================================================
# AUTRES TESTS DE DISTANCE ?
# =============================================================================

# Note importante : Ca ne sert à rien d'ajouter d'autres algorithmes de
# comparaison des histogrammes, ils se vautrent tous sur les images très
# claires, comme par exemple les linearts
# Exemple : https://danbooru.donmai.us/posts/3544450
# Fonctionne mieux avec la modification qui télécharge les images de Tweets en
# qualité maximale.

# Autre tests essayés, mais ça ne sert à rien :
# - Corrélation (Attention : Plus est haut, plus les images sont proches) :
# d = cv2.compareHist( query_features, features, cv2.HISTCMP_CORREL )
# - Intersection (Attention : Plus est haut, plus les images sont proches) :
# d = cv2.compareHist( query_features, features, cv2.HISTCMP_INTERSECT )
# - Distance euclidienne :
# d = cv2.norm( query_features, features, cv2.NORM_L2 )
# - Distance de Manhattan / Taxicab :
# d = cv2.norm( query_features, features, cv2.NORM_L1 )


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
    Recherche inversée d'image
    @param image Image de requête, au format de la librairie Python-OpenCV
    @param images_iterator Itérateur sur la base de données, revoyant des
                           objets contenant les attributs suivants :
                           - image_features : La liste des caractéristiques
                                              de l'image
                           - distance : Un attribut pour stocker la distance
                             avec l'image de requête
    @return Liste d'objets renvoyés par l'itérateur
            Cette liste ne contient pas toutes les images de la BDD, mais
            seulement celles qui ont des distances de l'image de requête
            inférieures aux variables de seuil (Voir ci-dessus)
    """
    def search_cbir( self, image : np.ndarray, images_iterator ) :
        # Liste d'identifiants d'images trouvées
        results = []
        
        # On commence par calculer la liste des caractéristiques de l'image de
        # requête, afin de la comparer à celles de la base de données (Ou
        # plutôt celles proposées par l'itérateur)
        query_features = np.float32( self.cd.describe(image) )
        
        # Documentation OpenCV pour calculer des histogrammes :
        # https://docs.opencv.org/2.4/modules/imgproc/doc/histograms.html#comparehist
        
        # =====================================================================
        # RECHERCHE INVERSEE AVEC LA DISTANCE DE BHATTACHARYYA
        # En premier car plus rapide que le Khi-Deux
        # =====================================================================
        # On itére sur toutes les images que nous propose l'itérateur
        for image in images_iterator :
            features = np.float32( image.image_features)
            
            # Distance de Bhattacharyya (Qui est aussi la distance de
            # Hellinger dans OpenCV)
            # https://fr.wikipedia.org/wiki/Distance_de_Bhattacharyya
            # Plus la distance est faible, plus les images sont proches
            # Compris entre 0 et 1
            d = cv2.compareHist( query_features, features, cv2.HISTCMP_BHATTACHARYYA )
            
            # Si la distance est inférieure à un certain seuil, on ajoute
            # l'identifiant de l'image en cours sur l'itérateur à notre liste
            # de résultats
            if d < SEUIL_BHATTACHARYYA :
                image.distance_bhattacharyya = d
                results.append( image )
        
        # =====================================================================
        # FILTRAGE AVEC LA DISTANCE DU HKI-DEUX
        # En deuxième car légèrement plus lent, et en plus on en fait deux
        # =====================================================================
        # On itére sur les images trouvées / validées précédemment
        results_old = results
        results = []
        for image in results_old :
            features = np.float32( image.image_features)
            
            # Test du khi-deux
            # https://fr.wikipedia.org/wiki/Test_du_%CF%87%C2%B2
            # Plus la distance est faible, plus les images sont proches
            # Compris entre 0 et l'infini
            # On prend le min(), car ce test est asymétrique
            d = min( cv2.compareHist( query_features, features, cv2.HISTCMP_CHISQR ),
                     cv2.compareHist( features, query_features, cv2.HISTCMP_CHISQR ) )
            
            # Si la distance est inférieure à un certain seuil, on ajoute
            # l'identifiant de l'image en cours sur l'itérateur à notre liste
            # de résultats
            if d < SEUIL_CHI2 :
                image.distance_chi2 = d
                results.append( image )
        
        # Retourner  la liste des résultats
        return results
