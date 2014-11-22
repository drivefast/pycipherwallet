import time
import bottle

from cqr_auth import verify
import cipherwallet_lib
from cipherwallet_lib import CipherwalletError
from constants import CW_SESSION_TIMEOUT

@bottle.get('/cipherwallet/login')
def _check_login():
    """
    accepts callbacks with no data from the cipherwallet API; these calls verify the availability 
        of the URL and check that the secret API key is set properely
    """
    # get the request custom headers, we need them to authenticate the cipherwallet server
    x_headers = dict((k, bottle.request.headers[k]) for k in bottle.request.headers.keys() if k[0:2] == "X-")
    if not verify(
        bottle.request.method, bottle.request.path, 
        x_headers, "", 
        bottle.request.headers.get('Authorization')
    ):
        bottle.abort(403, "Forbidden")


@bottle.post('/cipherwallet/login')
def _callback_with_data_login():
    """
    login callback requests come from the cipherwallet API server and they're signed with
       our own credentials (as opposed to the other requests, that come unsigned, directly  
       from the mobile app)
    """
    # get the request custom headers, we need them to authenticate the cipherwallet server
    x_headers = dict((k, bottle.request.headers[k]) for k in bottle.request.headers.keys() if k[0:2] == "X-")
    # convert bottle's super-smartass MultiDict to a regular dict
    post_data = dict((k, bottle.request.POST[k]) for k in bottle.request.POST.keys())
    if not verify(
        bottle.request.method, bottle.request.path, 
        x_headers, post_data, 
        bottle.request.headers['Authorization']
    ):
        bottle.abort(403, "Forbidden")

    try:
        bottle.response.content_type = "application/json"
        return cipherwallet_lib.callback_with_data_login(post_data) 
    except CipherwalletError as cwex:
        bottle.abort(cwex.http_status, cwex.http_desc)
        

@bottle.get('/cipherwallet/<operation:re:signup|checkout|reg>')
def _check(operation):
    """
    accepts callbacks with no data from the cipherwallet API; these calls verify the availability 
        of the URL and check that the secret API key is set properely
    """
    return ""


@bottle.post('/cipherwallet/<operation:re:signup|checkout|reg>')
def _callback_with_data(operation):
    """
    accepts callbacks containing data from the mobile app and places it temporarily in the 
        short term storage; from there, it will be picked up on the next poll and dispatched 
        to the form displayed by the browser
    """
    try:
        bottle.response.content_type = "application/json"
        return cipherwallet_lib.callback_with_data(operation, bottle.request.json)
    except CipherwalletError as cwex:
        bottle.abort(cwex.http_status, cwex.http_desc)
    except Exception:
        # most probably the request wasn't json
        bottle.abort(400, "Bad Request")


@bottle.get('/cipherwallet/<tag>/qr.png')
def _qr(tag):
    """
    AJAX request for cipherwallet QR code
    this action is typically invoked by your web page containing the form, thru the code 
        in cipherwallet.js, to obtain the image with the QR code to display
    it will return the image itself, with an 'image/png' content type, so you can use 
        the URL to this page as a 'src=...' attribute for the <img> tag
    """
    try:
        png, cookie = cipherwallet_lib.qr(tag)
        bottle.response.content_type = "image/png"
        bottle.response.set_cookie(
            "cwsession-" + tag, cookie, 
            expires=time.time() + CW_SESSION_TIMEOUT, path="/"
        )
        return png
    except CipherwalletError as cwex:
        bottle.abort(cwex.http_status, cwex.http_desc)


@bottle.get('/cipherwallet/<tag>')
def _poll(tag):
    """
    AJAX polling for the status of a page awaiting QR code scanning
    this action is typically invoked periodically by the browser, thru the code in cipherwallet.js, 
        in order to detect when / if the user scanned the QR code and transmitted the expected info
    """
    try:
        bottle.response.content_type = "application/json"
        return cipherwallet_lib.poll(tag, bottle.request.get_cookie("cwsession-" + tag))
    except CipherwalletError as cwex:
        bottle.abort(cwex.http_status, cwex.http_desc)


@bottle.post('/cipherwallet/<tag>')
def _set_qr_login_data(tag=None):
    """
    when the user presses (in the browser) the submit button on a signup form, the web app would 
        create the regular user record in the database. if the submit form was auto-filled as a 
        result of a cipherwallet QR code scan, then we should have cipherwallet registration data 
        in the short term storage, and we need to confirm to the cipherwallet API that the user 
        has been, in the end, signed up for the service. therefore, after completing the normal 
        signup procedure, the web page also calls this URL to confirm the cipherwallet registration
    """
    # we should have a cookie that gives out the session name
    try:
        bottle.response.content_type = "application/json"
        return cipherwallet_lib.set_qr_login_data(tag, 
            bottle.request.forms.get('user_id'),
            bottle.request.get_cookie("cwsession-" + tag)
        )
    except CipherwalletError as cwex:
        bottle.abort(cwex.http_status, cwex.http_desc)
        

