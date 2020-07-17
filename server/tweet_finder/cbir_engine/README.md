# Module Moteur CBIR

Il n'existe pas de librairie pour faire du Content-Based Image Retrieval (CBIR) en Python. J'ai donc été obligé de faire mon propre système, en utilisant de préférence OpenCV afin qu'il aille plus vite.

Comme le but de ce projet est plus grand que le moteur de CBIR, je me suis basé sur l'article "The complete guide to building an image search engine with Python and OpenCV", écrit par Adrian Rosebrock, et présenté sur le site www.pyimagesearch.com. Une partie des codes de cet article sont réutilisés ici, notamment l'objet ColorDescriptor qui est presque entièrement tiré de cet article.

https://www.pyimagesearch.com/2014/12/01/complete-guide-building-image-search-engine-python-opencv/


## Utilisation indépendante de ce module

Il est possible d'utiliser ce module indépendemment du reste du projet.

**Attention : Ce module ne gère pas de base de données !**
C'est la classe `CBIR_Engine_with_Database` qui fait le lien entre le moteur CBIR et la base de données.

### Importation et initialisation

Il faut d'abord importer l'objet `CBIR_Engine` de ce module, puis l'initialiser :
```
from cbir_engine import CBIR_Engine

engine = CBIR_Engine()
```

### Format des images

Ce module analyse des images représentés par des objets `numpy.ndarray`.

Le module `utils` contient la fonction `url_to_cv2_image` permettant d'importer n'importe quelle image depuis le web et de la convertir dans ce format.

### Indexation

Pour obtenir la liste des caractéristiques d'une image :
```
engine.index_cbir( image )
```
Avec `image` l'image à indexer, sous la forme d'un objet `numpy.ndarray`.

Cette fonction retourne alors une liste de réels.

### Recherche d'image inversé

Pour chercher une image à partir d'une autre :
```
engine.index_cbir( image, images_iterator )
```
Avec :
* `image` l'image de requête, sous la forme d'un objet `numpy.ndarray`,
* Et `images_iterator` un itérateur sur la base de données d'images indexées. Cet itérateur doit renvoyer des objets représentants les images indexés. Ces objets doivent contenir les deux attributs suivants :
  - `image_features` : La liste des caractéristiques de l'image, sous la forme d'une liste de réels,
  - `identifier` : Un identifiant unique à cette image, qui sera retourné si ses caractéristiques correspondent à l'image de requête.

Cette fonction retourne alors une liste d'identifiants d'images.

C'est la classe `Image_in_DB` du module `database` qui représente une image indexée.
De plus, il y a dans ce module `database` un exemple d'itérateur.
