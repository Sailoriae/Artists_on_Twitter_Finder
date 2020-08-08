var twitterAccountsDiv = document.getElementById("twitter-accounts");
var tweetsDiv = document.getElementById("tweets");
var displayErrorP = document.getElementById("display-error");
var displayProcessStatusP = document.getElementById("display-process-status");
var displayStatsP = document.getElementById("display-stats");
var displayInfosP = document.getElementById("display-infos");
var displaySupportedWebitesP = document.getElementById("supported-websites");

displayStats();
displaySupportedWebites();

function mainFunction () {
	document.getElementById("launch").style.display = "none";
	document.getElementById("illust-url").readOnly = true;

	twitterAccountsDiv.innerHTML = "";
	tweetsDiv.innerHTML = "";
	displayErrorP.innerHTML = "";
	displayProcessStatusP.innerHTML = "";

	var illustURL = document.getElementById("illust-url").value;
	var request = new XMLHttpRequest();

	request.addEventListener( "readystatechange", async function() {
		if ( this.readyState === 4 ) {
			if ( request.status === 200 ) {
				if ( request.responseText === "" ) {
					displayErrorP.textContent = lang["CANNOT_CONTACT_SERVER"];
					return;
				} else {
					var json = JSON.parse( request.responseText );
					console.log( json );
					populateError( json );

					populateStatus( json );

					if ( canPrintAccounts( json ) ) {
						populateTwitterAccounts( json );
					}
					if ( canPrintTweets(json) ) {
						populateTweets( json );
					}

					waitAndUpdate( json );
				}
			} else if ( request.status === 429 ) {
				await new Promise(r => setTimeout(r, 1000));
				mainFunction();
			} else {
				displayErrorP.textContent = lang["CANNOT_CONTACT_SERVER"];
			}
		}
	});

	request.open("GET", "./api/?url=" + illustURL); // self.send_header("Access-Control-Allow-Origin", "*")
	request.send();
}

async function waitAndUpdate ( json ) {
	if ( ! ( json["status"] === "END" ) ) {
		await new Promise(r => setTimeout(r, 5000));
		mainFunction();
	} else {
		document.getElementById("launch").style.display = "block";
		document.getElementById("illust-url").readOnly = false;
	}
}

function canPrintAccounts ( json ) {
	if ( ( json["status"] === "WAIT_LINK_FINDER" ) ||
		 ( json["status"] === "LINK_FINDER" ) ) {
		return false;
	}
	if ( ( json.error === "NO_URL_FIELD" ) ||
		 ( json.error === "NOT_AN_URL" ) ||
		 ( json.error === "INVALID_URL" ) ||
		 ( json.error === "UNSUPPORTED_WEBSITE" ) ||
		 ( json.error === "NO_TWITTER_ACCOUNT_FOR_THIS_ARTIST" ) ||
		 ( json.error === "NO_VALID_TWITTER_ACCOUNT_FOR_THIS_ARTIST" ) ||
		 ( json.error === "YOUR_IP_HAS_MAX_PENDING_REQUESTS" ) ) {
		 return false;
	}

	return true;
}

function canPrintTweets ( json ) {
	if ( ( json.error === "NO_URL_FIELD" ) ||
		 ( json.error === "NOT_AN_URL" ) ||
		 ( json.error === "INVALID_URL" ) ||
		 ( json.error === "UNSUPPORTED_WEBSITE" ) ||
		 ( json.error === "NO_TWITTER_ACCOUNT_FOR_THIS_ARTIST" ) ||
		 ( json.error === "NO_VALID_TWITTER_ACCOUNT_FOR_THIS_ARTIST" ) ||
		 ( json.error === "YOUR_IP_HAS_MAX_PENDING_REQUESTS" ) ) {
		return false;
	}

	return ( json["status"] === "END" );
}

function populateError ( json ) {
	displayErrorP.textContent = lang[ json.error ];
}

function populateStatus ( json ) {
	var p = document.createElement('p');
	p.textContent = lang[ "STATUS" ];
	p.textContent += lang[ json["status"] ]
	displayProcessStatusP.appendChild(p);
}

function populateTwitterAccounts ( json ) {
	var twitterAccounts = json['twitter_accounts'];

	if ( twitterAccounts.length === 0 ) {
		var p = document.createElement('p');
		p.textContent = lang[ "NO_TWITTER_ACCOUNT_FOUNDED" ];
	} else {
		var p = document.createElement('p');
		p.textContent = lang[ "FOUNDED_TWITTER_ACCOUNTS" ];

		for ( var i = 0; i < twitterAccounts.length; i++ ) {
			var a = document.createElement('a');
			a.href = "https://twitter.com/" + twitterAccounts[i].account_name;
			a.target = "_blank";
			a.textContent = "@" + twitterAccounts[i].account_name;
			p.appendChild(a);

			if ( i < twitterAccounts.length - 1 ) {
				p.append( ", " );
			}
		}
	}

	twitterAccountsDiv.appendChild(p);
}

function populateTweets ( json ) {
	var tweets = json["results"];

	if ( tweets.length === 0 ) {
		var p = document.createElement('p');
		p.textContent = lang[ "NO_TWEET_FOUNDED" ];
		tweetsDiv.appendChild(p);
	} else {
		var alreadyDisplayedTweetsID = [];

		for ( var i = 0; i < tweets.length; i++ ) {
			if ( alreadyDisplayedTweetsID.indexOf( tweets[i].tweet_id ) === -1 ) {
				alreadyDisplayedTweetsID.push( tweets[i].tweet_id );

				var div = document.createElement('div');

				var p = document.createElement('p');
				p.textContent = lang[ "FOUNDED_TWEET" ];
				var a = document.createElement('a');
				a.href = "https://twitter.com/any/status/" + tweets[i].tweet_id;
				a.target = "_blank";
				a.textContent = "https://twitter.com/any/status/" + tweets[i].tweet_id;
				p.appendChild(a);
				div.appendChild(p);

				twttr.widgets.createTweet( tweets[i].tweet_id, div, {
					conversation : "none",
					cards : "visible",
					linkColor : "#cc0000",
					theme : "light",
					dnt : "true"
				})

				tweetsDiv.appendChild(div);
			}
		}
	}
}

// Source : https://stackoverflow.com/questions/7790811/how-do-i-put-variables-inside-javascript-strings-node-js
function parse(str) {
	var args = [].slice.call(arguments, 1),
		i = 0;

	return str.replace(/%s/g, () => args[i++]);
}

function displayStats() {
	displayStatsP.innerHTML = "";
	displayInfosP.innerHTML = "";

	var request = new XMLHttpRequest();

	request.addEventListener( "readystatechange", async function() {
		if ( this.readyState === 4 ) {
			if ( request.status === 200 ) {
				if ( request.responseText === "" ) {
					displayStatsP.textContent = lang[ "CANNOT_DISPLAY_STATS" ];
					return;
				} else {
					var json = JSON.parse( request.responseText );
					console.log( json );
					displayStatsP.textContent = parse( lang[ "STATS" ], numberWithSpaces( json["indexed_tweets_count"] ), numberWithSpaces( json["indexed_accounts_count"] ) );

					displayInfosP.textContent = parse( lang[ "INFO" ], json["limit_per_ip_address"] )
				}
			} else if ( request.status === 429 ) {
				await new Promise(r => setTimeout(r, 1000));
				displayStats();
			} else {
				displayStatsP.textContent = lang[ "CANNOT_DISPLAY_STATS" ];
			}
		}
	});

	request.open("GET", "./api/stats"); // self.send_header("Access-Control-Allow-Origin", "*")
	request.send();
}

// Source : https://stackoverflow.com/questions/16637051/adding-space-between-numbers
function numberWithSpaces(x) {
	return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

function displaySupportedWebites() {
	displaySupportedWebitesP.innerHTML = "";

	var request = new XMLHttpRequest();

	request.addEventListener( "readystatechange", function() {
		if ( this.readyState === 4 ) {
			if ( request.status === 200 ) {
				if ( request.responseText === "" ) {
					return;
				} else {
					var json = JSON.parse( request.responseText );
					console.log( json );
					displaySupportedWebitesP.textContent = lang[ "SUPPORTED_WEBSITES" ];

					var keys = Object.keys( json );
					for ( var i = 0; i < keys.length; i++ ) {
						var a = document.createElement('a');
						a.href = json[ keys[i] ];
						a.target = "_blank";
						a.textContent = keys[i];
						displaySupportedWebitesP.appendChild(a);

						if ( i < keys.length - 1 ) {
							displaySupportedWebitesP.append( ", " );
						} else {
							displaySupportedWebitesP.append( "." );
						}
					}
				}
			}
		}
	});

	request.open("GET", "./supported_websites.json");
	request.send();
}
