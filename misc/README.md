# Artists on Twitter Finder : Divers

## Scripts qui sont utiles

* Script [`get_oauth_token.py`](get_oauth_token.py) :
  Permet d'obtenir les clés d'authentification à un compte Twitter.


## Archives et anciennes fonctionnalités

* Module [`old_cbir_engine`](old_cbir_engine) :
  Répertoire de l'ancien moteur de recherche par image. Celui-ci utilisé des histogrammes colorimétriques pour indexer.

* Script [`extract_tweets_ids_from_error_file.py`](extract_tweets_ids_from_error_file.py) :
  Ancien script de maintenance, quand le réessai des Tweets dont l'indexation a échouée n'était pas intégré au serveur.


## Scripts inutiles

* Script [`test_tweepy_rate_limits.py`](test_tweepy_rate_limits.py) :
  Permet de déterminer si Tweepy (Et donc l'API publique de Twitter) est limité par adresse IP ou par clés d'authentification.

* Script [`add_images_names.py`](add_images_names.py) :
  Script qui m'a permis d'ajouter les noms des images des Tweets déjà stockés dans ma base de données.
  Sauvegardé dans ce GIT car son utilisation de la méthode `statuses_lookup()` de la librairie Tweepy est intéressante.

* Script [`check_tweets_user_ids.py`](check_tweets_user_ids.py) :
  A servi a corriger un bug qui a engendré des problèmes dans la BDD.

* Script [`recalculate_images_features.py`](recalculate_images_features.py) :
  Permet de recalculer tous les vecteurs de caractéristiques des images dans la BDD. **Ne jamais utiliser !** Il vaut mieux vider les tables d'images et de Tweets, et supprimer les curseurs d'indexation. Ca va beaucoup plus vite, car cela utilise le parallélisme du serveur.


## Scripts et fonctionnalités de tests

Ces fonctionnalités n'ont pas étées ajoutées au serveur Artists on Twitter Finder.

* Script [`action_dispatcher.py`](action_dispatcher.py) :
  Fonction permettant d'étaler des actions dans le temps. Pose pleins de problèmes, voir dedans pour des détails.

* Script [`find_histogram_hash.py`](find_histogram_hash.py) :
  Tests statistiques pour chercher une méthode de hash des histogrammes.

* Scripts [`class_Graph_Search.py`](class_Graph_Search.py) et [`build_vectors_graph.py`](build_vectors_graph.py) :
  Permet d'ajouter au serveur la possibilité de faire de la recherche de vecteurs similaires via un arbre. Les vecteurs (C'est à dire les images de Tweets) sont organisées sous la forme d'un arbre, et la recherche le parcours afin de trouver des vecteurs similaires au vecteur de requête. N'a pas été ajouté au serveur car est super lent ! Pour faire ce genre de recherche, il faut rapprocher les données et les algorithmes. Milvus fait ça, lire [`Pistes_explorées_pour_la_recherche.md`](../doc/Pistes_explorées_pour_la_recherche.md) pour plus de détails.
