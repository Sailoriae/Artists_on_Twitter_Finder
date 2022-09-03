#!/usr/bin/python3
# coding: utf-8

"""
Enable multi-processing mode.

If this setting is enabled, many child processes will be created, as well as a
shared memory server based on the Pyro library. This will make the server
heavier, but the processing of requests will be much more efficient.

If this parameter is disabled, only threads will be created, and the shared
memory will simply be a Python object. The server will therefore be lighter,
but the processing of queries will be slower, because Python threads do not run
in parallel (See the GIL doc).

WARNING ! SQLite blocks the DB when writing ! Do not activate this parameter if
you use SQLite !
"""
ENABLE_MULTIPROCESSING = True

"""
Pair of keys to access the Twitter API. To get a pair of API_KEYS and
API_SECRET keys, you have to create an "application" on the Twitter interface
for developers: https://developer.twitter.com/en/apps

It is highly recommended to set this Twitter app to read-only access.
"""
API_KEY = ""
API_SECRET = ""

"""
Pair of access keys to the default Twitter account.
This account is used by :
- The command line interface
- The automatic update thread
- The reset thread of the indexing cursors with the search API
- The retry thread for indexing Tweets (Only if a Tweet ID has been manually
  inserted in the database)
- Some Link Finder threads (Step 1)
- Some image search threads (Step 3)
- The maintenance script to de-index deleted accounts

To get OAUTH_TOKEN and OAUTH_TOKEN_SECRET key pairs, you can use the
"get_oauth_token.py" script located in the "misc" directory. You will need the
API_KEY and API_SECRET key pair above.
"""
OAUTH_TOKEN = ""
OAUTH_TOKEN_SECRET = ""

"""
List of access key pairs to Twitter accounts.
This allows to parallelize the processing, and thus to improve the server
performance. These accounts are used for :
- Link Finder threads (Step 1)
- Image search threads (Step 3)
- Listing threads with the Search API (Step A)
- Listing threads with the Timeline API (Step B)

These key pairs are associated with a third key AUTH_TOKEN, allowing access to
the same Twitter accounts, but via the Search API (Step A). To obtain these
keys, you must :
1. Open a Twitter account in a browser,
2. Copy the value of the "auth_token" cookie here,
3. And don't disconnect this account, nor delete the session !
   Delete the browser cookies instead.

THE AUTH_TOKEN MUST MATCH THE OAUTH_TOKEN/OAUTH_TOKEN_SECRET PAIRS.
This is super mega important ! Otherwise the verification of blocking by an
account when indexing it with the search API might be wrong, and the account
wrongly indexed.

These used accounts must be able to see sensitive media in
searches! To do so, you must :
- Check the box "Show media with potentially sensitive content" in
  "Settings" -> "Privacy and security" -> "Content you see".
- Uncheck the box "Hide offensive content" in "Settings" ->
  "Privacy & Security" -> "Content you see" -> "Search settings"

It is highly recommended to use "useless" accounts here, in case of server
hacking (And stealing "auth_token" below).

The more keys you put here, the more threads the server will have (And child
processes if multi-processing mode is enabled). It is useless to put more
accounts than you have cores in your CPU.
"""
TWITTER_API_KEYS = [ {
                       "OAUTH_TOKEN" : "",
                       "OAUTH_TOKEN_SECRET" : "",
                       "AUTH_TOKEN" : ""
                      }, {
                       "OAUTH_TOKEN" : "",
                       "OAUTH_TOKEN_SECRET" : "",
                       "AUTH_TOKEN" : ""
                      }, {
                       "OAUTH_TOKEN" : "",
                       "OAUTH_TOKEN_SECRET" : "",
                       "AUTH_TOKEN" : ""
                      } ]

"""
Settings for using SQLite.
"""
SQLITE_DATABASE_NAME = "SQLite_Database.db"

"""
Settings for using MySQL.
"""
USE_MYSQL_INSTEAD_OF_SQLITE = False
MYSQL_ADDRESS = "localhost"
MYSQL_PORT = 3306
MYSQL_USERNAME = ""
MYSQL_PASSWORD = ""
MYSQL_DATABASE_NAME = ""

"""
HTTP server port.
DO NOT OPEN TO PUBLIC ! Use a real web server like Apache2 or Nginx to proxy to
the AOTF server.
"""
HTTP_SERVER_PORT = 3301

"""
Do more print().
Also enables writes to the "debug.log" file. This allows to have debug
information that cannot be seen in the terminal.
"""
DEBUG = False

"""
Enable the measurement of execution times for long procedures.
The averages are then accessible via the "metrics" command.
"""
ENABLE_METRICS = True

"""
Automatic update of accounts in the database.
Number of days without scanning the Twitter account to update it automatically.

Warning : In order to spread the updates over time, the automatic update system
can go ahead and launch the update of an account before this number of days has
elapsed.
"""
DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE = 30 # days

"""
Period in days to reset the indexing cursors with the search API.
Indeed : Twitter's search engine fluctuates, and is fairly poorly documented.
Some Tweets can be de-indexed or re-indexed.
It is therefore interesting from time to time to reset the indexing cursor with
the search API for each account.
This does not delete or re-index any Tweet in the database! We just add some.
So the speed depends mainly on the listing thread.

Warning: As for the automatic update, the reset system of the cursors can
launch an indexing in advance, in order to spread them in time.
"""
RESET_SEARCHAPI_CURSORS_PERIOD = 365 # days

"""
Limit the number of requests (Through the HTTP API) per IP address.
"""
MAX_PROCESSING_REQUESTS_PER_IP_ADDRESS = 10

"""
List of IP addresses not subject to limitation.
"""
UNLIMITED_IP_ADDRESSES = [ "127.0.0.1" ]

"""
Activate the logging of the results.
The results are then written in the "results.log" file. Each result is in JSON
format, one JSON per line because one line per result.
The JSON is identical to the one returned by the API.
Attention! The results are only logged if there was no problem or error.
"""
ENABLE_LOGGING = False

"""
This file contains access keys to the Twitter API. For security reasons, we
remove its access by anyone. This line is the equivalent of the "chmod o-rwx"
command.
If you want, you can customize or remove this behavior.
"""
from os import chmod, lstat
from stat import S_IRWXO
chmod(__file__, lstat(__file__).st_mode & ~S_IRWXO)
