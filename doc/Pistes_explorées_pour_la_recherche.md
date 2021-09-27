# Pistes et idées explorées pour accélérer la recherche par image

## Problème de la recherche par force brute

Il existe pleins de moteurs CBIR, mais je n'en n'ai pas trouvé ayant une recherche efficace lorsque la taille de leur base de données augmente.

Pour rappel, note moteur CBIR, comme la plupart des autres moteurs CBIR, extrait une liste ou un vecteur de caractéristiques. La recherche consiste donc à trouve des vecteurs similaires au vecteur de l'image de requêtes.

La première implémentation de cette recherche consiste à calculer la distance entre le vecteur de requête, et tous les autres de la base de données, et de prendre les plus proches. On pourrait appeler cela de la recherche par force brute, c'est à dire tout tester.

Le problème est que cette méthode devient lente lorsque la BDD grandie. Il faut donc soit :
- Faire le plus d'opérations de pré-filtrage dans la BDD. En effet, les opérations dans la BDD sont les plus rapides, car au plus proche des données.
- Organiser les vecteurs stockés de manière à accélérer le pré-filtrage. Cela peut être un graphe.
- Une combinaison de ces deux méthodes.

Cependant, cette amélioration n'est pas primordiale pour AOTF. En effet, la recherche ne se fait que sur certains comptes Twitter. Au maximum, le nombre de comparaisons est de l'ordre de 10 000.


## Utiliser LIRE (Lucene Image Retrieval)

LIRE est une librairie écrite en Java permettant d'extraire les caractéristiques d'images. C'est donc l'équivalent de notre module `cbir_engine`, mais en beaucoup plus poussé.

Github de cette librairie : https://github.com/dermotte/lire

Cependant, le problème de cette librairie est qu'elle ne contient pas le rangement de données (C'es à dire comment on organise la base de données, et donc comment on recherche).

Or, pour accélérer notre moteur CBIR, il faut faire le plus d'opérations possibles dans la base de données (C'est à dire au plus proche des données), afin de pré-filtrer les images indexées pour sortir le moins de données possibles.

Il existe cependant un projet regroupant LIRE et le SGDB Solr : https://github.com/dermotte/liresolr

C'est ce projet qui est utilisée (Sous forme modifiée) pour Trace.Moe : https://github.com/soruly/trace.moe

LIRE intégré dans Solr semble être une solution intéressante, car le moteur CBIR est dans le SGDB, donc ça rapproche les données du code. De plus, Trace.Moe a un gigantesque jeu de données, et fonctionne très bien, preuve que ce système est intéressant.

Son défaut est qu'il est complexe à mettre en oeuvre.

Note : Trace.Moe utilise l'algorithme de hashing ColorLayout (Implémenté dans LIRE, vient de MPEG-7). Au passage, les algo de hashing pourraient être une solution intéressante... A étudier !


## Utiliser Milvus

Milvus est un SGDB spécialisé dans les vecteurs, donc exactement les données que l'on stocke. L'opération de recherche (C'est à dire chercher des vecteurs similaires au vecteur de requête) se fait directement dans le SGDB, ce qui garantie de bonnes performances.

Github de ce SGDB : https://github.com/milvus-io/milvus

Cependant, Milvus calcul la distance de chaque vecteur dans la BDD avec le vecteur de requête. Sa vitesse repose sur une forte utilisation de la mémoire vive, et est fortement accéléré par l'utilisation de GPU. Il nécéssite donc un serveur plus puissant si la base de données est grande.

Milvus semble être intéressant pour un projet ayant de grosses ressources physiques (GPU et RAM), ce qui n'est pas le cas de mon petit serveur que j'utilise actuellement pour AOTF.

Les équipes de Milvus ont développé plusieurs cas d'utilisation de leur logiciel : https://github.com/milvus-io/bootcamp/tree/master/EN_solutions

Notemment un moteur de recherche par image, utilisant VGG pour extraire les caractéristiques des images.
- Github de ce moteur CBIR : https://github.com/zilliz-bootcamp/image_search
- Article expliquant son fonctionnement : https://medium.com/unstructured-data-service/milvus-application-1-building-a-reverse-image-search-system-based-on-milvus-and-vgg-aed4788dd1ea
- Autre article, plus détaillé sur la configuration : https://medium.com/unstructured-data-service/the-journey-to-optimizing-billion-scale-image-search-2-2-572a36d5d0d
- Explication de l'implémentation de VGG utilisée : https://keras.io/api/applications/vgg/

Chose très intéressante : Milvus organise les vecteurs stockés par proximité (ANN = Approximate Nearest Neighbor), ce qui permet de grandement accélérer la recherche !
- Source : https://medium.com/unstructured-data-service/milvus-was-built-for-massive-scale-think-trillion-vector-similarity-search-aec846038624#5d14
- Plusieurs méthodes d'indexation sont proposées : https://milvus.io/docs/v0.11.0/index.md#CPU

Avec l'indexation prenant le moins de RAM, pour 10 000 000 de vecteurs à 240 valeurs, ils recommandent 3 Go de RAM. Cependant, on a besoin d'un résultat le plus juste possible ("recall rate"). Ainsi, la méthode d'indexation `IVF_FLAT` est la plus adaptée à notre besoin. Le problème est que pour le même nombre de vecteurs de même taille, ils recommandent 9 Go de RAM.
- Comparer les ressources recommandées en fonction de la méthode d'indexation : https://www.milvus.io/tools/sizing
- "recall rate" = "la proportion des items pertinents proposés parmi l'ensemble des items pertinents", source : https://fr.wikipedia.org/wiki/Pr%C3%A9cision_et_rappel

On pourrait soit utiliser Milvus, soit créer notre système de graphe de voisinage (Et donc un nouveau algorithme de recherche).
Cependant, on a testé notre propre système, mais il est super lent ! Voir [`class_Graph_Search.py`](../misc/class_Graph_Search.py) pour notre implémentation.

Installation de Milvus sans Docker : https://github.com/milvus-io/milvus/blob/master/INSTALL.md

**Cependant, Milvus risque d'être une surconsommation de mémoire vive pour un gain minime lors d'une recherche sur un artiste.**


## Comparaison de modèles et de libraries ANN

Autre article intéressant sur la construction d'un moteur de recherche par image : https://www.oreilly.com/library/view/practical-deep-learning/9781492034858/ch04.html

Notamment le paragraphe "Length of Feature Vectors" qui compare certains modèles de Keras. VGG16 est celui qui sort les vecteurs de plus petite taille (512 valeurs, contre 2048 pour ResNet-50). Cependant, l'article propose de "compresser" ces 2048 valeurs en 100 (Voir le paragraphe "Reducing Feature-Length with PCA"). Cependant, cette méthode n'est pas adapté à notre utilisation, car elle nécessite l'ensemble des vecteurs pour pouvoir les réduires sur les valeurs qui les différencient.

Il compare aussi des librairies ANN = Approximate Nearest Neighbors (Annoy, NGT, FAISS...). Attention : Ce sont des librairies, pas des serveurs comme Milvus.

Les codes sources sont disponibles ici : https://github.com/PracticalDL/Practical-Deep-Learning-Book/tree/master/code/chapter-4

Autre comparaison des performances des librairies ANN : http://ann-benchmarks.com

**Conclusion : Milvus est plus adapté à notre cas**, pour le parallélisme, à moins qu'on crée un thread qui gére la BDD via une librairie (Par exemple NGT). Et VGG16 aussi semble pas mal : Petits vecteurs, vitesse raisonnable, et "Top-1% accuracy" par trop mal (Même si ce n'est pas le meilleur).


## PyTables

PyTables, reposant sur la librairie HDF5, est une librairie de stockage de données dans SGDB, directement dans des fichiers. Cela permettrait de stocker les vecteurs de chaque compte Twitter dans un fichier séparé. On peut même aller plus loin et complétement réécrire la classe `SQLite_or_MySQL` pour ne pas utiliser du tout de SQL.

Enorme intéret : Permet d'être indépendant, et de garder AOTF simple !
Si on l'implémente, comparer ses performances avec notre MySQL actuel !
Documentation : http://www.pytables.org/index.html

Attention cependant au parallélisme : *Unlike most RDBMs, PyTables is not intended to serve concurrent accesses to a database. It has no protections whatsoever against corruption for different (or even the same) programs accessing the same database. Opening several handles to the same database in read-only mode is safe, though.*

Question que je me suis posée : Est-ce que ça ne serait pas mieux d'utiliser une librairie ANN, comme Annoy ou NMSLIB par exemple (Recommandés dans l'article ci-dessus comme des libraires simples à utiliser). Parce que ces librairies reposent aussi sur HDF5, mais elles ont en plus le moteur intégré.
Réponse : Le problèmes de ces libs, c'est que c'est compliqué d'ajouter de nouveaux vecteurs une fois le graphe de voisinage construit.
