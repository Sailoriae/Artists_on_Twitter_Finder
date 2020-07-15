# Module Outils pour le moteur de CBIR avec BDD

Ce module contient des outils pour la classe `CBIR_Engine_with_Database` :

* Classe `url_to_cv2_image` : Retourne une image au bon format pour le moteur CBIR à partir de l'URL de cette image.

Il contient aussi des outils non-utilisés dans ce projet, mais conservés au cas où :

* Fonction `add_argument_to_url` : Ajoute un argument à une URL.
  A été utilisée lors du test de téléchargement des images de GetOldTweets3 en meilleure qualité. Mais ce test ne fut pas concluant. Voir `class_CBIR_Engine_with_Database.py`.
