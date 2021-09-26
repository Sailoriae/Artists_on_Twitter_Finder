#!/usr/bin/python3
# coding: utf-8

import numpy as np
import cv2
import imutils
from typing import List


"""
Cette classe est un moteur d'extraction de caractéristiques d'une image
("image features descriptor").
https://fr.wikipedia.org/wiki/Extraction_de_caract%C3%A9ristique_en_vision_par_ordinateur

Ce genre de moteur doit normalement pouvoir extraire des caractéristiques dans
la couleur, la texture, et les formes.
Le notre ne fait que la couleur, mais est un peu amélioré.
Il analyse les couleurs en HSV (Teinte, saturation et luminosité) et non en RGB
(Rouge, vert et bleu).
"""
class ColorDescriptor :
    """
    Constructeur
    @param bins Un triplet, correspondant au nombre d'échantillons de
                l'histogramme à 3 dimensions (Ou 3 cannaux) :
                - Première dimension : Teinte ("Hue")
                - Deuxième dimension : Saturation ("Saturation")
                - Troisième dimension : Luminosité ("Brightness" / "Value")
                Valeurs recommandées : (8, 12, 3)
    """
    def __init__( self, bins : int ) :
        # Stocke le nombre d'échantillon dans l'histogramme à 3 dimensions
        self.bins = bins
    
    """
    Extraction des caractéristiques d'une image
    L'image est découpée en 5 zones qui sont traitées indépendemments :
    - Une ellipse centrale
    - Le quart haut-gauche moins l'ellipse centrale
    - Le quart haut-droit moins l'ellipse centrale
    - Le quart bas-droit moins l'ellipse centrale
    - Le quart bas-gauche moins l'ellipse centrale
    
    @param image Une image, au format de la librairie Python-OpenCV
    @return La liste des caractéristiques de l'image
    """
    def describe( self, image : np.ndarray ) -> List[float] :
        # Convertir l'image depuis RGB vers HSV
        # Note : cv2.imdecode() décode toujours les images vers du BGR
        image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Initialiser la liste des caractéristiques de l'image que l'on va
        # retourner
        features = []
        
        # Stocker les dimensions de l'image et calculer son centre
        (h, w) = image.shape[:2]
        (cX, cY) = (int(w * 0.5), int(h * 0.5))
        
        # Diviser l'image en quatre rectangles, dans l'ordre suivant :
        # haut-gauche, haut-droit, bas-droit, bas-gauche
        segments = [(0, cX, 0, cY), (cX, w, 0, cY), (cX, w, cY, h), (0, cX, cY, h)]
        
        # Construire un masque en forme d'ellipse au centre de l'image
        (axesX, axesY) = (int(w * 0.75) // 2, int(h * 0.75) // 2)
        ellipMask = np.zeros(image.shape[:2], dtype = "uint8")
        cv2.ellipse(ellipMask, (cX, cY), (axesX, axesY), 0, 0, 360, 255, -1)
        
        # Traiter chaque quart / rectangles de l'image
        for (startX, endX, startY, endY) in segments:
            # Construire le masque du rectangle / coin de l'image, en
            # soustrayant l'ellipse centrale
            cornerMask = np.zeros(image.shape[:2], dtype = "uint8")
            cv2.rectangle(cornerMask, (startX, startY), (endX, endY), 255, -1)
            cornerMask = cv2.subtract(cornerMask, ellipMask)
            
            # Calculer l'histogramme 3D de la zone restante de l'image (C'est à
            # dire le  rectangle moins l'ellipse) et l'ajouter à la liste des
            # caractéristiques
            hist = self.histogram(image, cornerMask)
            features.extend(hist)
        
        # Calculer l'histogramme 3D de la zone de l'image pas encore
        # trairée (C'est à dire l'ellipse) et l'ajouter à la liste des
        # caractéristiques
        hist = self.histogram(image, ellipMask)
        features.extend(hist)
        
        # Retourner la liste des caractéristiques de l'image
        return features
    
    """
    Calcul l'histogramme 3D d'une partie de l'image
    @param image Une image, au format de la librairie Python-OpenCV
    @param mask
    @return
    """
    def histogram( self, image : np.ndarray, mask ) :
        # Extraire un histogramme 3D de la région masquée de l'image, en
        # utilisant le nombre d'échantillons par dimension
        hist = cv2.calcHist([image], [0, 1, 2], mask, self.bins, [0, 180, 0, 256, 0, 256])
        
        # Nomaliser l'histogramme
        if imutils.is_cv2(): # Si OpenCV 2.4
            hist = cv2.normalize(hist).flatten()
        else: # Si OpenCV 3+
            hist = cv2.normalize(hist, hist).flatten()
        
        # Retourner l'histogramme
        return hist
