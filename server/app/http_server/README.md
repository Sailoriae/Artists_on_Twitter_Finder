# Module de la procédure des threads du serveur HTTP

- `class_HTTP_Server` : Classe du serveur HTTP. Le serveur HTTP intégré contient uniquement l'API. L'interface web dans le répertoire [`public`](../../../public) permet d'utiliser graphiquement le serveur AOTF.
- `thread_http_server` : Thread de serveur HTTP. Lance le serveur HTTP en mode multi-threads. Chaque requête HTTP mène à la création d'un thread pour y répondre.

La documentation de l'utilisation l'API HTTP est disponible dans le fichier [`API_HTTP.md`](../../../doc/API_HTTP.md).
