# Artist on Twitter Finder : Configurations

## `apache2_example.conf` : Hôte virtuel Apache2

Ce fichier est à modifier ! Remplacez :
* `/path/to/Artist_on_Twitter_Finder/public` par le chemin vers le répetoire `public` de "Artist on Twitter Finder",
* Et `sub.domain.tld` par le nom de domaine utilisé.

Activer cet hôte virtuel Apache2 :
```
sudo ln -s /path/to/Artist_on_Twitter_Finder/configs/apache.conf /etc/apache2/sites-enabled/sub.domain.tld.conf
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
sudo letsencrypt certonly --webroot -w /path/to/Artist_on_Twitter_Finder/public -d sub.domain.tld --email name@domain.tld --text --rsa-key-size 4096
sudo a2enmod ssl
sudo service apache2 restart
```

## `artist-on-twitter_example.service` : Service

Ce fichier est à modifier ! Remplacez :
* `/path/to/Artist_on_Twitter_Finder/server` par le chemin vers le répetoire `server` de "Artist on Twitter Finder",
* Et `username` par le nom d'utilisateur qui aura le processus.

Puis activez ce service, et démarrez-le :
```
sudo systemctl enable /path/to/Artist_on_Twitter_Finder/configs/artist-on-twitter.service
```
