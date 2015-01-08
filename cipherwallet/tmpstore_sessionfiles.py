import random
import json
import time
import glob
import os

from constants import TMPSTORE_DIR, CW_SESSION_TIMEOUT, ALPHABET, H_METHOD
import db_interface as db

####  temporary storage facility using plaintext files  ####
"""
Obviously, this is NOT the ideal alternative of implementing a temporary storage.

Some files become obsolete after a few seconds or minutes. To indicate the validity  
of the files, as soon as we create them, we change the last-modified date to a 
future date when the data is considered stale or invalid. You HAVE TO run a cron job 
that deletes the obsoleted files, otherwise your directory will keep filling up.
use the following command in a crontab that executes every hour:
    find /path/to/sessions/directory -type f -mmin +60 -delete
"""

K_NONCE = "CQR_NONCE_{0}_{1}"       # + user, nonce
K_CW_SESSION = "CW_SESSION_{0}"     # + cipherwallet session id
K_USER_DATA = "CW_USER_DATA_{0}"    # + cw session id
K_SIGNUP_REG  = "CW_SIGNUP_REG_{0}" # + cw session id
K_USER_IDENT = "CW_USERIDENT_{0}"   # + cw session id

def __file_write_with_expiration(fname, content, ttl):
    try:
        fh = open(TMPSTORE_DIR + fname, "w")
        fh.write(content)
        fh.close()
        # set the file's mtime to be the expiration date
        os.utime(TMPSTORE_DIR + fname, (time.time(), ttl + time.time()))
        return True
    except:
        return False

def __file_read_if_not_expired(fname):
    try:
        # make sure the data is still valid (not expired)
        if os.stat(TMPSTORE_DIR + fname).st_mtime < time.time():
            return None
        # seems ok so far, return the file content
        fh = open(TMPSTORE_DIR + fname, "r")
        content = fh.read()
        fh.close()
        return content
    except:
        return None


def is_nonce_valid(arg1, arg2, ttl):
    """
    create a file representing a nonce 
    if the file already exists, it means that the nonce attempts to being reused
    """
    if TMPSTORE_DIR + K_NONCE.format(arg1, arg2) in os.listdir(TMPSTORE_DIR):
        # we assume that the ttl is just approximatively OK, although the file 
        # may linger around for another few minutes after its expiration
        return False
    return __file_write_with_expiration(K_NONCE.format(arg1, arg2), ".", ttl)
    

def cw_session_data(session_id, var, value=None):
    """
    cipherwallet session variables managed in the temp store
    """
    json_s = __file_read_if_not_expired(K_CW_SESSION.format(session_id))
    s = json.loads(json_s) if json_s is not None else None
    if value is None:
        return s.get(var) if s is not None else None
    else:
        # session exist, set the session variable and re-save
        if s is None: s = {}
        s[var] = value
        if __file_write_with_expiration(K_CW_SESSION.format(session_id), json.dumps(s), CW_SESSION_TIMEOUT):
            return value 
        else: 
            return None
    

def set_user_data(session_id, user_data):
    """
    this function temporarily stores data transmitted by user, when POSTed 
       by the user device; the data is then picked up by the page ajax
       polling mechanism
    """
    
    if __file_write_with_expiration(K_USER_DATA.format(session_id), json.dumps(user_data), 30):
        return session_id 
    else:
        return None


def get_user_data(session_id):
    """
    the complement of the above: gets called by the web page polling mechanism to 
    retrieve data transmitted (POSTed) by the user's device, after scanning a QR code
    """
    return __file_read_if_not_expired(K_USER_DATA.format(session_id))


def set_signup_registration_for_session(session_id, registration, complete_duration):
    """
    this function is called when the user's mobile app uploaded signup data, 
       in addition to the set_user_data() above
    it returns a new login credentials record
    """
    creds = db.create_cipherwallet_user(registration)
    if __file_write_with_expiration(K_SIGNUP_REG.format(session_id), json.dumps(creds), complete_duration):
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
        return json.loads(__file_read_if_not_expired(K_SIGNUP_REG.format(session_id)))
    except Exception:
        return None


def set_user_ident(session_id, user_ident):
    """
    on QR login, the push web service invoked by the cipherwallet API calls this function 
       to temporarily store user identification data until it gets polled by the ajax 
       functions on the login page
    """
    if __file_write_with_expiration(K_USER_IDENT.format(session_id), user_ident, 30):
        return session_id
    else:
        return None


def get_user_ident(session_id):
    """
    on QR login push, this function gets called by the login page poll mechanism 
       to retrieve user identification data posted with the function above
    """
    return __file_read_if_not_expired(K_USER_IDENT.format(session_id))
