function streamingUrl(path)
	{ return `${location.protocol}://${location.host}/${path}`; }

function initUrl(url)
	{ return eval(fetch(url)); }

function streamingInit(path)
	{ return initUrl
		(streamingUrl
			(path)); }


function update()
	{ return streamingInit(location.path); }

function init()
	{ return streamingInit
		('init-1.js'); }
