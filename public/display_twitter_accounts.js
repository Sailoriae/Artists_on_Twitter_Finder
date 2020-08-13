var twitterAccountsDiv = document.getElementById("twitter-accounts");

function canDisplayTwitterAccounts ( json ) {
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

function displayTwitterAccounts ( json ) {
	twitterAccountsDiv.innerHTML = "";

	if ( ! canDisplayTwitterAccounts( json ) ) {
		return;
	}

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