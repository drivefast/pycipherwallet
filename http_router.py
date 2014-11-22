import time
import bottle
import bcrypt
import sqlalchemy
from sqlalchemy.sql import text as sql_statement

import cipherwallet.api_router

ROOT = '/path/to/pycipherwallet'

@bottle.route('/<folder:re:css>/<filename:re:.*\.css>')
@bottle.route('/<folder:re:js>/<filename:re:.*\.js>')
@bottle.route('/<folder:re:img>/<filename:re:.*\.(png|jpg|ico)>')
def static_css(folder, filename):
    return bottle.static_file(folder + "/" + filename, root=ROOT)

@bottle.route('/<filename:re:.*\.html>')
def static(filename):
    return bottle.static_file(filename, root=ROOT)

@bottle.route('/cipherwallet/cipherwallet.js')
def cipherwalletjs():
    return bottle.static_file("cipherwallet/cipherwallet.js", root=ROOT)

@bottle.post('/user/<user_id>')
def create_user(user_id):
    """
    This sample web service is created to look similar to what is called with a POST method 
        by your signup web page when the user presses the "create user" submit button. Form 
        data is POSTed from the signup page.
    If data signup page data was loaded from the mobile app (QR code scanning), we also 
        register the user to use cipherwallet (QR code scanning) for the logins
    This should mostly be *your* procedure to create an user record, and should work regardless
        of whether cipherwallet is active or not
    """
    try:
        # connect to the database (normally, the cipherwallet sdk will connect to the same database)
        # we use a sqlite database here as an example
        db_engine = sqlalchemy.create_engine('sqlite:///your.db', echo=True)
        db = db_engine.connect()
    except:
        bottle.abort(503, "Service Unavailable")

    # make sure we have valid data
    firstname = bottle.request.POST.get('firstname', "").strip()
    password1 = bottle.request.POST.get('password1', "").strip()
    if (
        user_id is None or len(user_id) < 5 or len(user_id) > 64 or
        len(firstname) < 1 or len(firstname) > 64 or
        len(password1) < 5 or len(password1) > 64 
    ):
        bottle.abort(400, "Bad Request")
        
    # encrypt the password (you DO store the passwords in encrypted form, dont you)
    password = bcrypt.hashpw(password1, bcrypt.gensalt())

    # if the user already exists, delete it
    # (obviously, you wouldn't do that on your real website)
    db.execute(
        sql_statement("DELETE FROM users WHERE email = :user_id;"),
        user_id=user_id
    )
    # now add the user
    ret = db.execute(
        sql_statement(
            "INSERT INTO users(firstname, email, password, created_on) " +
            "VALUES (:firstname, :email, :password, :now);"
        ),
        firstname=firstname,
        email=user_id,
        password=password,
        now=time.time()
    )
    if ret.rowcount:
        return {
            'firstname': firstname,
            'email': user_id,
        }
    else:
        bottle.abort(503, "Service Unavailable")


if __name__ == "__main__":
    bottle.debug(True)
    bottle.run(host="0.0.0.0", port=8080, reloader=True)
