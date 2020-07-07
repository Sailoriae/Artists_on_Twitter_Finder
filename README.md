# Artist on Twitter Finder

Ce projet comporte plusieurs modules qui peuvent être utilisés indépendamments :
* `cbir_engine` : Moteur de recherche d'image par le contenu ("Content-Based Image Retrieval", CBIR), mais ne gère pas de base de données. Ce moteur est généraliste, il peut donc être réutilisé dans un autre projet, à condition de réécrire un accès à une base de données et l'itération sur cette base (Pour la recherche).
* `database` : Couche d'abstraction à l'utilisation de la base de données. Cette couche est spécialisée pour notre projet.
* `link_finder` : Moteur de recherche de comptes Twitter d'un artiste à partir d'une illustration postée sur un des sites supportés.
* `twitter` : Couche d'abstraction à l'utilisation de l'API Twitter via la librairie Python Tweepy. Est spécialisé, contient uniquement les fonctions dont nous avons besoin.
* `utils` : Divers fonctions utiles.

La classe `CBIR_Engine_with_Database` fait le lien entre le moteur CBIR et la base de données, mais est spécialisé pour les images dans des Tweets.
