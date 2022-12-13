# Configurations externes pour le serveur AOTF

## Hôte virtuel Apache2

Le fichier `apache2_example.conf` est un exemple de fichier de configuration pour créer un hôte virtuel dans le serveur HTTP Apache2.

Si vous souhaitez l'utilisez, dupliquez-le vers `apache2.conf` pour y modifier les valeurs suivantes :
* `PATH_TO_AOTF` : Chemin vers votre installation d'AOTF.
* `AOTF_DOMAIN` : Nom de domaine utilisé.

Puis activez cet hôte virtuel Apache2 :
```
sudo ln -s /path/to/Artists_on_Twitter_Finder/configs/apache.conf /etc/apache2/sites-enabled/sub.domain.tld.conf
```

Activez les modules Apache2 nécessaires :
```
sudo a2enmod proxy
sudo a2enmod proxy_http
```

Et relancez le serveur Apache2 :
```
sudo service apache2 restart
```

Vous pouvez aussi optionnellement activer HTTPS en obtenant un certificat auprès de Let's Encrypt :
```
sudo a2dismod ssl
sudo service apache2 restart
sudo letsencrypt certonly --apache -d sub.domain.tld
sudo a2enmod ssl
sudo service apache2 restart
```

## Service Systemd

Le fichier `artist-on-twitter_example.service` est un exemple de fichier de configuration pour créer un service via Systemd.

Si vous souhaitez l'utilisez, dupliquez-le vers `artist-on-twitter.service` pour y modifier les valeurs suivantes :
* `/path/to/Artists_on_Twitter_Finder/server` par le chemin vers le répertoire `server` de "Artists on Twitter Finder",
* Et `username` par le nom d'utilisateur qui aura le processus.

Par mesure de sécurité, on crée un lien physique vers le fichier de configuration du service, et on en donne la propriété à `root:root`.
```
sudo ln /path/to/Artists_on_Twitter_Finder/configs/artist-on-twitter.service /etc/systemd/system/artist-on-twitter.service
sudo chown root:root /etc/systemd/system/artist-on-twitter.service
```

Puis activez ce service, et démarrez-le :
```
sudo systemctl enable artist-on-twitter.service
```

## Alternative au service

Si vous ne souhaitez pas créer un service, vous pouvez simplement ajouter le AOTF au démarrage via la table Cron de l'utilisateur que vous souhaitez utiliser.
Pour se faire, éditez la table de cet utilisateur (`sudo crontab -e -u utilisateur`) et ajoutez-y la ligne suivante :
```
@reboot screen -dmS twitter python3 /path/to/Artists_on_Twitter_Finder/server/app.py
```

L'arrêt du serveur se fera proprement lors du shutdown car le serveur AOTF gère les signaux `SIGTERM` et `SIGHUP`. Vous pouvez vérifier la bonne extinction du serveur via le fichier `debug.log`, ce qui nécessite l'activation du paramètre `DEBUG` dans votre fichier `parameters.py`. Si le message `Arrêt terminé.` y a été écrit, c'est que le serveur AOTF s'est bien arrêté proprement.

Cependant, **cette méthode n'est pas recommandée si vous utilisez un serveur MySQL**, car ce dernier sera éteint avant AOTF lors du shutdown, ce qui n'est pas propre (Même si ça ne pose pas de problème pour les données).