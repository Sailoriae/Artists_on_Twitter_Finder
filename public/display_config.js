var infosP = document.getElementById("display-infos");
var advancedP = document.getElementById("display-advanced");

displayConfig();

function displayConfig() {
	var request = new XMLHttpRequest();

	request.addEventListener( "readystatechange", async function() {
		if ( this.readyState === 4 ) {
			if ( request.status === 200 ) {
				if ( request.responseText != "" ) {
					var json = JSON.parse( request.responseText );
					console.log( json );
					infosP.textContent = parse( lang[ "INFO" ], json["limit_per_ip_address"] );
					if ( json["ip_can_bypass_limit"] )
						infosP.innerHTML += "<br/>" + lang[ "IP_CAN_BYPASS_LIMIT" ];
					if ( json["ip_can_use_advanced"] ) {
						infosP.innerHTML += "<br/>" + lang[ "IP_CAN_USE_ADVANCED" ];
						advancedP.classList.remove("display-none");
					}
				}
			} else if ( request.status === 429 ) {
				await new Promise(r => setTimeout(r, 1000));
				displayConfig();
			}
		}
	});

	request.open("GET", baseURL + "/config"); // self.send_header("Access-Control-Allow-Origin", "*")
	request.send();
}
