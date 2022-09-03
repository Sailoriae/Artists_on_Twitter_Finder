# Index de la documentation d'AOTF

Veuillez d'abord lire la description générale de AOTF, c'est à dire le fichier [`../README.md`](../README.md).

* [`API_HTTP.md`](API_HTTP.md) : Documentation de l'API HTTP du serveur AOTF.
* [`Architecture_du_serveur.png`](Architecture_du_serveur.png) : Diagramme de l'architecture du serveur à l'exécution.
* [`Stratégie_de_sauvegarde.md`](Stratégie_de_sauvegarde.md) : Idées pour sauvegarder la base de données MySQL du serveur AOTF.
* [`Réflexions_et_conclusions.md`](Réflexions_et_conclusions.md) : Réflexions et conclusions sur ce projet.

La documentation n'est pas seulement ici ! Il y a des fichiers `README.md` dans presque tous les répertoires de ce projet. Les plus intéressants pour compléter cette documentation sont les suivants :

* [`../server/README.md`](../server/README.md) : Instructions d'installation et d'utilisation du serveur, liste de ses fonctionnalités et description de son architecture.
* [`../server/tweet_finder/cbir_engine/README.md`](../server/tweet_finder/cbir_engine/README.md) : Fonctionnement du moteur de recherche par image.

Ce répertoire contient aussi des fichiers de documentation moins importants :

* [`Avertissement_utilisation.md`](Avertissement_utilisation.md) : Avertissement sur l'indexation de comptes Twitter dans la base de données.
* [`Limites_de_scan_des_comptes_Twitter.md`](Limites_de_scan_des_comptes_Twitter.md) : Pourquoi il peut manquer des Tweets des comptes Twitter scannés.
* [`Pistes_explorées_pour_la_recherche.md`](Pistes_explorées_pour_la_recherche.md) : Pistes et idées explorées pour accélérer la recherche par image (LIRE et Milvus). Attention, ce document date de l'ère de l'ancien moteur de recherche par image (Voir [`old_cbir_engine`](../misc/old_cbir_engine)), remplacé le 26 septembre 2021. Il n'est donc plus à jour.
* [`English_documentation.md`](English_documentation.md) : Introduction et documentation simplifiée du projet en anglais. Ce fichier réuni le [`README.md`](../README.md) racine, et une partie du [`README.md`](../server/README.md) du serveur. Il ne doit pas contenir de documentation plus technique que l'utilisation du serveur !
