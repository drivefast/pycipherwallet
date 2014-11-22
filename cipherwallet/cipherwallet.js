var all_cw_codes = {};

function Cipherwallet(options) {

	// the id of the (typically) div element that will display the QR code and the "What's this" link underneath
	this.qrContainer = document.getElementById(options.qrContainerID);
	if (!this.qrContainer) return;
	this.tag = options.qrContainerID;
	// detailsURL is a web page describes cipherwallet from an user perspective
	this.detailsURL = options.detailsURL || "http://www.cipherwallet.com/wtfcipherwallet.html";
	// callback function for successful data transfer; will have as argument the JSON received on the poll response
	this.onSuccess = options.onSuccess || function(x) {}; 
	// callback function for failed data transfer; will have as argument a number that can be:
	//     400 = bad parameters, that shouldnt happen if the API code is clean
	//     401 = the request that transmitted the data was not authorized
	//     410 = offer expired
	//       0 = any other screwed up error
	this.onFailure = options.onFailure || function(x) {}; 
	this.polls = true;
	all_cw_codes[this.tag] = this;
	// populate the div that will display the QR code, and activate the longPoll() loop
	// when the image download completes
	this.qrContainer.innerHTML =
		'<a href="' + this.detailsURL + '">' +
		'<img ' + 
		    'src="/cipherwallet/' + this.tag + '/qr.png?_=' + Date.now() + '" ' +
		    'onload="all_cw_codes[\'' + this.tag + '\'].longPoll()" ' +
		'/>' +
		'<p>What\'s this?</p>' +
		'</a>'
	;

}	

Cipherwallet.prototype.longPoll = function() {
// continuously poll the AJAX server waiting for data to be received from the mobile app
    if (!this.polls)
        return;
    var this_tag = this.tag;
    $.ajax({ 
        url: "/cipherwallet/" + this_tag,
        cache: false,
        statusCode: {
            // user scanned code and posted data successfully, call the onSuccess() function
            200: function(user_data) { 
                all_cw_codes[this_tag].polls = false; 
                all_cw_codes[this_tag].onSuccess(user_data); 
            },
            // no scanned information received (yet)
            202: function() { console.log("..."); },
        },
        error: function(xhr, textStatus, errorThrown) { 
            // poll function encountered an error, the http status is meaningful
            all_cw_codes[this_tag].qrContainer.style.display = "none"; 
            all_cw_codes[this_tag].polls = false; 
            // also call the onFailure() function
            all_cw_codes[this_tag].onFailure(xhr.status); 
        },
        complete: function() { all_cw_codes[this_tag].longPoll(); }, 
        timeout: 10000 
    });
};

Cipherwallet.prototype.stop = function() {
// stop polling
    this.polls = false;
    this.qrContainer.innerHTML = "";
};

Cipherwallet.prototype.registerForQRLogin = function(user, cb) {
// you may call this to complete a registration procedure
    $.ajax({ 
        type: "POST",
        url: "/cipherwallet/" + this.tag,
        data: { user_id: user },
        complete: function(xhr) { cb(xhr.status == 200); },
        timeout: 20000 
    });
};
