# Module Outils pour le moteur de CBIR avec BDD

Ce module contient des outils pour la classe `CBIR_Engine_with_Database` :

* Fonction `url_to_cv2_image` : Retourne une image au bon format pour le moteur CBIR à partir de l'URL de cette image.

* Fonction `url_to_content` : Retourne le contenu binaire disponible à une URL.

* Fonction `get_tweet_image`: Même que `url_to_content`, mais gérer les erreurs communes pour des images de Tweet. A n'utiliser que pour des URL menant à des images de Tweets !
