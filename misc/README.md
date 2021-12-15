# Artists on Twitter Finder : Divers

## Scripts qui sont utiles

* Script [`get_oauth_token.py`](get_oauth_token.py) :
  Permet d'obtenir les clés d'authentification à un compte Twitter.

* Script [`analyze_results.py`](analyze_results.py) :
  Permet d'analyser les résultats du serveur AOTF.


## Archives et anciennes fonctionnalités

* Module [`old_cbir_engine`](old_cbir_engine) :
  Répertoire de l'ancien moteur de recherche par image. Celui-ci utilisait des histogrammes colorimétriques pour indexer.
  Ce modèle générait ainsi des vecteurs de longueur fixe (240 nombres réels entre 0 et 1). La recherche se faisait alors par des tests de distance dans l'espace vectoriel.
  Il a été remplacé car la recherche menait à beaucoup de faux positifs, et les vecteurs prenaient beaucoup de place dans la base de données.
  Aujourd'hui, le modèle qu'on utilise est pHash, qui génère des empreintes (64 bits).


## Scripts inutiles

* Script [`test_tweepy_rate_limits.py`](test_tweepy_rate_limits.py) :
  Permet de déterminer si Tweepy (Et donc l'API publique de Twitter) est limité par adresse IP ou par clés d'authentification.


## Scripts et fonctionnalités de tests

Ces fonctionnalités n'ont pas étées ajoutées au serveur Artists on Twitter Finder.

* Script [`action_dispatcher.py`](action_dispatcher.py) :
  Fonction permettant d'étaler des actions dans le temps. Pose pleins de problèmes, voir dedans pour des détails.

* Scripts [`class_Graph_Search.py`](class_Graph_Search.py) et [`build_vectors_graph.py`](build_vectors_graph.py) :
  Permet d'ajouter au serveur la possibilité de faire de la recherche de vecteurs similaires via un arbre. On parle de vecteurs et pas d'empreintes, car ils ont étés créés pour l'ancien moteur de recherche par image. Les vecteurs (C'est à dire les images de Tweets) sont organisées sous la forme d'un arbre, et la recherche le parcours afin de trouver des vecteurs similaires au vecteur de requête. N'a pas été ajouté au serveur car est super lent ! Pour faire ce genre de recherche, il faut rapprocher les données et les algorithmes. Milvus fait ça, lire [`Pistes_explorées_pour_la_recherche.md`](../doc/Pistes_explorées_pour_la_recherche.md) pour plus de détails.
