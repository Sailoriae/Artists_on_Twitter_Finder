var danbooruA = document.getElementById("danbooru-link");
var danbooruP = document.getElementById("danbooru-warning");

danbooruA.onclick = function() {
	if ( danbooruP.classList.contains( "display-none" ) )
		danbooruP.classList.remove("display-none");
	else
		danbooruP.classList.add("display-none");
};


var defaultSearchP = document.getElementById("display-default-search");
var directSearchP = document.getElementById("display-direct-search");

var defaultSearchDiv = document.getElementById("default-search");
var directSearchDiv = document.getElementById("direct-search");

var directSearch = false;

defaultSearchP.onclick = function () {
	defaultSearchP.classList.add("display-none");
	directSearchP.classList.remove("display-none");
	defaultSearchDiv.classList.remove("display-none");
	directSearchDiv.classList.add("display-none");
	directSearch = false;
};

directSearchP.onclick = function () {
	defaultSearchP.classList.remove("display-none");
	directSearchP.classList.add("display-none");
	defaultSearchDiv.classList.add("display-none");
	directSearchDiv.classList.remove("display-none");
	directSearch = true;
};
