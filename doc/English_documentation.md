# Artists on Twitter Finder (English version)

"Artists on Twitter Finder" (AOTF) is an image search engine (Or "reverse image search"), specialized in illustrations posted by artists on Twitter.

Unlike generalist image search engines, like Google Images or TinEye, this one is very specialized : From an illustration posted on one of the supported websites, it will search if the artist of this illustration has a Twitter account, and, if yes, will search for their Tweets containing this illustration.

In order to be as optimized as possible, this processing is done by a server, found in the [`server`](../server) directory. Thus, it can index accounts and their Tweets in a database in order to be as fast as possible when there is a new request for a Twitter account known by the system.

In order to receive and respond to requests, the server has an HTTP API. The response contains the step of processing the request, and the result if the processing is completed. The documentation for this API is available in english the HTML file [`documentation.en.html`](../public/documentation.en.html).

The HTTP API can be used through a web interface, found in the [`public`](../public) directory. In order for it to be functional, it must be made accessible by an HTTP server, such as Apache. The latter must also proxy to the HTTP API of the AOTF server. A sample Apache configuration is present in the [`configs`](../configs) directory.

Unfortunately, this project was entirely written and documented in French. Maybe there are even more lines of French than code ! The only English documentation you will find is in this file. We recommend using [DeepL.com](https://www.deepl.com/) if you want to explore it beyond this file.


## Example of use

Here is [a fanart of The Owl House](https://www.deviantart.com/namygaga/art/The-Owl-Witch-Academia-7-856041224) (And Little Witch Academia), drawn and published on DeviantArt by NamyGaga. By giving this URL to the AOTF server, it will :
- Search if the artist has one or more Twitter accounts, in our case, she has one: @NamyGaga1,
- Index the Tweets with one or more images in its database,
- Search for the image in the Tweets indexing,
- Return the Tweets containing the image of the request.

In our example, the server found the Tweet [ID 1308936477527756804](https://twitter.com/NamyGaga1/status/1308936477527756804).

Thanks to the HTTP API, sending a request to the server and receiving its response can be done automatically. Thus, "Artists on Twitter Finder" can be very interesting for robots posting illustrations on Twitter, in order to retweet the artist instead of reposting their illustration.


## Currently supported websites

When we talk about a "supported website" by the server, we mean one of the following sites:

* DeviantArt : https://www.deviantart.com/
* Pixiv : https://www.pixiv.net/en/
* Danbooru : https://danbooru.donmai.us/ (Warning, may contain NSFW directly on the home page)
* Derpibooru : https://derpibooru.org/
* Furbooru : https://furbooru.org/


## Directories

* [`server`](../server) : "Artists on Twitter Finder" server. For each query, finds the artists' Twitter accounts, indexes their Tweets, and searches for the query illustration. It contains an API in the form of an HTTP server to receive requests and return their status and results in JSON format.
* [`configs`](../configs) : Apache2 configuration file, to proxy from the outside to the server's HTTP server.
* [`maintenance`](../maintenance) : Maintenance scripts for the server's database.
* [`client`](../client) : Client to the server's API, and sample scripts.
* [`public`](../public) : Web interface to use the server API (In English and French).
* [`doc`](../doc) : Miscellaneous documentation. Note : The code is well documented (But in French), and there are `README.md` files in all directories (Also in French).
* [`backups`](../backups) : Directory to place the database dumps made by the [`mysqldump_backup.py`](../maintenance/mysqldump_backup.py) script.
* [`misc`](../misc) : Backup of various scripts.


## Using AOTF, or installing the server

**If you want to use AOTF without installing it :** You need to find someone who hosts an instance of AOTF and makes it available to everyone. You can then use its web interface, and its HTTP API if you are a developer. You can consult the HTTP API documentation in the HTML file [`documentation.en.html`](../public/documentation.en.html), or directly on the documentation page of the instance's web interface.

**If you want to install your AOTF instance :** The [`server/README.md`](../server/README.md) file documents the installation and use of the AOTF server. Then, if you want to enable the public web interface, see the [`configs/README.md`](../configs/README.md) file. These two documents are written in French, but don't panic, the documentation in English for installing and using the AOTF server is just below.


## Installing the server

0. Clone this repository (`git clone`), this will make it easier to update (`git pull`). The main branch always contains the latest working version.
1. Duplicate the file [`parameters_english.py`](../server/parameters_english.py) to `parameters.py`, and configure it with your API access keys. You will need:
   - One or more Twitter accounts that will be used to index Tweets.
   - A developer Twitter account. To do so, ask for a developer access on the following portal : https://developer.twitter.com
   - And optionally a MySQL server (Otherwise, the server uses SQLite).
2. Install the necessary Python libraries: `pip install -r requirements.txt`

If you are on Windows or MacOS, it is recommended to install the PyReadline library as well: `pip install pyreadline`

To enable the web interface through Apache and/or automatic server startup, see the last two paragraphs of this document.

If you are using MySQL, you can backup the database of the AOTF server automatically (Cron Task) or manually by running the [`mysqldump_backup.py`](../maintenance/mysqldump_backup.py) script. This script creates MySQL dumps that are placed in the [`../backups`](../backups) directory. The AOTF server does not need to be shut down. For more information, see the file [`Stratégie_de_sauvegarde.md`](../doc/Stratégie_de_sauvegarde.md), but it's written in french. Just remember that the `--hex-blob` and `--single-transaction` options are mandatory in your dump command (`mysqldump`).


## Using the server

1. If you are SSH connected on a server, first create a screen : `screen -S twitter`
2. Run the server : `python3 app.py`

This starts the server and puts you on the command line (Which is entirely in French). If you want to quit the screen and leave the server running, do `Ctrl + A + D`.

To stop the server, you can either run the `stop` command on its command line, or send it a `SIGTERM` signal.
If it uses a MySQL database, you can also kill it with `Ctrl + C` or a `SIGKILL` signal. This is not a problem for data consistency.

During server execution (Outside the startup and shutdown phases), the following commands are available :
* `query [URL of the illustration]` : Run a query and see its status. This command must be run again to get the status and results of the query. This command works similarly to the `/query` endpoint in the HTTP API.
* `scan [Name of the account to be scanned]` : Index or update the indexing of Tweets from a Twitter account.
* `search [Image file URL] [Optional: Twitter account name to search]` : Search for an image in the entire database, or on a particular account. Allows more flexible use of the server. As with the `query` command, you have to run the command again to get the status and results of the search.
* `stats` : Display database statistics.
* `threads` : Display threads and what they are doing.
* `queues` : Show the size of the queues.
* `metrics` : Show execution time measurements. The `ENABLE_METRICS` parameter must be set to `True` to allow the server to measure execution times. These measurements have been placed at specific points in the request processing.
* `stacks` : Write the thread call stacks to a `stacktrace.log` file. If a thread is stuck, this command is very useful to understand where it is stuck, and thus debug.
* `stop` : Stop the server.
* `help` : Display the help (But in French).


## Apache2 virtual host

The `apache2_example.conf` file is an example configuration file for creating a virtual host in the Apache2 HTTP Server.

If you want to use it, duplicate it to `apache2.conf` to change the following values :
* `PATH_TO_AOTF`: Path to your AOTF installation.
* `AOTF_DOMAIN` : Domain name used.

Then activate this Apache2 virtual host :
```
sudo ln -s /path/to/Artists_on_Twitter_Finder/configs/apache.conf /etc/apache2/sites-enabled/sub.domain.tld.conf
```

Enable the necessary Apache2 modules:
```
sudo a2enmod proxy
sudo a2enmod proxy_http
```

And restart the Apache2 server:
```
sudo service apache2 restart
```

You can also optionally enable HTTPS by obtaining a certificate from Let's Encrypt:
```
sudo a2dismod ssl
sudo service apache2 restart
sudo letsencrypt certonly --apache -d sub.domain.tld
sudo a2enmod ssl
sudo service apache2 restart
```


## Automatic startup

If you want AOTF to start automatically when your server starts, edit the contab of the user you installed it with (`sudo crontab -e -u user`) and add the following line:
```
@reboot screen -dmS twitter python3 /path/to/Artists_on_Twitter_Finder/server/app.py
```

The stopping of the server will be done cleanly during the shutdown because the AOTF server handles the `SIGTERM` and `SIGHUP` signals
