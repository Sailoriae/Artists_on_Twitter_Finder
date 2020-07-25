var twitterAccountsDiv = document.getElementById("twitter-accounts");
var tweetsDiv = document.getElementById("tweets");
var displayErrorP = document.getElementById("display-error");
var displayProcessStatusP = document.getElementById("display-process-status");
var displayStatsP = document.getElementById("display-stats");
var displayInfosP = document.getElementById("display-infos");

displayStats();

function mainFunction () {
	document.getElementById("launch").style.display = "none";
	document.getElementById("illust-url").readOnly = true;

	twitterAccountsDiv.innerHTML = "";
	tweetsDiv.innerHTML = "";
	displayErrorP.innerHTML = "";
	displayProcessStatusP.innerHTML = "";

	var illustURL = document.getElementById("illust-url").value;
	var request = new XMLHttpRequest();

	request.addEventListener( "readystatechange", function() {
		if ( this.readyState === 4 ) {
			if ( request.status === 200 ) {
				if ( request.responseText === "" ) {
					displayErrorP.textContent = "Impossible de contacter le serveur.";
					return;
				} else {
					var json = JSON.parse( request.responseText );
					console.log( json );
					var isThereAnError = isThereAnErrorAndIfYesPopulateError( json );

					populateStatus( json );

					if ( canPrintAccounts( json ) ) {
						populateTwitterAccounts( json );
					}
					if ( ! ( isThereAnError ) && ( canPrintTweets(json) ) ) {
						populateTweets( json );
					}

					waitAndUpdate( json );
				}
			} else {
				displayErrorP.textContent = "Impossible de contacter le serveur.";
			}
		}
	});

	request.open("GET", "http://localhost:3301/?url=" + illustURL); // self.send_header("Access-Control-Allow-Origin", "*")
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
	return ( json["status"] === "END" );
}

function isThereAnErrorAndIfYesPopulateError ( json ) {
	if ( json.error === "NO_URL_FIELD" ) {
		displayErrorP.textContent = "Aucune URL entrée.";
		return true;
	} else if ( json.error === "INVALID_URL" ) {
		displayErrorP.textContent = "URL entrée invalide.";
		return true;
	} else if ( json.error === "UNSUPPORTED_WEBSITE" ) {
		displayErrorP.textContent = "Site de l'URL entrée non supporté.";
		return true;
	} else if ( json.error === "NO_TWITTER_ACCOUNT_FOR_THIS_ARTIST" ) {
		displayErrorP.textContent = "Aucun compte Twitter trouvé pour cet artiste.";
		return true;
	} else if ( json.error === "NO_VALID_TWITTER_ACCOUNT_FOR_THIS_ARTIST" ) {
		displayErrorP.textContent = "Aucun compte Twitter valide trouvé pour cet artiste.";
		return true;
	} else if ( json.error === "ERROR_DURING_REVERSE_SEARCH" ) {
		displayErrorP.textContent = "L'illustration entrée a un format à la noix et ne peut pas être cherchée.";
		return true;
	} else if ( json.error === "PROCESSING_ERROR" ) {
		displayErrorP.textContent = "Erreur coté serveur, impossible de terminer le traitement de la requête.";
		return true;
	} else if ( json.error === "YOUR_IP_HAS_MAX_PENDING_REQUESTS" ) {
		displayErrorP.textContent = "Votre adresse IP a atteint son quota maximal de requêtes en cours de traitement.";
		return true;
	}
	return false;
}

function populateStatus ( json ) {
	var p = document.createElement('p');
	p.textContent = "Status du traitement : ";

	if ( json["status"] === "END" ) {
		p.textContent += "Fin de traitement.";
	} else {
		p.textContent += "En cours de traitement par le serveur...";
	}

	displayProcessStatusP.appendChild(p);
}

function populateTwitterAccounts ( json ) {
	var p = document.createElement('p');
	p.textContent = "Comptes Twitter trouvés : ";

	var twitterAccounts = json['twitter_accounts'];

	for ( var i = 0; i < twitterAccounts.length; i++ ) {
		var a = document.createElement('a');
		a.href = "https://twitter.com/" + twitterAccounts[i].account_name;
		a.target = "_blank";
		a.textContent = "@" + twitterAccounts[i].account_name;
		p.appendChild(a);

		if ( i < twitterAccounts.length ) {
			p.appendChild = ", ";
		}
	}

	twitterAccountsDiv.appendChild(p);
}

function populateTweets ( json ) {
	var tweets = json["results"];

	if ( tweets.length === 0 ) {
		var p = document.createElement('p');
		p.textContent = "Aucun Tweet trouvé.";
		tweetsDiv.appendChild(p);
	} else {
		for ( var i = 0; i < tweets.length; i++ ) {
			var div = document.createElement('div');

			var p = document.createElement('p');
			p.textContent = "Tweet trouvé (" + (i+1) + "/" + tweets.length + ") : ";
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

function displayStats() {
	displayStatsP.innerHTML = "";
	displayInfosP.innerHTML = "";

	var request = new XMLHttpRequest();

	request.addEventListener( "readystatechange", function() {
		if ( this.readyState === 4 ) {
			if ( request.status === 200 ) {
				if ( request.responseText === "" ) {
					displayStatsP.textContent = "Impossible d'afficher les statistiques.";
					return;
				} else {
					var json = JSON.parse( request.responseText );
					console.log( json );
					displayStatsP.textContent = json["indexed_tweets_count"] + " Tweets indexés sur " + json["indexed_accounts_count"] + " comptes Twitter.";

					displayInfosP.textContent = "Les nombre de requêtes en cours de traitement par adresse IP est limité à " + json["limit_per_ip_address"] + "."
					if ( json["no_update_on_request"] ) {
						displayInfosP.textContent += " Attention ! L'index des Tweets des comptes n'est pas mis à jour lors d'une requête."
					}
					displayInfosP.textContent += " L'index des Tweets avec images d'un compte est mis à jour automatiquement au bout de " + json["update_accounts_frequency"] + " jours."
				}
			} else {
				displayStatsP.textContent = "Impossible d'afficher les statistiques.";
			}
		}
	});

	request.open("GET", "http://localhost:3301/stats"); // self.send_header("Access-Control-Allow-Origin", "*")
	request.send();
}