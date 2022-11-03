#!/usr/bin/python3
# coding: utf-8

from PIL import Image
import scipy.fftpack
import numpy


# Taille des empreintes. La taille des empreintes en bits sera le carré de
# cette valeur. Si cette valeur est changé, la base de données doit être reset.
HASH_SIZE = 8
# J'ai testé de monter à 144 bits. Déjà, les images qui avaient une distance de
# 6 bits passent à 14. Il faut donc augmenter le seuil si on veut garder notre
# tolérance aux légères modifications.
# Sauf que les faux positifs qui étaient égaux (Distance 0 en 64 bits) passent
# à 18-20 bits. Normal, pHash est plus précis quand on augmente la taille.
# Après, est-ce que c'est utile ? Car les faux positifs sont souvent des images
# à la con (Couleur unie avec une petite crotte à un endroit).
# A 256 bits, la distance entre les faux positifs explose, et notre seuil de
# tolérance passerait à 20.
# Le problème est qu'augmenter la taille des hash conduirait à plus de
# résultats ayant une distance strictement supérieure à zéro, et donc
# limiterait les résultas dans le cas d'une recherche dans toute la base de
# données.

# Nombre maximum de bits de différence pour considérer que des images sont les
# mêmes. Cette valeur doit être ajustée en fonction de la taille des
# empreintes (Défini ci-dessus).
# Le choix de 10 bits pour des empreintes de 64 vient de l'article suivant :
# http://www.hackerfactor.com/blog/?/archives/529-Kind-of-Like-That.html
# Sauf que pHash est tellement précis que j'ai réduit à 6 bits.
MAX_DIFFERENT_BITS = 6


"""
Moteur de recherche d'image par le contenu ("content-based image retrieval",
CBIR), généraliste, mais ne stocke rien ! La comparaison entre les images se
fait par calcul d'empreintes, grâce à l'algorithme pHash.

Apparemment, pHash génére moins de collision de dHash. Source :
https://www.hackerfactor.com/blog/?/archives/529-Kind-of-Like-That.html
"""
class CBIR_Engine :
    """
    Calculer l'empreinte d'une image.
    @param image Une image au format PIL.Image.
    @return Son empreinte.
    """
    def _phash( self, image : Image,
                hash_size : int = HASH_SIZE, highfreq_factor : int = 4 ) -> int :
        # Code venant de la librairie Python "ImageHash" :
        # https://github.com/JohannesBuchner/imagehash
        # BSD 2-Clause "Simplified" License, Copyright (c) Johannes Buchner
        # On a copié-collé ce code au lieu d'utiliser la librairie pour éviter
        # de passer par une étape supplémentaire. On gagne que dalle, mais
        # c'est toujours ça de gagné.
        img_size = hash_size * highfreq_factor
        
        # J'ai testé avec OpenCV (Librairie "OpenCV-Python"), et bizarrement,
        # elle est plus lente pour faire le passage en nuance de gris et le
        # redimensionnement. Pas de beaucoup, 1.3 fois plus lent environ.
        # Code OpenCV, l'image doit être une "numpy.ndarray" (La fonction
        # "url_to_cv2_image()" existe encore dans "old_cbir_engine") :
        # cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # cv2.resize(image, (img_size, img_size), interpolation = cv2.INTER_AREA)
        image = image.convert("L").resize((img_size, img_size), Image.ANTIALIAS)
        
        pixels = numpy.asarray(image)
        dct = scipy.fftpack.dct(scipy.fftpack.dct(pixels, axis=0), axis=1)
        dctlowfreq = dct[:hash_size, :hash_size]
        med = numpy.median(dctlowfreq)
        diff = dctlowfreq > med
        
        # Méthode environ 3 fois plus rapide que de passer par une string
        # String : int( "".join(str(b) for b in 1 * diff.flatten()), 2 )
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
    @param image Une image au format PIL.Image.
    @return Son empreinte.
    """
    def index_cbir( self, image : Image ) -> int :
        return self._phash( image )
    
    """
    Recherche par image.
    
    @param image Image de requête, au format PIL.Image.
    @param images_iterator Itérateur sur la base de données, revoyant des
                           dictionnaires contenant les champs suivants :
                           - image_hash : L'empreinte de l'image,
                           - distance : Un attribut pour stocker la distance
                             avec l'image de requête.
    
    @return Liste d'objets renvoyés par l'itérateur.
            Cette liste ne contient pas toutes les images de la BDD, mais
            seulement celles qui ont des distances de l'image de requête
            inférieures à la variable de seuil (Voir ci-dessus).
    """
    def search_cbir( self, image : Image, images_iterator ) :
        # Liste des images de l'itérateur qu'on a validées
        results = []
        
        # On commence par calculer l'empreinte de l'image de requête, afin de
        # la comparer aux empreintes des images dans la base de données (Ou
        # plutôt celles proposées par l'itérateur)
        query_hash = self._phash( image )
        
        # On itére sur toutes les images que nous propose l'itérateur
        for image in images_iterator :
            # Calcul de la distance de Hamming
            distance = self._hamming_distance( query_hash, image["image_hash"] )
            
            # Si la distance est inférieure à un certain seuil, on ajoute
            # l'identifiant de l'image en cours sur l'itérateur à notre liste
            # de résultats
            if distance <= MAX_DIFFERENT_BITS :
                image["distance"] = distance
                results.append( image )
        
        return results
