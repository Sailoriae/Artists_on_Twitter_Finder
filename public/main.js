var errorP = document.getElementById("display-error");
var processStatusP = document.getElementById("display-process-status");

document.getElementById("launch-default").onclick = function() {
	mainFunction();
};

document.getElementById("launch-direct").onclick = function() {
	mainFunction( true, true );
};

function mainFunction ( new_loop = true, isDirectRequest = false, identifier = null ) {
	if ( new_loop ) {
		lockUI();

		twitterAccountsDiv.innerHTML = "";
		tweetsDiv.innerHTML = "";
		errorP.innerHTML = "";
		processStatusP.innerHTML = "";
	}

	var request = new XMLHttpRequest();
	var illustURL = document.getElementById("illust-url").value;
	var imageFile = document.getElementById("image-file").files;
	var accountName = document.getElementById("account-name").value;

	request.addEventListener( "readystatechange", async function() {
		if ( this.readyState === 4 ) {
			if ( request.status === 200 ) {
				if ( request.responseText != "" ) {
					var json = JSON.parse( request.responseText );
					console.log( json );
					displayError( json );
					displayStatus( json );
					if ( !isDirectRequest ) displayTwitterAccounts( json );
					displayTweets( json );

					waitAndUpdate( json, isDirectRequest, json["identifier"] );
				}
			} else if ( request.status === 429 ) {
				await new Promise(r => setTimeout(r, 1000));
				mainFunction( false, isDirectRequest, identifier );
			} else if ( request.status === 503 ) {
				errorP.textContent = lang["CANNOT_CONTACT_SERVER"];
				unlockUI();
			} else if ( request.status === 403 ) {
				errorP.textContent = lang["FORBIDDEN"];
				unlockUI();
			}
		}
	});

	if ( isDirectRequest ) { // Recherche directe
		if ( new_loop ) {
			if ( imageFile.length === 0 ) {
				errorP.textContent = lang["IMAGE_MISSING"];
				unlockUI();
				return;
			}
			if ( accountName )
				request.open("POST", baseURL + "/search?account_name=" + accountName);
			else
				request.open("POST", baseURL + "/search");
			request.setRequestHeader("Content-type", imageFile[0].type);
			request.send( imageFile[0] );
		} else {
			request.open("GET", baseURL + "/search?identifier=" + identifier);
			request.send();
		}
	} else { // Recherche classique
		request.open("POST", baseURL + "/query");
		request.setRequestHeader("Content-type", "text/plain");
		request.send( illustURL );
	}
}

function lockUI () {
	document.getElementById("launch-default").style.display = "none";
	document.getElementById("launch-direct").style.display = "none";
	document.getElementById("illust-url").readOnly = true;
	document.getElementById("image-file").readOnly = true;
	document.getElementById("account-name").readOnly = true;
	document.getElementById("loader").style.display = "inline-block";
}

function unlockUI () {
	document.getElementById("launch-default").style.display = "block";
	document.getElementById("launch-direct").style.display = "block";
	document.getElementById("illust-url").readOnly = false;
	document.getElementById("image-file").readOnly = false;
	document.getElementById("account-name").readOnly = false;
	document.getElementById("loader").style.display = "none";
}

async function waitAndUpdate ( json, isDirectRequest = false, identifier = null ) {
	if ( json["error"] === "YOUR_IP_HAS_MAX_PROCESSING_REQUESTS" ) {
		retryLoopOnError( 30, isDirectRequest, identifier )
	} else if ( json["status"] !== null && json["status"] !== "END" ) {
		await new Promise(r => setTimeout(r, 5000));
		mainFunction( false, isDirectRequest, identifier );
	} else {
		unlockUI();
	}
}

async function retryLoopOnError ( waitTime = 30, isDirectRequest = false, identifier = null  ) {
	saveErrorP = errorP.innerHTML;
	for ( var i = waitTime; i > 0; i-- ) {
		errorP.innerHTML = saveErrorP + "<br/>" + parse( i > 1 ? lang[ "NEXT_TRY_IN" ] : lang[ "NEXT_TRY_IN_SINGULAR" ], i );
		await new Promise(r => setTimeout(r, 1000));
	}
	mainFunction( false, isDirectRequest, identifier );
}

function displayError ( json ) {
	errorP.textContent = lang[ json["error"] ];
}

function displayStatus ( json ) {
	if ( json["status"] === null ) {
		processStatusP.innerHTML = "";
		return;
	}

	processStatusP.textContent = lang[ "STATUS" ];
	processStatusP.textContent += lang[ json["status"] ]

	if ( json["status"] === "INDEX_ACCOUNTS_TWEETS" ) {
		if ( json[ "has_first_time_scan" ] )
			processStatusP.textContent += " " + lang[ "WARNING_FIRST_TIME_INDEX_ACCOUNTS_TWEETS" ];
		else
			processStatusP.textContent += " " + lang[ "INDEX_ONLY_FOR_UPDATE" ];
	}
}
