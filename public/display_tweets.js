var tweetsDiv = document.getElementById("tweets");

function canDisplayTweets ( json ) {
	if ( ( json.error === "NO_URL_FIELD" ) ||
		 ( json.error === "NOT_AN_URL" ) ||
		 ( json.error === "INVALID_URL" ) ||
		 ( json.error === "UNSUPPORTED_WEBSITE" ) ||
		 ( json.error === "NO_TWITTER_ACCOUNT_FOUND" ) ||
		 ( json.error === "NO_VALID_TWITTER_ACCOUNT_FOUND" ) ||
		 ( json.error === "YOUR_IP_HAS_MAX_PROCESSING_REQUESTS" ) ) {
		return false;
	}

	return ( json["status"] === "END" );
}

function displayTweets ( json ) {
	tweetsDiv.innerHTML = "";

	if ( ! canDisplayTweets( json ) ) {
		return;
	}

	var tweets = json["results"];

	if ( tweets.length === 0 ) {
		var p = document.createElement('p');
		p.textContent = lang[ "NO_TWEET_FOUND" ];
		tweetsDiv.appendChild(p);
	} else {
		var alreadyDisplayedTweetsID = [];

		for ( var i = 0; i < tweets.length; i++ ) {
			if ( alreadyDisplayedTweetsID.indexOf( tweets[i].tweet_id ) === -1 ) {
				alreadyDisplayedTweetsID.push( tweets[i].tweet_id );

				var div1 = document.createElement('div');
				var div2 = document.createElement('div');

				var p = document.createElement('p');
				p.textContent = lang[ "TWEET_FOUND" ];
				var a = document.createElement('a');
				a.href = "https://twitter.com/any/status/" + tweets[i].tweet_id;
				a.target = "_blank";
				a.rel = "noopener";
				a.textContent = "https://twitter.com/any/status/" + tweets[i].tweet_id;
				p.appendChild(a);
				div1.appendChild(p);

				const userPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
				if (userPrefersDark) {
					var theme = "dark";
				} else {
					var theme = "light";
				}

				try {
					twttr.widgets.createTweet( tweets[i].tweet_id, div2, {
						conversation : "none",
						cards : "visible",
						linkColor : "#cc0000",
						theme : theme,
						dnt : "true"
					})
				} catch ( ReferenceError ) { // Si la JS de Twitter n'a pas été chargée
					var p = document.createElement('p');
					p.textContent = lang[ "CANNOT_DISPLAY_TWEET" ];
					div2.appendChild(p);
				}

				tweetsDiv.appendChild(div1);
				tweetsDiv.appendChild(div2);
			}
		}
	}
}
