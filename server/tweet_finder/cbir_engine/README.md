# Module du moteur CBIR

L'objet `CBIR_Engine` est un moteur de recherche par image, qui utilise l'algorithme **pHash** pour indexer et comparer les images. pHash est un algorithme d'empreinte d'image ("image hashing"), qui permet d'extraire une liste de bits à partir de n'importe quelle image. La recherche se fait alors par comparaison bits à bits entre l'empreinte de l'image de requête, et les empreintes des images stockées dans la base de données.

On a choisi pHash car il est celui qui a le moins de collisions, et donc le moins de faux-positifs ou faux-négatifs. De plus, par rapport à dHash, il supporte beaucoup mieux la compression des images par Twitter. Son inconvénient par rapport à dHash est qu'il est légèrement plus lent.

Source : http://www.hackerfactor.com/blog/?/archives/529-Kind-of-Like-That.html

L'ancien moteur de recherche par image d'AOTF extrayait des images une liste de caractéristiques, ou "features list", de longueur fixe, qui s'assimile à un vecteur dans un espace vectoriel. La recherche se faisait alors par recherche du plus proche vecteur. Ce moteur est présent dans le répertoire [`old_cbir_engine`](../../../misc/old_cbir_engine).


## Utilisation indépendante de ce module

Il est possible d'utiliser ce module indépendamment du reste du projet. **Attention : Ce module ne gère pas de base de données !**


### Importation et initialisation

Il faut d'abord importer l'objet `CBIR_Engine` de ce module, puis l'initialiser :
```python
from cbir_engine import CBIR_Engine

engine = CBIR_Engine()
```

### Format des images

Ce module analyse des images représentés par des objets `PIL.Image`.

Le module `utils` contient la fonction `url_to_PIL_image()` permettant d'importer n'importe quelle image depuis le web et de la convertir dans ce format.


### Indexation (Calcul des empreintes)

Pour obtenir l'empreinte d'une image :

```python
engine.index_cbir( image )
```

Avec `image` l'image à indexer, sous la forme d'un objet `PIL.Image`.


### Recherche par image

Pour chercher une image à partir d'une autre :

```python
engine.index_cbir( image, images_iterator )
```

Avec :
* `image` l'image de requête, sous la forme d'un objet `PIL.Image``,
* Et `images_iterator` un itérateur sur la base de données des images indexées. Cet itérateur doit renvoyer des objets représentants les images indexés. Ces objets doivent contenir obligatoirement les deux attributs suivants :
  - `image_hash` : L'empreinte de l'image, au même format que la fonction `index_cbir()` a renvoyé,
  - Et `distance` : Un attribut servant au moteur CBIR à stocker le nombre de bits de différence entre l'empreinte de cette image, et l'empreinte de l'image de requête.

Cette fonction retourne alors une liste contenant les objets de l'itérateurs qui ont étés sélectionnés comme images identiques à l'image de requêtes. Cette liste peut être vide.

Les images indexées sont représentées par des dictionnaires (Parce que c'est plus simple à faire passer dans Pyro).
Ces dictionnaires continenent les champs suivants :
- `account_id` : ID du compte Twitter ayant tweeté l'image,
- `tweet_id` : ID du Tweet contenant l'image,
- `image_name` : Nom de l'image, permettant de la retrouver en un GET HTTP,
- `image_hash` : Empreinte de l'image,
- `image_position` : La position de l'image (1-4) dans le Tweet (Car un tweet peut contenir au maximum 4 images),
- `images_count` : Le nombre d'images dans le Tweet (1-4).
- `distance` : La distance entre cette image et celle de requête (`None` par  défaut).

L'itérateur est la méthode `get_images_in_db_iterator()` de la classe `SQLite_or_MySQL`.
