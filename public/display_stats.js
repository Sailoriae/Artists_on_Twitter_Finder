var statsP = document.getElementById("display-stats");
var warningP = document.getElementById("display-warning");
var infosP = document.getElementById("display-infos");

// Source : https://stackoverflow.com/questions/7790811/how-do-i-put-variables-inside-javascript-strings-node-js
function parse( str ) {
	var args = [].slice.call(arguments, 1),
		i = 0;

	return str.replace(/%s/g, () => args[i++]);
}

// Source : https://stackoverflow.com/questions/16637051/adding-space-between-numbers
function numberWithSpaces( x ) {
	return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

function displayStats() {
	var request = new XMLHttpRequest();

	request.addEventListener( "readystatechange", async function() {
		if ( this.readyState === 4 ) {
			if ( request.status === 200 ) {
				if ( request.responseText === "" ) {
					statsP.textContent = lang[ "CANNOT_DISPLAY_STATS" ];
					return;
				} else {
					var json = JSON.parse( request.responseText );
					console.log( json );
					statsP.innerHTML = parse( lang[ "STATS_1" ], numberWithSpaces( json["indexed_tweets_count"] ), numberWithSpaces( json["indexed_accounts_count"] ) );

					statsP.innerHTML += "<br/>";

					if ( json["processing_user_requests_count"] == 0 )
						statsP.innerHTML += lang[ "STATS_2_1_ZERO" ];
					else if ( json["processing_user_requests_count"] == 1 )
						statsP.innerHTML += lang[ "STATS_2_1_ONE" ];
					else
						statsP.innerHTML += parse( lang[ "STATS_2_1_PLURAL" ], numberWithSpaces( json["processing_user_requests_count"] ) );

					if ( json["processing_scan_requests_count"] == 0 )
						statsP.innerHTML += lang[ "STATS_2_2_ZERO" ];
					else if ( json["processing_scan_requests_count"] == 1 )
						statsP.innerHTML += lang[ "STATS_2_2_ONE" ];
					else
						statsP.innerHTML += parse( lang[ "STATS_2_2_PLURAL" ], numberWithSpaces( json["processing_scan_requests_count"] ) );

					infosP.textContent = parse( lang[ "INFO" ], json["limit_per_ip_address"] );

					if ( json["processing_user_requests_count"] > 20 ) {
						warningP.textContent = json["processing_user_requests_count"];
					}

					await new Promise(r => setTimeout(r, 30000));
					displayStats();
				}
			} else if ( request.status === 429 ) {
				await new Promise(r => setTimeout(r, 1000));
				displayStats();
			} else {
				statsP.textContent = lang[ "CANNOT_DISPLAY_STATS" ];
			}
		}
	});

	request.open("GET", "./api/stats"); // self.send_header("Access-Control-Allow-Origin", "*")
	request.send();
}
