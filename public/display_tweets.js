var tweetsDiv = document.getElementById("tweets");
var widgetWarningP = document.getElementById("widget-warning");

function canDisplayTweets ( json ) {
	if ( !canDisplayTwitterAccounts( json ) )
		return false;

	if ( json["error"] === "ERROR_DURING_REVERSE_SEARCH" ||
		 json["error"] === "QUERY_IMAGE_TOO_BIG" ) {
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
				a.textContent = "ID " + tweets[i].tweet_id;
				p.appendChild(a);
				div1.appendChild(p);

				const userPrefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
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
					widgetWarningP.textContent = lang[ "CANNOT_DISPLAY_TWEETS" ];
				}

				tweetsDiv.appendChild(div1);
				tweetsDiv.appendChild(div2);
			}
		}
	}
}
