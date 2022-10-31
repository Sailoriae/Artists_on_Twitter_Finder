var danbooruA = document.getElementById("danbooru-link");
var danbooruP = document.getElementById("danbooru-warning");

danbooruA.onclick = function() {
	if ( danbooruP.classList.contains( "display-none" ) )
		danbooruP.classList.remove("display-none");
	else
		danbooruP.classList.add("display-none");
};
