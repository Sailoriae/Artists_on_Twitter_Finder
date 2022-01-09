# Serveur de mémoire partagée

La mémoire partagée consiste en un objet racine, `Shared_Memory`, et ses sous-objets. Si le serveur est démarré en mode multi-processus (`ENABLE_MULTIPROCESSING` est à `True`), la mémoire partagée est un serveur tournant avec la librairie Python `Pyro4`. Sinon, l'objet racine peut être simplement partagé entre les threads.

Documentation de la librairie Pyro4 : https://pyro4.readthedocs.io/en/stable/index.html

Cette librairie permet de partager des objets entre des processus (Car nous sommes obligés de faire du multi-processus et non du multi-threading à cause du GIL). Elle peut aussi permettre de faire un système distribué. "Artists on Twitter Finder" pourrait donc être distribué sur plusieurs serveurs (En modifiant un peu le code).


## Origine de l'utilisation de Pyro

Le Global Interpreter Lock, ou "GIL", est une sorte de sémaphore qui empêche deux threads Python de s'éxécuter en même temps, afin de ne pas corrompre la mémoire. Ainsi, le multi-threading en Python (Module `threading`) n'est pas du vrai multi-threading, car les instructions Python ne sont pas exécutées en parallèle. Si l'on veut faire du vrai multi-threading en Python, il faut faire du multi-processing (Module `multiprocessing`).

Et faire du multi-processus rend l'utilisation d'une mémoire partagée impossible ! Pour partager des données, il faut obligatoirement faire un serveur de mémoire partagée.

Ainsi, j'ai exploré deux solutions de serveur de mémoire partagée :
- Les "Managers" du module `multiprocessing`. Leur gros problème est qu'ils n'acceptent qu'une liste restreinte d'objets, ce qui transforme complétement la mémoire partagée et leur utilisation.
- La librarie `Pyro4`. Peut supporter des classes, et exécuter coté-serveur le code de leurs attributs, mais pas pour les sous-objets ! Cependant, une parade a été trouvée pour pallier ce problème, et faire une mémoire partagée efficace, voir ci-dessous.


## Procédure de lancement du serveur Pyro : `thread_pyro_server`

Cette procédure est appelée en procédure de création d'un thread par `app.py`. Elle ne peut pas être un sous-processus de la racine, car cela empêche les accès aux données depuis d'autres threads.
Le script `thread_pyro_server.py` peut être éxécuté indépendamment... Mais ça ne sert à rien, sauf à débugger.

En revanche, il peut être intéressant d'accéder à la mémoire partagée afin de débugger le serveur AOTF. Pour se faire, éxécutez le code suivant dans une console Python (IPython par exemple) :
```python
import Pyro4
Pyro4.config.SERIALIZER = "pickle"

e = Pyro4.Proxy( "PYRO:shared_memory@localhost:3300" )
```


## Objets dans la mémoire partagée

L'objet racine de la mémoire partagée est `Shared_Memory`. Lors qu'un objet est créé, sa méthode `register_obj` est appelée afin d'enregistrer le nouvel objet sur le serveur Pyro (Elle ne fait rien si le serveur n'est pas démarré en mode multi-processus). Cela permet de faire des "pseudos-sous-objets".

En effet, Pyro permet d'éxécuter les méthodes des objets sur le serveur, mais pas des sous-objets ! Afin de pallier à ce problème (Et afin d'utiliser des sémaphores, qui se sont pas tranférables car non-sérialisables), on enregistre les URI des enregistrement des objets, et non les objets eux-mêmes. Ainsi, lorsqu'un getter est appelé, il renvoit un objet `Pyro4.Proxy` qui est connecté au sous-objet.

Ainsi, l'utilisation est transparente dans le reste du serveur AOTF !
Autre avantage : Toutes les méthodes de tous les objets présents dans ce module sont exécutées coté serveur Pyro.

**Attention :** Eviter d'ouvrir des proxies en interne de la mémoire partagée ! Garder les objets originaux en attributs privés, afin qu'ils puissent être utilisés en interne comme des objets Pythons normaux. Cela permet de ne pas ouvrir de proxies quand ce n'est pas nécessaire. Une exception peut être faire pour les requêtes, notamment si elle doit être retournée par la fonction.

Arbre des objets :
- `Shared_Memory` : Objet racine.

  - Attribut `user_requests` : URI vers objet `User_Requests_Pipeline` : Mémoire partagée pour les threads de traitement des requêtes des utilisateurs.
    - Liste `requests` (Privé) : Liste d'URI vers objets `User_Request` : Requêtes des utilisateurs.
    - Attribut `requests_sem` (Privé) : URI vers objet `Pyro_Semaphore` : Vérrouillage de la liste précédente. Permet de vérifier qu'une requête n'est pas lancée deux fois.
    - Attributs `*_queue` : URIs vers objets `Pyro_Queue` : 3 files d'attente des différentes threads de traitement (Etapes 1, 2 et 3). Contiennent des URI de la liste `requests`.
    - Attribut `limit_per_ip_addresses` : URI vers objet `HTTP_Requests_Limitator` : Limitateur du nombre de requêtes en cours de traitement par adresse IP.
    - Attribut `thread_step_2_tweets_indexer_sem` : URI vers objet `Pyro_Semaphore` : Verouillage du lancement d'une nouvelle requête de scan dans l'étape de traitement utilisateur numéro 2.

  - Attribut `scan_requests` : URI vers objet `Scan_Requests_Pipeline` : Mémoire partagée pour les threads de traitement des requêtes de scan.
    - Liste `requests` (Privé) : Liste d'URI vers objets `Scan_Request` : Requêtes de scan.
    - Attribut `requests_sem` (Privé) : URI vers objet `Pyro_Semaphore` : Vérrouillage de la liste précédente. Permet de vérifier qu'une requête n'est pas lancée deux fois.
    - Attributs `*_list_account_*_queue` : URIs vers objets `Pyro_Queue` : 4 files d'attente des threads de listage (Etapes A et B, avec une version prioritaire et non-prioritaire pour chaque file). Contiennent des URI de la liste `requests`.
    - Attribut `queues_sem` : URI vers objet `Pyro_Semaphore` : Vérrouillage des 4 files précédentes. Permet de passer une requête non-prioritaire en prioritaire.
    - Attribut `step_C_index_account_tweets_queue` : URIs vers objet `Pyro_Queue` : File d'attente du thread de d'indexation (Etape C). Contient des Tweets représentés par des dictionnaires.
    - Attribut `indexing_ids_dict` (Privé) : Dictionnaire : Contient les Tweets en cours d'indexation dans chaque thread d'indexation (Etape C).
    - Attribut `step_C_sem` : URI vers objet `Pyro_Semaphore` : Vérouillage du dictionnaire précédent. Permet de terminer les requêtes de scan sans oublier un Tweet encore en cours d'indexation.

  - Attribut `http_limitator` : URI vers objet `HTTP_Requests_Limitator` : Limitateur du nombre de requêtes sur l'API HTTP.
  - Attribut `execution_metrics` : URI vers objet `Metrics_Container` : Récépteur et conteneur des temps de calculs des threads de traitement.
  - Attribut `threads_registry` : URI vers objet `Threads_Registry` : Objet auquel les threads / processus s'enregistrent. De plus, les threads de traitement déclarent les requêtes qu'ils sont en train de traiter (En donnent l'URI de la requête concernée).

Voir chaque classe pour plus de documentation.


## Notes

Les objets `Pyro4.Proxy` ferment leur connexion lorsqu'ils arrivent dans le garbadge collector. Source : https://github.com/irmen/Pyro4/blob/79de6434259ff82d202090cbd0901673d4b8344b/src/Pyro4/core.py#L264

Si les paramètres `ENABLE_MULTIPROCESSING` est à `False`, c'est à dire que le serveur ne crée pas de processus fils, le serveur Pyro n'est pas lancé, et la mémoire partagée fonctionne comme un simple objet Python, partagé entre les Threads.

Ainsi, il faut toujours utiliser la fonction `open_proxy()` !
Celle-ci renvoie un `Pyro4.Proxy` si le serveur est démarré en mode multi-processus, ou directement l'objet sinon.
Dans ces deux cas, elle ajoute au proxy ou à l'objet deux méthodes, pour ne pas avoir à utiliser les méthodes et attributs `_pyro*` :
* `get_URI()` : Retourne l'URI du proxy, ou simplement l'objet.
* `release_proxy()` : Ferme le proxy, ou ne fait rien.
