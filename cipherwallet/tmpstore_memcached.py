import random
import json
import pylibmc

from constants import MCD_CONFIG, CW_SESSION_TIMEOUT, ALPHABET, H_METHOD
import db_interface as db

####  temporary storage facility using memcached  ####

K_NONCE = "CQR_NONCE_{0}_{1}"       # + user, nonce
K_CW_SESSION = "CW_SESSION_{0}"     # + cipherwallet session id
K_USER_DATA = "CW_USER_DATA_{0}"    # + cw session id
K_SIGNUP_REG  = "CW_SIGNUP_REG_{0}" # + cw session id
K_USER_IDENT = "CW_USERIDENT_{0}"   # + cw session id

mcd = pylibmc.Client(MCD_CONFIG)   # configuration comes from __init__.py

def is_nonce_valid(arg1, arg2, ttl):
    """
    adds a nonce with a limited time-to-live
    failure means that a nonce with the same key already exists
    """
    return mcd.add(K_NONCE.format(arg1, arg2), 0, time=ttl)

def cw_session_data(session_id, var, value=None):
    """
    cipherwallet session variables managed in the temp store
    """
    json_s = mcd.get(K_CW_SESSION.format(session_id))
    s = json.loads(json_s) if json_s is not None else None
    if value is None:
        return s.get(var) if s is not None else None
    else:
        # session exist, set the session variable and re-save
        if s is None: s = {}
        s[var] = value
        return value if mcd.set(K_CW_SESSION.format(session_id), json.dumps(s), time=CW_SESSION_TIMEOUT) else None
    

def set_user_data(session_id, user_data):
    """
    this function temporarily stores data transmitted by user, when POSTed 
       by the user device; the data is then picked up by the page ajax
       polling mechanism
    """
    return session_id if mcd.set(K_USER_DATA.format(session_id), json.dumps(user_data), time=30) else None


def get_user_data(session_id):
    """
    the complement of the above: gets called by the web page polling mechanism to 
    retrieve data transmitted (POSTed) by the user's device, after scanning a QR code
    """
    return mcd.get(K_USER_DATA.format(session_id))


def set_signup_registration_for_session(session_id, registration, complete_duration):
    """
    this function is called when the user's mobile app uploaded signup data, 
       in addition to the set_user_data() above
    it returns a new login credentials record
    """
    creds = db.create_cipherwallet_user(registration)
    if mcd.set(K_SIGNUP_REG.format(session_id), json.dumps(creds), time=complete_duration):
        del creds['registration']
        return creds
    else:
        return None
	    

def get_signup_registration_for_session(session_id):
    """
    when the user completes the signup process (by submitting the data on the
       signup page), we need to call this function to retrieve the registration
       confirmation tag that we saved with the function above
    """
    try:
        return json.loads(mcd.get(K_SIGNUP_REG.format(session_id)))
    except Exception:
        return None


def set_user_ident(session_id, user_ident):
    """
    on QR login, the push web service invoked by the cipherwallet API calls this function 
       to temporarily store user identification data until it gets polled by the ajax 
       functions on the login page
    """
    return session_id if mcd.set(K_USER_IDENT.format(session_id), user_ident, time=30) else None


def get_user_ident(session_id):
    """
    on QR login push, this function gets called by the login page poll mechanism 
       to retrieve user identification data posted with the function above
    """
    return mcd.get(K_USER_IDENT.format(session_id))
