var statsP = document.getElementById("display-stats");
var warningP = document.getElementById("display-warning");

displayStats();

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

					if ( json["processing_user_requests_count"] > 20 ) {
						warningP.innerHTML = lang[ "WARNING_1" ];
						if ( json["pending_tweets_count"] > 1000 ) {
							warningP.innerHTML += "<br/>"
							warningP.innerHTML += parse( lang[ "WARNING_2" ], numberWithSpaces( json["pending_tweets_count"] ) );
						}
					} else if ( json["pending_tweets_count"] > 1000 ) {
						warningP.innerHTML = parse( lang[ "WARNING_3" ], numberWithSpaces( json["pending_tweets_count"] ) );
					} else {
						warningP.innerHTML = "";
					}

					await new Promise(r => setTimeout(r, 30000));
					displayStats();
				}
			} else if ( request.status === 429 ) {
				await new Promise(r => setTimeout(r, 1000));
				displayStats();
			} else {
				statsP.textContent = lang[ "CANNOT_DISPLAY_STATS" ];
				statsP.innerHTML += "<br/>" + lang[ "SERVER_IS_DOWN" ];
			}
		}
	});

	request.open("GET", "./api/stats"); // self.send_header("Access-Control-Allow-Origin", "*")
	request.send();
}
