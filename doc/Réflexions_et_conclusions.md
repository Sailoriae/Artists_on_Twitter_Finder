# Réflexions et conclusions

## Légèreté relative du serveur AOTF

Une version alternative d'AOTF aurait eu un Link Finder qui parcours en permanence les sites supportés à la recherche de nouveaux comptes à indexer, et une recherche par image qui se fait directement avec un fichier image, et donc qui se fait dans toutes la base de données. AOTF aurait alors été beaucoup plus proche de ce que SauceNAO fait déjà. De plus, cette version alternative aurait eu besoin d'un moteur de recherche plus avance ou d'un SGDB spécialisé, comme par exemple Milvus. Voir les notes dans [`Pistes_explorées_pour_la_recherche.md`](Pistes_explorées_pour_la_recherche.md).

Cependant, cette version alternative aurait été beaucoup plus gourmandes en ressources, notamment pour la recherche par image. C'est d'ailleurs pour cette raison que AOTF utilise toujours une recherche par force brute, car c'est celle qui nécessite le moins de ressource (Et surtout qui est adapté dans notre cas où on ne recherche que sur certains comptes).

AOTF a été conçu à la base pour être exécuté facilement sur des serveurs modestes (Comme le mien). Il peut même tourner sur un Raspberry Pi (Si on désactive le mode multi-processus).
