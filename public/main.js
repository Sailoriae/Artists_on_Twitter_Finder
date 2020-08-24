var errorP = document.getElementById("display-error");
var processStatusP = document.getElementById("display-process-status");

displayStats();
displaySupportedWebites();

function mainFunction ( new_loop = true ) {
	if ( new_loop ) {
		lockUI();

		twitterAccountsDiv.innerHTML = "";
		tweetsDiv.innerHTML = "";
		errorP.innerHTML = "";
		processStatusP.innerHTML = "";
	}

	var illustURL = document.getElementById("illust-url").value;
	var request = new XMLHttpRequest();

	request.addEventListener( "readystatechange", async function() {
		if ( this.readyState === 4 ) {
			if ( request.status === 200 ) {
				if ( request.responseText === "" ) {
					errorP.textContent = lang["CANNOT_CONTACT_SERVER"];
					return;
				} else {
					var json = JSON.parse( request.responseText );
					console.log( json );
					displayError( json );
					displayStatus( json );
					displayTwitterAccounts( json );
					displayTweets( json );

					waitAndUpdate( json );
				}
			} else if ( request.status === 429 ) {
				await new Promise(r => setTimeout(r, 1000));
				mainFunction( new_loop = false );
			} else if ( request.status === 414 ) {
				errorP.textContent = lang["REQUEST_URI_TOO_LONG"];
				unlockUI()
			} else {
				errorP.textContent = lang["CANNOT_CONTACT_SERVER"];
			}
		}
	});

	request.open("GET", "./api/?url=" + illustURL); // self.send_header("Access-Control-Allow-Origin", "*")
	request.send();
}

function lockUI () {
	document.getElementById("launch").style.display = "none";
	document.getElementById("illust-url").readOnly = true;
}

function unlockUI () {
	document.getElementById("launch").style.display = "block";
	document.getElementById("illust-url").readOnly = false;
}

async function waitAndUpdate ( json ) {
	if ( ! ( json["status"] === "END" ) ) {
		await new Promise(r => setTimeout(r, 5000));
		mainFunction( new_loop = false );
	} else {
		unlockUI();
	}
}

function displayError ( json ) {
	errorP.textContent = lang[ json.error ];
}

function displayStatus ( json ) {
	processStatusP.textContent = lang[ "STATUS" ];
	processStatusP.textContent += lang[ json["status"] ]
	
	if ( json[ "has_first_time_scan" ] ) {
		processStatusP.textContent += " " + lang[ "WARNING_FIRST_TIME_INDEX_ACCOUNTS_TWEETS" ];
	}
}
