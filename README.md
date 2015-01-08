Cipherwallet SDK for Python
=
Cipherwallet is a digital wallet mobile application. Users store personal data, like name, addresses, phone numbers or credit cards. Websites that display a specially crafted QR code, obtained from the cipherwallet API, can easily and securely collect user's data from the mobile app. For more details, see the [cipherwallet] product official site. A completely functional [demo] is also available.

This SDK provides a set of functions that can be used to integrate cipherwallet with your website - practically it simplifies the access to the cipherwallet API. We opted for a very basic, easy to understand implementation, that relies on a minimum number of dependencies.

Most of the time that you have to spend will be about:
  - understanding the information exchange data flow;
  - setting the constants in ```constants.py```;
  - implementing a few very basic functions in the ```hooks.py``` module;
  - wiring up the sdk calls and the results returned in your web pages.
We also have a few sample implementations to get you going faster.

TL;DR
=
  - Clone the project. The SDK files will land in the ```/cipherwallet``` directory - make sure your website doesn't offer direct access to the files in there.
  - Copy the ```constants.sample.py``` and ```hooks.sample.py``` files as ```constants.py``` and ```hooks.py```. Make the settings that you need in the new files. Your customer ID and secret API key are available on the cipherwallet [dashboard]. 
  - If you are planning to use cipherwallet login services, create an extra table in your database, to store the user properties needed by cipherwallet. (See how at the top of the ```db_interface.py``` module.)
  - Add ```<div>``` elements on your web pages, where the QR codes are supposed to be be displayed. Make the pages load the javascript code in ```cipherwallet/cipherwallet.js```.
  - Use the customer [dashboard] to program what the users will see on their phone when they scan the QR codes, and the names of the parameters to be passed to your web application. Make sure the callback scripts ```/cipherwallet/*``` URLs are callable from the internet, and set them appropriately for the services you define on the [dashboard].
  - In your web pages javascript code, instantiate a Cipherwallet object and implement its callback functions. Typically these functions distribute user's data to the elements on your web page, or deal with error conditions.

For details, keep on reading.

Terraforming
=
Install the SDK using pip:

    pip install cipherwallet

If you want to fiddle around with the code, clone the cipherwallet sdk project instead:

    git clone https://github.com/drivefast/pycipherwallet.git

and run the setup script:

    python setup.py develop

The files located directly under ```pycipherwallet/example/``` are a sample website, powered by a [bottle] module. The actual cipherwallet SDK files end up in the ```pycipherwallet/cipherwallet/``` directory. 

The SDK comes with two sample files: ```constants.sample.py``` and ```hooks.sample.py```. Duplicate these files but remove the word ```sample``` from their name, such that their names become ```constants.py``` and ```hooks.py```. Remember to make sure that the content of these files is NOT available to the outside world, as they will end up storing sensitive information. Carefully mask them out in your .htaccess file (if using apache), issue a 404 Not Found error when they're invoked directly in nginx - you get the point.

```constants.py``` is a generic constants file, where you set the privileges to access the cipherwallet API, connections to your database and backend systems, etc. You will also find templates that describe the services execution. We will talk about them in detail later.

If you don't have a cipherwallet account yet, now it would be a good time to create it. The free evaluation tier has all the features of a paid account, and we encourage you to use this tier during the initial development phase. When you log in to the cipherwallet website, you will be taken directly to the [dashboard] page. In the _API Settings_ section, you will find your customer ID and a secret key. Copy these 2 values in the `CUSTOMER_ID` and `API_SECRET` variables in  ```constants.py```.

Your application will need to store temporarily, for short periods of time, data received from the mobile app, in transit to the web page displayed by the browser. We provided libraries that can work with memcached, redis, mongoDB, or plaintext files backends. (Obviously, the plaintext files backend is not recommended for production systems.) Uncomment one of the lines that define the ```TMP_DATASTORE``` constant, and provide connection information as necessary. 


Checkout services
=
The SDK offers all the tools to generate the cipherwallet API request for the QR code, display it, poll the status of data receipt, and act on a poll returning data. Detailed description on how the checkout service works can be found in the [checkout service documentation].

Starting with the checkout page on your website, make sure you have an ID assigned to every input field in the html form. Create the service in the [dashboard] page, indicate you will be using the python SDK, and configure all the settings and parameters you need.

In the javascript code of your checkout web page, load the ```cipherwallet/cipherwallet.js``` module:

    <script src="cipherwallet/cipherwallet.js" type="text/javascript"></script> 

Find a place to display the QR code, and create a ```<div>``` container for it. Instantiate a ```Cipherwallet``` object, and provide the initialization variables:
- ```qrContainerID``` = the id of your ```<div>``` html container we just mentioned
- ```detailsURL``` = where the user's browser gets redirected when they click on the QR code, or on the "What's This" hyperlink underneath
- ```onSuccess``` = a function that executes when a poll operation returns a dataset from your web server. The function receives as argument the data object itself. You may use this function to write the data received from the mobile app in the corresponding fields of the checkout form.
- ```onFailure``` = a function that executes when the poll operation returns an http status in the 400 or 500 range. The function receives as argument the http status from the poll.
You may peek at our [demo] website, or on the [dashboard] page itself, for implementation samples.

The checkout service doesn't require any connection to your database backend, so you can safely leave all the alternative definitions of the ```DB_CONNECTION_*``` variables in ```constants.py``` commented out.

However, you do need to add an entry in the ```qr_requests``` dictionary variable. The entry needs to have the same name (key) as in the [dashboard] page, and needs to be itself a dictionary with the following elements:
- ```operation``` = operation type, in this case ```OP_CHECKOUT```
- ```qr_ttl``` = (optional) how long the QR code is active, in seconds. For checkout QR codes, the default value is 300s (5 minutes), maximum is 600s (10 minutes)
- ```display``` = (optional) the text to display at the top of the screen in the mobile application, when requesting the data. This text will override the corresponding service setting in the [dashboard] page. You may use a constant string, or a function that returns a string (for example, a function that looks up the total value of the items in the cart, and returns a string like "We will charge $27.84 for the 3 items in your card"). It is a good practice to implement this function in ```hooks.py```.
- ```callback_url``` = (optional) the URL that will handle the data received from the mobile app. It will override the corresponding service setting in the [dashboard] page. For this SDK, the URL is expected to be ```https://your.website.com/cipherwallet/checkout```. Note that a warning message will be automatically displayed to the user, if the URL is not an https scheme.
- ```rq_params``` = (optional) (not implemented)
- ```confirm``` = (optional) a text that will be displayed in the mobile app, as a result of transmitting the data, indicating the transmission success. You may provide a string, or a function that returns a string (for example a function that checks the credit card type and returns either "Thank you for your payment" or "We're sorry, we only accept VISA or Mastercard").

Make sure your callback URL ```https://your.website.com/cipherwallet/checkout``` is available. Also, make sure it is a secure http (i.e. starts with https://): the credit card information is sensitive, and needs to travel between the mobile app and your web app in an encrypted form. The mobile app user will be notified if you are not using secure http.


Signup services
=
The signup process starts very much similar with the checkout service, but some more work needs to be done in order to register the user for cipherwallet logins.

Similar to what you made for the checkout service, go ahead and provide a ```<div>``` tag on your signup web page, where the QR code will be displayed. Import the ```cipherwallet/cipherwallet.js``` module in your page, and create an instance of the ```Cipherwallet``` object, with all the parameters and functions needed. Create a service descriptor in the ```qr_requests``` variable, with the same name (key) you used in the [dashboard]. For this service, provide the data like you did for the checkout service (use ```OP_SIGNUP``` for the ```operation``` key though).

Here comes the (slightly) trickier part. As described in the [signup service documentation], for completed signups, you will need to store the cipherwallet login credentials for your user, along with the rest of the user data. Instead of messing up with your users table, and asking you to add some fields used by the cipherwallet app, we opted to ask you to create a separate table, called ```cw_logins```, and maintain a 1-on-1 relationship with your existing users table. If you use almost any SQL database on your backend, the cipherwallet logins table would look like this:

    CREATE TABLE cw_logins (
        user_id VARCHAR(...) PRIMARY KEY,  -- or whatever type your unique user ID is
        cw_id VARCHAR(20),
        secret VARCHAR(128),
        reg_tag CHAR(...),                 -- it's an UUID
        hash_method VARCHAR(8),            -- can be md5, sha1, sha256
        created INTEGER
    );

The ```user_id``` field is both a primary key, and a foreign key in your existing users table. Pick the appropriate type for it, create the relationship, and make sure that you have a procedure to remove the ```cw_logins``` record when the corresponding record your the regular users table is removed. The ```reg_tag``` field needs to be used to remove the user's cipherwallet login privileges: if you delete the cipherwallet user record, you should also call the cipherwallet API to invalidate their login capabilities. The ```hash_method``` will take whatever value you have set in the ```H_METHOD``` constant at the time the record is created.

The SDK also needs to access your database, to maintain the ```cw_logins``` table. We're using [sqlalchemy] to access the database, it should work for most types of SQL backends. Uncomment the ```DB_CONNECTION_STRING``` variable in ```constants.py``` that matches your database type, fill in the correct values, and provide the privileges in ```DB_CONNECTION_USERNAME``` and ```DB_CONNECTION_PASSWORD```.

There is one more thing to do. In a successful scenario, an user that scans the signup QR code will transfer data from their mobile app into the signup form on your web page, and eventually will press the "Submit" button. At that time, we assume your web app creates the user record in the database, but it should also create the corresponding record in ```cw_logins```. As such, together with whatever action is performed on the Submit button, you should also call the ```registerForQRLogin()``` method of the ```Cipherwallet``` object created for your page. The ```registerForQRLogin()``` function takes 2 parameters - the user ID that you assigned to the new user, and a javascript callback function that executes at the end of the cipherwallet registration operation. 


Login Services
=
If you had the chance to read the [login service documentation], you noticed that the login service doesn't need an user interface. Also, since you probably programmed a signup or registration service already, you probably have the necessary database access settings in place.

You start with the usual - declare the service in your [dashboard] page, and indicate the callback URL, which is probably ```https://yourwebsite.com/cipherwallet/login```. On your login web page, provide a ```<div>``` tag where the QR code will be displayed. Import the ```cipherwallet/cipherwallet.js``` module in your page, and create an instance of the ```Cipherwallet``` object, with all the parameters and functions needed. Create a service descriptor in the ```qr_requests``` variable, with the same name as the one you used in the [dashboard], and provide an ```OP_LOGIN``` value for the ```operation``` key. Optionally, you may override the time-to-live for the QR code (default is 120 seconds, maximum is 1200 seconds), or the callback URL where the user credentials are transmitted. You don't need to program display or data-entry parameters.

When the user scans the QR code, your web app will receive a POST http request that contains the user credentials. As opposed how other services transfer the data between the mobile app and the web app, this request will not come directly from the mobile app. Instead, it will come from one of the cipherwallet servers, and will be signed with the same credentials that your website uses to sign its requests to the cipherwallet API. The ```cipherwallet/login``` handler will take care of authenticating the cipherwallet server, and will place the user credentials in the short term storage.

On the next poll coming from the user's browser, the user credentials will be retrieved and evaluated. If they verify successfully, the SDK will call the ```authorize_session_for_user()``` in ```hooks.py```, with the user unique identifier as a parameter. You must provide an implementation for this function, which would typically declare the browser session as authorized, and would do whatever your backend process does with the session variables when an user logs in the classic way (username and password). The ```onSuccess()``` function from your javascript ```Cipherwallet``` object may be used to advance (refer) the user browser to the first page that you normally show to an user that just logged in.


Registration Services
=
Even though they probably opted for cipherwallet login services at the time they signed up, there may still be cases when your users may need to register, or re-register, at a later time. This is what the registration service is for.

To implement, create the service on the [dashboard] page. The registration service doesn't generate UI artifacts in the mobile app, so the callback URL is the only thing you need to indicate, and that is most probably ```https://yourwebsite.com/cipherwallet/reg```. 

On your website, choose the web page where you want to display the QR code for registration. It must be a web page that is accessible only _after_ the user logged in - like the page they use to change their password. On the page, create the ```<div>``` tag where the QR code will be displayed, load the ```cipherwallet/cipherwallet.js``` module, and instantiate a ```Cipherwallet``` object. There are no special requirements for the implementation of the ```onSuccess()``` and ```onFailure()``` functions.

If you didn't provide access to your database from inside the cipherwallet SDK (i.e. you didn't assign values to the DSN, username and password constants in  ```constants.py```), it's time to do that. Also create the ```cw-logins``` table in your database. See the signup service description above for more details on how to do this.

Create a service descriptor in the ```qr_requests``` variable, with the same name as the one you used in the [dashboard], and provide an ```OP_REGISTRATION``` value for the ```operation``` key. You may override the time-to-live for the QR code (default is 30 seconds, maximum is 60 seconds), or the callback URL where you expect the mobile app to send a request.

When the user scans the QR code, you will get a request on ```cipherwallet/reg``` (unless you changed it to something else). The code in that script will take care of communicating with the cipherwallet API, creating the credentials set, and sending the response back to the mobile app, but at one point it will need to obtain the unique user identifier for the login user. For that, you need to provide an implementation for the ```get_user_id_for_current_session()``` function in ```hooks.py``


Canceling And Refreshing A Registration
=
To cancel a registration, either send a request to the ```cipherwallet/deregister``` with the user ID you need to deregister, or call the ```remove_qr_login_data()``` function in ```cipherwallet_lib.py``` directly.

The cipherwallet server may remove the registrations that were inactive for more than 6 months. To prevent this, call the ```refresh_qr_login_data()``` function from ```cipherwallet_lib.py``` with the user ID as parameter.


This is it!
=


  [cipherwallet]: http://www.cipherwallet.com/
  [demo]: http://demo.cipherwallet.com/
  [account management page]: http://www.cipherwallet.com/home.html
  [landing page]: http://www.cipherwallet.com/user.html
  [API documentation]: http://www.cipherwallet.com/cust_doc.html
  [checkout service documentation]: http://www.cipherwallet.com/cust_doc.html#checkout_service
  [signup service documentation]: http://www.cipherwallet.com/cust_doc.html#signup_service
  [login service documentation]: http://www.cipherwallet.com/cust_doc.html#login_service
  [registration service documentation]: http://www.cipherwallet.com/cust_doc.html#registration_service
  [bottle]: http://bottlepy.org/docs/dev/index.html
  [sqlalchemy]: http://www.sqlalchemy.org/
  [1-click]: http://www.amazon.com/gp/help/customer/display.html?nodeId=468482

