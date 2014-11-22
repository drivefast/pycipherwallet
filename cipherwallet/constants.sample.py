
# your customer ID and API secret key, as set on https://cipherwallet.com/dashboard.html
CUSTOMER_ID = "YOUR_CIPHERWALLET_CUSTOMER_ID"
API_SECRET = "YOUR_CIPHERWALLET_API_SECRET"

# API location
API_URL = "http://api.cqr.io"
# preferred hashing method to use on message encryption: md5, sha1, sha256 or sha512
H_METHOD = "sha256"
# how long (in seconds) do we delay a "still waiting for user data" poll response
POLL_DELAY = 2
# service id, always "cipherwallet"
SERVICE_ID = "cipherwallet"
# an alphabet with characters used to generate random strings
ALPHABET = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_@"

# depending on your temporary datastore of choice, uncomment one of the following sections
# and adjust the settings accordingly
#   memcached:
#TMP_DATASTORE = 'memcached'; MCD_CONFIG = ['localhost:11211', 'localhost:11212']
#   redis:
#TMP_DATASTORE = 'redis'; REDIS_HOST = "localhost"; REDIS_PORT = 6379; REDIS_DB = 0
#   plaintext files:
#TMP_DATASTORE = 'sessionfiles'; TMPSTORE_DIR = "/path/to/session/directory/"
# how long are we supposed to retain the information about a QR scanning session
# the value should be slightly larger than the maximum QR time-to-live that you use
CW_SESSION_TIMEOUT = 610

# for logins via QR code scanning, you need to provide access to a SQL database where your users 
#     information is stored (we're assuming here you are using a SQL database). cipherwallet only 
#     needs read/write access to a table it creates (cw_logins), so feel free to restrict as needed. 
# we use the core sqlalchemy to create an uniform database access layer; for more details about 
#     sqlalchemy see http://docs.sqlalchemy.org/en/rel_0_8/core/connections.html
# to set the database connection, uncomment and configure one of the lines below
#DB_CONNECTION_STRING = "postgresql+psycopg2://{0}:{1}@server_host:port/database_name"
#DB_CONNECTION_STRING = "mysql+mysqldb://{0}:{1}@server_host:port/database_name"
#DB_CONNECTION_STRING = "oracle+cx_oracle://{0}:{1}@tnsname"
#DB_CONNECTION_STRING = "mssql+pymssql://{0}:{1}@server_host:port/database_name"
#DB_CONNECTION_STRING = "sqlite:////path/to/your/dbfile.db"
DB_CONNECTION_USERNAME = "god"
DB_CONNECTION_PASSWORD = "zzyzx"

# in your database, YOU MUST create a table called 'cw_logins', which will have a 1-1 relationship with
#    your users table; something like this (but check the correct syntax for on your SQL server type):
""" 
CREATE TABLE cw_logins (
    user_id VARCHAR(...) PRIMARY KEY,  -- or whatever type your unique user ID is
    cw_id VARCHAR(20),
    secret VARCHAR(128),
    reg_tag CHAR(),                    -- it's an UUID
    hash_method VARCHAR(8),            -- can be md5, sha1, sha256
    created INTEGER
);
"""
# 'user_id' is the unique identifier of an user in your main users table, and should be declared as
#    a primary key and foreign index in your users table; if your SQL server supports it, cascade 
#    the changes and deletes
# 'cw_id' is the cipherwallet ID assigned to the user
# 'secret' is the secret encryption key assigned to the user; YOU MUST ENCRYPT THIS!
# 'reg_tag' is an identifier that the cipherwallet API maintains; use this identifier when you need 
#    to remove an user's registration. it is an UUID, so you may use a more appropriate data type if 
#    your database supports one
# 'hash_method' is the hash type the user will hash their user credentials with, on QR scan logins; 
#    can be md5, sha1, sha256
# 'created' is the date when the record was created, epoch format (feel free to change this field type 
#    to a date/time field, if you find it more convenient)
# you should also create an index on cw_id, it will help during your queries

# your user's secret keys must be stored in an encrypted form in the cw_logins table
# we use an AES-256 encryption algorithm for that, with the encryption key below
# the encryption itself comes in play in db-interface.lib.php
# the AES-256 encryption key must be 32-bytes long; example:
#CW_SECRET_ENC_KEY = "000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"
# hint: to easily generate a 32-byte encryption key like needed here, just generate 2 random UUIDs, 
#    concatenate them, and remove the formatting dashes

OP_SIGNUP = "signup"
OP_LOGIN = "login"
OP_CHECKOUT = "checkout"
OP_REGISTRATION = "reg"

# provide a service descriptor entry in this map for every cipherwallet QR code you are using
# on each entry, you provide:
#    - 'operation': the operation type, one of the OP_* constants above 
#    - 'qr_ttl': a time-to-live for the QR code, in seconds
#    - 'callback_url': the URL used by the mobile app to transfer the data back to your web app
#    - 'display': a message that gets displayed at the top of the screen, in the mobile app, when  
#          the user is asked to select the data they want to send; you may provide a string, or 
#          a function that returns a string (for example, you can customize the message for a 
#          checkout service, such that it mentions the amount to be charged to the credit card)
#    - 'confirmation': a message to be displayed as a popup-box in the mobile app, that informs if 
#          the last QR code scanning and data transfer operations was successful or not; you may  
#          provide a string, or a function that returns a string
# the service descriptor parameters specified here will override the ones pre-programmed with the 
#    the dashboard page
# the 'operation' must be specified; 'qr_ttl' has default and max values for each type of service; 
#    'display' is only effective for the signup and checkout services; and 'confirm' is only 
#    effective for signup, checkout and registration services
# here is an example that contains 4 services: a signup, a registration, a login and a checkout
# commented out values indicate default values
qr_requests = {
    'signup-form-qr': {
        'operation': OP_SIGNUP, 
        'qr_ttl': 300, 
        'display': "Simulate you are signing up for a new account at\\your.website.com",
        'confirm': "Your signup data has been submitted.",
    },
    'login-form-qr': { 
        'operation': OP_LOGIN, 
#       'qr_ttl': 60, 
#       'callback_url': "https://thiswebsite.com/cipherwallet/login",
    },
    'checkout-form-qr': {
        'operation': OP_CHECKOUT, 
#       'qr_ttl': 120, 
#       'callback_url': "https://thiswebsite.com/php-cipherwallet/checkout",
#       'display': get_message_for_cart_value(),   # implement this function in hooks.py
        'confirm': "Thank you for your purchase.",
    },
    'reg-qr': { 
        'operation': OP_REGISTRATION, 
#       'qr_ttl': 30, 
#       'callback_url': "https://thiswebsite.com/cipherwallet/login",
        'confirm': {
            'title': "cipherwallet registration",
            'message': "Thank you. You may now use cipherwallet to log in to this website.",
        },
    },
}
