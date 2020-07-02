class TweetCriteria:
    """Search parameters class"""

    def __init__(self):
        self.maxTweets = 0
        self.topTweets = False
        self.within = "15mi"
        self.emoji = "ignore"

    def setUsername(self, username):
        """Set username(s) of tweets author(s)
        Parameters
        ----------
        username : str or iterable

        If `username' is specified by str it should be a single username or
        usernames separeated by spaces or commas.
        `username` can contain a leading @

        Examples:
            setUsername('barackobama')
            setUsername('barackobama,whitehouse')
            setUsername('barackobama whitehouse')
            setUsername(['barackobama','whitehouse'])
        """
        self.username = username
        return self

    def setExcludeWords(self, excludeWords):
        """Set word(s) to exclude from tweets
        Parameters
        ----------
        excludeWords : list or iterable

        Example: ["red", "blue", "yellow", "green"]
        """
        self.excludeWords = excludeWords
        return self

    def setSince(self, since):
        """Set a lower bound date in UTC
        Parameters
        ----------
        since : str,
                format: "yyyy-mm-dd"
        """
        self.since = since
        return self

    def setUntil(self, until):
        """Set an upper bound date in UTC (not included in results)
        Parameters
        ----------
        until : str,
                format: "yyyy-mm-dd"
        """
        self.until = until
        return self

    def setMinReplies(self, minReplies):
        """Set the minimum number of replies of tweets to search
        Parameters
        ----------
        minReplies : str,
                     for example: 42
        """
        self.minReplies = minReplies
        return self

    def setMinFaves(self, minFaves):
        """Set the minimum number of favorites of tweets to search
        Parameters
        ----------
        minFaves : str,
                   for example: 42
        """
        self.minFaves = minFaves
        return self

    def setMinRetweets(self, minRetweets):
        """Set the minimum number of retweets of tweets to search
        Parameters
        ----------
        minRetweets : str,
                      for example: 42
        """
        self.minRetweets = minRetweets
        return self

    def setNear(self, near):
        """Set location to search nearby
        Parameters
        ----------
        near : str,
               for example "Berlin, Germany"
        """
        self.near = near
        return self

    def setWithin(self, within):
        """Set the radius for search by location
        Parameters
        ----------
        within : str,
                 for example "15mi"
        """
        self.within = within
        return self

    def setQuerySearch(self, querySearch):
        """Set a text to be searched for
        Parameters
        ----------
        querySearch : str
        """
        self.querySearch = querySearch
        return self

    def setMaxTweets(self, maxTweets):
        """Set the maximum number of tweets to search
        Parameters
        ----------
        maxTweets : int
        """
        self.maxTweets = maxTweets
        return self

    def setLang(self, Lang):
        """Set language
        Parameters
        ----------
        Lang : str
        """
        self.lang = Lang
        return self

    def setEmoji(self, Emoji):
        """Set emoji style. Style must be one of 'ignore', 'unicode', or 'name'.
        Parameters
        ----------
        Emoji : str
        """
        self.emoji = Emoji
        return self

    def setTopTweets(self, topTweets):
        """Set the flag to search only for top tweets
        Parameters
        ----------
        topTweets : bool
        """
        self.topTweets = topTweets
        return self
