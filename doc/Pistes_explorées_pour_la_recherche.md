# Pistes et idées explorées pour accélérer la recherche par image

## Problème de la recherche par force brute

Il existe pleins de moteurs CBIR, mais je n'en n'ai pas trouvé ayant une recherche efficace lorsque la taille de leur base de données augmente.

Pour rappel, note moteur CBIR, comme la plupart des autres moteurs CBIR, extrait une liste ou un vecteur de caractéristiques. La recherche consiste donc à trouve des vecteurs similaires au vecteur de l'image de requêtes

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

Cependant, cette implémentation sort forcément tous les vecteurs de caractéristiques de la BDD, et donc est forcément ralentit avec de grands jeux de données.


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

Avec l'indexation prenant le moins de RAM, pour 10 000 000 de vecteurs à 240 valeurs, ils recommandent 3 Go de RAM.
- Comparer les ressources recommandées en fonction de la méthode d'indexation : https://www.milvus.io/tools/sizing

On pourrait soit utiliser Milvus, soit créer notre système de graphe de voisinage (Et donc un nouveau algorithme de recherche).

Installation de Milvus sans Docker : https://github.com/milvus-io/milvus/blob/master/INSTALL.md

**Cependant, Milvus risque d'être une surconsommation de mémoire vive pour un gain minime lors d'une recherche sur un artiste.**
