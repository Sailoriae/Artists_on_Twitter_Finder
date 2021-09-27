#!/usr/bin/python3
# coding: utf-8

import cv2
import matplotlib.pyplot as plt 
import itertools

from url_to_cv2_image import url_to_cv2_image


"""
Cette fonction permet d'afficher l'histogramme 3D d'une image.
On ne représente pas les "bins", c'est trop gros, on représente seulement les
points centraux.
En effet, il est impossible d'afficher un véritable histogramme 3D, car cela
reviendrait à représenter des cubes de couleurs variants avec l'intensité, mais
les cubes extérieurs masqueraient les cubes intérieurs. C'est pour cela que
cette fonction affiche des points à la place de cubes.

@param url URL de l'image dont il faut calculer l'histogramme.
"""
def plot_histogram( url, test_proof = False ) :
    # Nombre d'échantillons pour les 3 dimensions (HSV) de l'image
    bins = (8,12,3)
    
    # Obtenir l'image
    image = cv2.cvtColor( url_to_cv2_image( url ), cv2.COLOR_BGR2HSV)
    
    # Calculer son histogramme 3D avec OpenCV
    # On obtient alors un tableau à 3 dimensions
    # C'est ce tableau qu'on veut afficher
    hist = cv2.calcHist([image], [0, 1, 2], None, bins, [0, 180, 0, 256, 0, 256])
    
    # Normaliser et "applatir" l'histogramme en une seule liste
    hist_flat = cv2.normalize(hist, hist).flatten()
    
    # Créer la liste des échantillons sur les 3 dimensions
    h_indice = list(range(0,bins[0]))
    s_indice = list(range(0,bins[1]))
    v_indice = list(range(0,bins[2]))
    
    # Calculs du pas entre chaque valeurs
    h_step = 180/bins[0]
    s_step = 256/bins[1]
    v_step = 256/bins[2]
    
    # Mettre des pseudo-vraies-valeurs aux échentillons
    # Ce sont en vérité des "bins", mais comme c'est trop gros à représenter,
    # on représente seulement le point central
    h = [value * h_step + h_step/2 for value in h_indice]
    s = [value * s_step + s_step/2 for value in s_indice]
    v = [value * v_step + v_step/2 for value in v_indice]
    
    # Générer toutes les combinaisons possibles des 3 listes précédentes
    # Dans l'ordre HSV, c'est ainsi que cv2.normalize() "applatit"
    # J'ai vérifié manuellement, et cette liste est exactement dans le bon
    # ordre que la liste "hist_flat"
    # Ainsi, les coordonnées de cette liste correspondent aux valeurs dans la
    # liste "hist_flat"
    coord = list(itertools.product(*[h,s,v]))
    
    # Preuve de fonctionnement de ce que je raconte ci-dessus
    # On accède aux valeurs sans planter, alors que les échantillonnages des
    # 3 dimensions sont différents (8-12-3 pour respectivement H-S-V)
    if test_proof :
        for c in list(itertools.product(*[h_indice,s_indice,v_indice])) :
            hist[c[0]][c[1]][c[2]]
    # Pour tester que les axes ne sont pas inversés, il suffit de tester avec
    # des images couleur unique
    
    # Séparer la liste de tuples en trois listes
    h, s, v = list(zip(*coord))
    
    # Créer la figure Matplotlib
    fig = plt.figure( figsize = (16, 9) )
    ax = plt.axes( projection = "3d" )
    
    # Ajouter la grille
    ax.grid( b = True, color = "grey", 
             linestyle = "-.", linewidth = 0.3, 
             alpha = 0.2 ) 
    
    # Afficher les points
    sctt = ax.scatter3D( h, s, v,
                         alpha = 0.7,
                         c = hist_flat,
                         marker = "o",
                         cmap = "rainbow" )
    
    # Afficher la quatrième dimension (Intensité)
    cbar = fig.colorbar(sctt, ax = ax, shrink = 0.5, aspect = 5)
    
    # Afficher des légendes
    plt.title( "Histogramme 3D de l'image en HSV" )
    ax.set_xlabel( "Hue", fontweight = "bold" ) 
    ax.set_ylabel( "Saturation", fontweight = "bold" ) 
    ax.set_zlabel( "Value", fontweight = "bold" )
    cbar.ax.set_ylabel( "Intensités", fontweight = "bold" )
    
    # Modifier l'angle de vue pour avoir quelque chose de plus confortable
    ax.view_init(elev=10, azim=45)
    
    # Afficher le plot
    plt.show()


"""
Image de test / démo : https://danbooru.donmai.us/posts/4307427
"""
if __name__ == "__main__" :
    plot_histogram( "https://danbooru.donmai.us/data/__hatsune_miku_and_sakura_miku_vocaloid_drawn_by_ume_neko_otaku_nyanko__26c82358db3faf78456a9e5b1f96c22e.jpg" )
