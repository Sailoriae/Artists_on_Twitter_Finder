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
					document.getElementById("loader").style.display = "none";
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
				document.getElementById("loader").style.display = "none";
			}
		}
	});

	request.open("POST", "./api/query"); // self.send_header("Access-Control-Allow-Origin", "*")
	request.setRequestHeader("Content-type", "text/plain");
	request.send( illustURL );
}

function lockUI () {
	document.getElementById("launch").style.display = "none";
	document.getElementById("illust-url").readOnly = true;
	document.getElementById("loader").style.display = "inline-block";
}

function unlockUI () {
	document.getElementById("launch").style.display = "block";
	document.getElementById("illust-url").readOnly = false;
	document.getElementById("loader").style.display = "none";
}

async function waitAndUpdate ( json ) {
	if ( json["error"] === "YOUR_IP_HAS_MAX_PROCESSING_REQUESTS" ) {
		retryLoopOnError( waitTime = 30 )
	} else if ( ! ( json["status"] === "END" ) ) {
		await new Promise(r => setTimeout(r, 5000));
		mainFunction( new_loop = false );
	} else {
		unlockUI();
	}
}

async function retryLoopOnError ( waitTime = 30 ) {
	saveErrorP = errorP.innerHTML;
	for ( var i = waitTime; i > 0; i-- ) {
		errorP.innerHTML = saveErrorP + "<br/>" + parse( lang[ "NEXT_TRY_IN" ], i );
		await new Promise(r => setTimeout(r, 1000));
	}
	mainFunction( new_loop = false );
}

function displayError ( json ) {
	errorP.textContent = lang[ json.error ];
}

function displayStatus ( json ) {
	processStatusP.textContent = lang[ "STATUS" ];
	processStatusP.textContent += lang[ json["status"] ]
	
	if ( ( json[ "has_first_time_scan" ] ) && ( json["status"] === "INDEX_ACCOUNTS_TWEETS" ) ) {
		processStatusP.textContent += " " + lang[ "WARNING_FIRST_TIME_INDEX_ACCOUNTS_TWEETS" ];
	}
}
