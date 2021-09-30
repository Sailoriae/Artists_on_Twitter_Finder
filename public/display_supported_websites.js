var supportedWebitesP = document.getElementById("supported-websites");

displaySupportedWebites();

function displaySupportedWebites() {
	supportedWebitesP.innerHTML = "";

	var request = new XMLHttpRequest();

	request.addEventListener( "readystatechange", function() {
		if ( this.readyState === 4 ) {
			if ( request.status === 200 ) {
				if ( request.responseText != "" ) {
					var json = JSON.parse( request.responseText );
					console.log( json );
					supportedWebitesP.textContent = lang[ "SUPPORTED_WEBSITES" ];

					var keys = Object.keys( json );
					for ( var i = 0; i < keys.length; i++ ) {
						var a = document.createElement('a');
						a.href = json[ keys[i] ];
						a.target = "_blank";
						a.rel = "noopener";
						a.textContent = keys[i];
						supportedWebitesP.appendChild(a);

						if ( i < keys.length - 1 ) {
							supportedWebitesP.append( ", " );
						} else {
							supportedWebitesP.append( "." );
						}
					}
				}
			}
		}
	});

	request.open("GET", "./supported_websites.json");
	request.send();
}
