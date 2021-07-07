// Source : https://stackoverflow.com/a/7790858
function parse( str ) {
	var args = [].slice.call(arguments, 1),
		i = 0;

	return str.replace(/%s/g, () => args[i++]);
}

// Source : https://stackoverflow.com/a/16637170
function numberWithSpaces( x ) {
	return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}
