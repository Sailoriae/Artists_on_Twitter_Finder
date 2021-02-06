# Artists on Twitter Finder : Scripts de maintenance

* Script [`remove_deleted_accounts.py`](remove_deleted_accounts.py) :
  Permet de supprimer les comptes de la base de données qui n'existent plus sur Twitter. Supprime aussi leurs Tweets.
  **Attention :** Ce script supprime les comptes supprimés, suspendus ou passés en privé / protégé.

* Script [`cleanup_database.py`](cleanup_database.py) :
  Permet de vérifier que les Tweets enregistrés dans la base de données ont bien un compte enregistré correspondant, et que les images de Tweets enregistrées ont bien un Tweet enregistré correspondant.
  Puis supprime les Tweets sans compte enregistré, et les images de Tweets sans Tweet enregistré.
