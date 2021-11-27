# Artists on Twitter Finder : Configurations

## `apache2_example.conf` : Hôte virtuel Apache2

Ce fichier est à modifier ! Remplacez :
* `/path/to/Artists_on_Twitter_Finder/public` par le chemin vers le répetoire `public` de "Artists on Twitter Finder",
* Et `sub.domain.tld` par le nom de domaine utilisé.

Activer cet hôte virtuel Apache2 :
```
sudo ln -s /path/to/Artists_on_Twitter_Finder/configs/apache.conf /etc/apache2/sites-enabled/sub.domain.tld.conf
```

Activer les modules Apache2 nécessaires :
```
sudo a2enmod proxy
sudo a2enmod proxy_http
```

Et relancer le serveur Apache2 :
```
sudo service apache2 restart
```

### Optionnel : HTTPS

```
sudo a2dismod ssl
sudo service apache2 restart
sudo letsencrypt certonly --apache -d sub.domain.tld
sudo a2enmod ssl
sudo service apache2 restart
```

## `artist-on-twitter_example.service` : Service

Ce fichier est à modifier ! Remplacez :
* `/path/to/Artists_on_Twitter_Finder/server` par le chemin vers le répetoire `server` de "Artists on Twitter Finder",
* Et `username` par le nom d'utilisateur qui aura le processus.

Par mesure de sécurité, on crée un lien physique vers le fichier de configuration du service, et on en donne la propriété à `root:root`.
```
sudo ln /path/to/Artists_on_Twitter_Finder/configs/artist-on-twitter.service /etc/systemd/system/artist-on-twitter.service
sudo chown root:root /etc/systemd/system/artist-on-twitter.service
```

Puis activez ce service, et démarrez-le :
```
sudo systemctl enable /path/to/Artists_on_Twitter_Finder/configs/artist-on-twitter.service
```
