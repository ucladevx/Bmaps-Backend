# Facebook Authentication
from mappening.utils.database import *

from flask import Flask, jsonify, redirect, url_for, session, request, Blueprint
from flask_login import UserMixin, LoginManager, login_required, current_user, login_user, logout_user
from flask_cors import CORS
from flask_oauth import OAuth
from datetime import datetime
import json

auth = Blueprint('auth', __name__)

# Got APP_ID and APP_SECRET from Mappening app with developers.facebook.com
DEBUG = True
SECRET_KEY = os.getenv('FACEBOOK_SECRET_KEY')
FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID')
FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')

# Flask-Oauth - set up authentication
auth.debug = DEBUG
auth.secret_key = SECRET_KEY
oauth = OAuth()

# Flask-Login - configure application for login
login_manager = LoginManager()

# Required to allow Blueprints to work with flask_login
# on_load is run when Blueprint is first registered to the app
@auth.record_once
def on_load(state):
    login_manager.init_app(state.app)
    # login_manager.session_protection = "strong" 
    # Enable session protection to prevent user sessions from being stolen
    # By default is in "basic" mode. Can be set to "None or "strong"

    print "Login manager set up with auth Blueprint!"


# OAuth for authentication. Also supports Google Authentication.
facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email'}
)

# https://stackoverflow.com/questions/16273499/flask-login-can-not-be-used-in-blueprint-object
# https://github.com/twtrubiks/Flask-Login-example/blob/master/app.py
# https://flask-login.readthedocs.io/en/latest/#your-user-class

# UserMixin provides default implementations for methods user objs should have
class User(UserMixin):
    def __init__(self, user_name, user_id, active=True):
        self.user_name = user_name
        self.user_id = user_id
        self.active = active

    # Get unicode id to uniquely identify user
    # Can be used to load user from user_loader callback
    def get_id(self):
        return unicode(self.user_id)

    # # True if user has an activated account that they can log in to
    # # Otherwise account will be rejected/suspended from use
    # def is_active(self):
    #     user = map_users_collection.find_one({'user_id': self.user_id})
    #     if user != None:
    #         return True
    #     else:
    #         return False

    # # Determine whether user is anonymous
    # def is_anonymous(self):
    #     return False:

    # # True is user is authenticated with proper credentials
    # # Must be true for users to fulfill criteria of login_required
    # def is_authenticated(self):
    #     return True

# Return user
def get_user(user_id):
    # Check that user exists
    user = map_users_collection.find_one({'user_id': user_id})
    if user != None:
        return True
    else:
        return False

# Can use user ID as remember token
# Must change user's ID to invalidate login sessions
# Can achieve this with session tokens rather than the user's ID
# Would modify get_id() method to return session token rather than user's ID
@login_manager.user_loader
def user_loader(user_id):
    if get_user(user_id):
        user = map_users_collection.find_one({'user_id': user_id})
        user = User(user['user_name'], user['user_id'])
        return user
    return None    

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')

@auth.route('/api/login-failed')
def login_failed():
    return "Failed to log user in!"

@auth.route('/api/register')
def register():
    return redirect(url_for('FbAuth.facebook_register'))

@auth.route('/api/register/facebook')
def facebook_register():
    return facebook.authorize(
      callback=url_for('FbAuth.facebook_authorized',
      next=request.args.get('next') or None, _external=True))

# Checks whether authentication works or access is denied
@auth.route('/api/register/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None or 'access_token' not in resp:
        flash('Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']))
        return redirect(url_for('FbAuth.login_failed'))
    session['oauth_token'] = (resp['access_token'], '')
    session['expires'] = resp['expires_in']
    # return session.get('oauth_token')[0]

    # Email is not always supplied, currently doesn't try to use email
    # me = facebook.get('/me?fields=id,name,first_name,last_name,email,picture')

    # # Returns success if new user was added, otherwise error if duplicate
    # return redirect(url_for('Users.add_user', user_id=me.data['id'], 
    #     user_name=me.data['name'], user_firstname=me.data['first_name'], 
    #     user_lastname=me.data['last_name']))

    me = facebook.get('/me?fields=id,name,first_name,last_name,email,picture')
    userID = me.data['id']
    userName = me.data['name']
    accessToken = resp['access_token']
    fb_user = map_users_collection.find_one({'user_id': userID})

    # If user exists in collection, logs them in
    # Otherwise, registers new user and logs them in
    if fb_user == None:
        add_user(userID, userName, me.data['first_name'], me.data['last_name'], accessToken)
        user = User(userName, userID)
        login_user(user)
    else:
        user = User(fb_user['user_name'], userID)
        login_user(user)

    return "Successfully logged in with Facebook!"

# Registers new user in DB
def add_user(userID, userName, firstName, lastName, accessToken):
    # Check if user already exists in collection
    if map_users_collection.find({'user_id': userID}).count() > 0:
      return "USER_ALREADY_EXISTS"

    # Insert new user
    map_users_collection.insert_one({
        "user_id": userID, 
        "user_name": userName, 
        "user_firstname": firstName, 
        "user_lastname": lastName,
        "access_token": accessToken,
        "joined_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "preferences": []
      })

    # Check that user was successfully added to collection
    if map_users_collection.find({'user_id': userID}).count() > 0:
      return "ADDED_USER"
    else:
      return "ADDING_USER_FAILED"

# Only works if already logged in
@auth.route('/api/user-id', methods=['GET'])
@login_required
def facebook_user_id():
    me = facebook.get('/me?fields=id')
    return me.data['id']

# Log out user. 
# Will no longer be able to access any route decorated with @login_required
@auth.route('/api/logout')
@login_required
def logout():
    logout_user()
    return "Successfully logged out!"  
