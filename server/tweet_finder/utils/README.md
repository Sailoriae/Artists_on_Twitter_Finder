# Module Outils pour le moteur de CBIR avec BDD

Ce module contient des outils pour les classes du Tweet Finder :

* Fonction `url_to_PIL_image` : Retourne une image au bon format pour le moteur CBIR (Objet `PIL.Image`) à partir de l'URL de cette image.
  Utilise les fonctions `url_to_content` et `binary_image_to_cv2_image`.

* Fonction `binary_image_to_PIL_image` : Retourne une image au bon format pour le moteur CBIR (Objet `PIL.Image`) à partir du contenu binaire de l'image (Objet Python `bytes`).

* Fonction `url_to_content` : Retourne le contenu binaire (Objet Python `bytes`) disponible à une URL.

* Fonction `get_tweet_image`: Même que `url_to_content`, mais gérer les erreurs communes pour des images de Tweet. A n'utiliser que pour des URL menant à des images de Tweets !
