import os
import re
import time
import json
import random
import requests
import importlib
import traceback

from constants import *
import db_interface as db
import cqr_auth as cqr
import hooks

tmp_datastore = importlib.import_module("cipherwallet.tmpstore_{0}".format(TMP_DATASTORE), package=None)

class CipherwalletError(Exception):

    def __init__(self, http_status=500, http_desc="Internal Server Error"):
        Exception.__init__(self, "{0} {1}".format(str(http_status), http_desc))
        self.http_status = http_status
        self.http_desc = http_desc
        

def qr(tag):
    """
    called by an AJAX request for cipherwallet QR code
    this action is typically invoked by your web page containing the form, thru the code 
        in cipherwallet.js, to obtain the image with the QR code to display
    it will return the image itself, with an 'image/png' content type, so you can use 
        the URL to this page as a 'src=...' attribute for the <img> tag
    """

    # default timeout values, do not modify because they must stay in sync with the API
    DEFAULT_TTL = {
        OP_SIGNUP: 120,
        OP_LOGIN: 60,
        OP_CHECKOUT: 300,
        OP_REGISTRATION: 30,
    }

    # create an unique session identifier, 8 random characters, and postfix it with the QR code tag
    # the qr code tag is useful to distinguish multiple QR codes on the same page
    if re.compile("[a-zA-Z0-9.:_-]+").match(tag) is None:
        raise CipherwalletError(400, "Bad request")
    cw_session = "".join(random.choice(ALPHABET) for _ in range(8)) + "-" + tag
    
    # get the user data request template; templates for each type of request are pre-formatted 
    #    and stored in the constants file, in the qr_requests variable
    try:
        rq_def = qr_requests[tag]
    except Exception:
        raise CipherwalletError(501, "Not implemented")

    # set the time-to-live of the cipherwallet session in the temporary storage
    cw_session_ttl = rq_def.get('qr_ttl', DEFAULT_TTL[rq_def['operation']])
    if tmp_datastore.cw_session_data(cw_session, 'qr_expires', 1 + cw_session_ttl + int(time.time())) is None:
        raise CipherwalletError(500, "Internal server error")

    # for registration QR code requests, we also save the current user ID in the short term storage
    if rq_def['operation'] == OP_REGISTRATION:
        uid = hooks.get_user_id_for_current_session() # you MUST implement this function in hooks.py
        if uid is None:  
            raise CipherwalletError(401, "Unauthorized")
        else:
            tmp_datastore.cw_session_data(cw_session, 'user_id', uid);

    # prepare request to the API
    method = "POST";
    resource = "/{0}/{1}.png".format(tag, cw_session)
    request_params = {}
    if rq_def.get('qr_ttl'): request_params['ttl'] = rq_def['qr_ttl']
    if rq_def.get('callback_url'): request_params['push_url'] = rq_def['callback_url']
    if rq_def['operation'] not in [ OP_LOGIN, OP_REGISTRATION, ]:
        display = rq_def.get('display')
        if hasattr(display, '__call__'):
            request_params['display'] = display()
        elif type(display) == type(""): 
            request_params['display'] = rq_def['display']
        # should do the same thing for the service params

    # create CQR headers and the query string
    api_rq_headers = cqr.auth(
        CUSTOMER_ID, API_SECRET, method, resource, request_params or "", H_METHOD
    )
    # some extra headers we need
    api_rq_headers['Content-Type'] = "application/x-www-form-urlencoded";
    #api_rq_headers['Content-Length'] = len(request_params);

    # get the QR image from the API and send it right back to the browser
    api_rp = requests.post(API_URL + resource, headers=api_rq_headers, data=request_params)
    content = api_rp.content if api_rp.status_code == 200 \
        else open(os.path.dirname(os.path.realpath(__file__)) + "/1x1.png").read()
    return content, cw_session

def poll(tag, cw_session_id=None):
    """
    AJAX polling for the status of a page awaiting QR code scanning
    this action is typically invoked periodically by the browser, thru the code in cipherwallet.js, 
        in order to detect when / if the user scanned the QR code and transmitted the expected info
    """
    # we look for the presence of requested info associated with the data in the storage place
    session_cookie_name = "cwsession-" + tag
    if cw_session_id is None:
        raise CipherwalletError(410, "Offer expired")

    session_expires_on = tmp_datastore.cw_session_data(cw_session_id, 'qr_expires')
    if session_expires_on is None or session_expires_on < time.time():
        raise CipherwalletError(410, "Offer expired")

    user_data_json = tmp_datastore.get_user_data(cw_session_id)
    if user_data_json is not None:
        # QR scan data is present, submit it as AJAX response
        return user_data_json

    user_ident_json = tmp_datastore.get_user_ident(cw_session_id)
    if user_ident_json is not None:
        # this is user data for the login service
        # if the user signature was hashed properely, we can declare the user logged in
        user_id = cqr.authorize(json.loads(user_ident_json))
        if user_id is not None:
            # you MUST implement the function below in hooks.py
            return hooks.authorize_session_for_user(user_id) or { 'error': "User not registered" }
        else:
            raise CipherwalletError(401, "Unauthorized")

    time.sleep(POLL_DELAY)
    raise CipherwalletError(202, "Waiting For User")


def set_qr_login_data(tag, user_id, cw_session_id=None):
    """
    when the user presses (in the browser) the submit button on a signup form, the web app would 
        create the regular user record in the database. if the submit form was auto-filled as a 
        result of a cipherwallet QR code scan, then we should have cipherwallet registration data 
        in the short term storage, and we need to confirm to the cipherwallet API that the user 
        has been, in the end, signed up for the service. therefore, after completing the normal 
        signup procedure, the web page also calls this URL to confirm the cipherwallet registration
    """
    # we should have a cookie that gives out the session name
    if cw_session_id is None:
        raise CipherwalletError(410, "Session Timeout")
    # we should also have a session variables set corresponding to this cookie
    # (a cipherwallet session lives in the customer's short term storage facility)
    reg_data = tmp_datastore.get_signup_registration_for_session(cw_session_id)
    if reg_data is None:
        raise CipherwalletError(410, "Session Timeout")
    
    # call the cipherwallet API to confirm the registration
    method = "PUT"
    resource = "/reg/{0}".format(reg_data['registration'])
    api_rq_headers = cqr.auth(CUSTOMER_ID, API_SECRET, method, resource, "", H_METHOD)
    api_rp = requests.put(API_URL + resource, headers=api_rq_headers)
    if api_rp.status_code == 200:
        # confirmed with the cipherwallet API, we just have to save the credentials 
        #    in the permanent storage now
        if db.set_user_data_for_qr_login(user_id, reg_data) is None:
            raise CipherwalletError(500, "Server Error")
        else:
            del reg_data['registration']
            return reg_data
    else:
        raise CipherwalletError(410, "Session Timeout") # this is not accurate, just a best guess...
        

def callback_with_data_login(user_ident):
    """
    login callback requests come from the cipherwallet API server and they're signed with
       our own credentials (as opposed to the other requests, that come unsigned, directly  
       from the mobile app)
    """
    # save all variables received (hopefully user credentials) in the short term storage
    # we will authenticate the user only when these variables are pulled from the storage, 
    #    by the polling procedure executed in the browser
    session = user_ident['session']
    del user_ident['session']
    if tmp_datastore.set_user_ident(session, json.dumps(user_ident)) is None:
        raise CipherwalletError(500, "Server Error")

    return ""
    
def callback_with_data(operation, rq):
    """
    accepts callbacks containing data from the mobile app and places it temporarily in the 
        short term storage; from there, it will be picked up on the next poll and dispatched 
        to the form displayed by the browser
    """

    try:
        session = rq['session']
    except Exception:
        raise CipherwalletError(400, "Bad Request")

    reg_meta = rq.get('reg_meta')
    if reg_meta:
        reg_tag = reg_meta['tag']

    rp = {}
    # saved data should not include the meta information, the browser doesnt 
    #    need to see it
    if operation == OP_REGISTRATION:
        # get user ID for the browser session that initiated the registration
        user_id = tmp_datastore.cw_session_data(session, 'user_id');
        if user_id is None:
            raise CipherwalletError(410, "Offer Expired")
        # confirm registration by calling the cipherwallet API
        method = "PUT"
        resource = "/reg/{0}".format(reg_tag)
        api_rq_headers = cqr.auth(CUSTOMER_ID, API_SECRET, method, resource, "", H_METHOD)
        api_rp = requests.put(API_URL + resource, headers=api_rq_headers)
        if api_rp.status_code == 200:
            # create and save a set of new cipherwallet credentials in permanent storage
            cw_user_data = db.create_cipherwallet_user(reg_tag)
            if db.set_user_data_for_qr_login(user_id, cw_user_data):
                del cw_user_data['registration']
                rp = cw_user_data
            else:
                raise CipherwalletError(500, "Server Error")
        else:
            # cipherwallet API didnt accept our reg confirmation
            raise CipherwalletError(api_rp.status_code, api_rp.reason)
            
        # silence up the browser poll (rp only contains elements if cipherwallet credentials
        #    are now safe in the house)
        tmp_datastore.set_user_data(session, { 'registration': "success" if rp else "failed" })

    elif operation == OP_SIGNUP:
        rp['credentials'] = tmp_datastore.set_signup_registration_for_session(
            session, reg_tag, int(reg_meta['complete_timer'])
        )

    if operation != OP_REGISTRATION:
        # store the request payload (i.e. data from the mobile app) in the temporary storage, 
        #    so that the next poll will find it
        if tmp_datastore.set_user_data(session, rq['user_data']) is None:
            raise CipherwalletError(500, "Server Error")

    # we're in the 200 OK territory already, but if possible, build a decent response for 
    #    the mobile app
    try:
        confirm = qr_requests[session.split('-', 1)[1]]['confirm']
        if hasattr(confirm, '__call__'):
            rp['confirm'] = confirm()
        elif type(confirm) == type("") or type(confirm) == type({}): 
            rp['confirm'] = confirm
    except Exception:
        pass
        
    return rp

