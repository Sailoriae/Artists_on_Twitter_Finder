# Limites du moteur CBIR

A cause de la compression Twitter et **surtout** du fait qu'il utilise uniquement le modèle des histogrammes (Pour extraire les vecteurs des images), le moteur CBIR a du mal avec les images très claires, comme par exemple les "linearts" ou les "sketchs", c'est à dire les images en noir et blanc.

Grace au double calcul de distances (Khi-Deux et Bhattacharyya / Hellinger), si on donne au moteur une image de requête en couleur, il ne va pas sortir d'image en noir et blanc. En revanche, il peut avoir du mal avec une image de requête en noir et blanc.

D'où l'intérêt de l'étape 4 (Filtrage des résultats). Même si cette étape a aussi du mal.

Il y a donc de grandes améliorations à faire, au point de pouvoir supprimer l'étape 4.
