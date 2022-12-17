var statsP = document.getElementById("display-stats");
var warningP = document.getElementById("display-warning");

displayStats();

function displayStats() {
	var request = new XMLHttpRequest();

	request.addEventListener( "readystatechange", async function() {
		if ( this.readyState === 4 ) {
			if ( request.status === 200 ) {
				if ( request.responseText != "" ) {
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
			} else if ( request.status === 503 ) {
				statsP.textContent = lang[ "CANNOT_DISPLAY_STATS" ];
				statsP.innerHTML += "<br/>" + parse( lang[ "SERVER_IS_DOWN" ], "<a href=\"https://twitter.com/" + contactScreenName + "\" target=\"_blank\" rel=\"noopener\">@" + contactScreenName + "</a>" );
				retryLoopOnServerDown();
			} else {
				statsP.textContent = lang[ "WRONG_WEBSERVER_CONFIG" ];
			}
		}
	});

	request.open("GET", baseURL + "/stats"); // self.send_header("Access-Control-Allow-Origin", "*")
	request.send();
}

async function retryLoopOnServerDown ( waitTime = 60 ) {
	saveStatsP = statsP.innerHTML;
	for ( var i = waitTime; i > 0; i-- ) {
		statsP.innerHTML = saveStatsP + "<br/>" + parse( i > 1 ? lang[ "NEXT_TRY_IN" ] : lang[ "NEXT_TRY_IN_SINGULAR" ], i );
		await new Promise(r => setTimeout(r, 1000));
	}
	displayStats();
}
