var errorP = document.getElementById("display-error");
var processStatusP = document.getElementById("display-process-status");

displayStats();
displaySupportedWebites();

function mainFunction ( new_loop = true ) {
	document.getElementById("launch").style.display = "none";
	document.getElementById("illust-url").readOnly = true;

	if ( new_loop ) {
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
			} else {
				errorP.textContent = lang["CANNOT_CONTACT_SERVER"];
			}
		}
	});

	request.open("GET", "./api/?url=" + illustURL); // self.send_header("Access-Control-Allow-Origin", "*")
	request.send();
}

async function waitAndUpdate ( json ) {
	if ( ! ( json["status"] === "END" ) ) {
		await new Promise(r => setTimeout(r, 5000));
		mainFunction( new_loop = false );
	} else {
		document.getElementById("launch").style.display = "block";
		document.getElementById("illust-url").readOnly = false;
	}
}

function displayError ( json ) {
	errorP.textContent = lang[ json.error ];
}

function displayStatus ( json ) {
	processStatusP.innerHTML = "";

	var p = document.createElement('p');
	p.textContent = lang[ "STATUS" ];
	p.textContent += lang[ json["status"] ]
	processStatusP.appendChild(p);
}
