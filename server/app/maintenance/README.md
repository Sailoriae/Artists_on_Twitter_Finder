# Procédures des threads de maintenance

- `thread_auto_update_accounts` : Thread de mise à jour automatique des comptes dans la base de données.
- `thread_remove_finished_requests` : Thread de délestage des requêtes terminées. Les requêtes utilisateurs sont conservées 3h (Ou 1h si elle s'est terminée en erreur, ou 10mins si elle s'est terminée en erreur d'entrée utilisateur), et les requêtes de scan 24h.
- `thread_reset_SearchAPI_cursors` : Thread de suppression des curseurs d'indexation avec l'API de recherche, car l'indexation sur le moteur de recherche de Twitter est très fluctuante.

- `thread_retry_failed_tweets` : Considéré comme un thread de maintenance, mais il est placé dans le répertoire [`scan_pipeline`](../scan_pipeline).
