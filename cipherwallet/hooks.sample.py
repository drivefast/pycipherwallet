import sqlalchemy
from sqlalchemy.sql import text as sql_statement


# you will need to implement this when you use the registration page
def get_user_id_for_current_session():
    """
    this function is supposed to return the user id of the currently logged-in user
        or None if no active log in. you would probably obtain this information from
        your session variables.
    """
    return "user@yoursite.com"
    
    
# you will need to implement this when your signup page includes registration
#    capabilities for the QR login service
def authorize_session_for_user(user_id):
    """
    called by the login AJAX poll function if QR login was successful, in order to 
       return the user info needed by your web application
    this function should perform the same operations as your regular login (typically
       set the session variables for the logged-in user), and is expected to return 
       a dictionary with whatever you need to forward to the browser, in response to
       the AJAX poll
    """
    try:
        db_engine = sqlalchemy.create_engine('sqlite:///your.db', echo=True)
        db = db_engine.connect()
        rs = db.execute(
            sql_statement("SELECT email, firstname FROM users WHERE email = :user_id;"),
            user_id=user_id
        ).fetchone()
        return {
            'email': rs[0],
            'firstname': rs[1],
        }
    except Exception:
        return None
