from mappening.utils.secrets import FACEBOOK_SECRET_KEY
from mappening.api.utils import user_utils
from mappening.api.models.user import User
from mappening.api import users
from facebook import facebook_oauth

from flask import Flask, jsonify, redirect, url_for, session, request, Blueprint
from flask_login import UserMixin, LoginManager, login_required, current_user, login_user, logout_user
from flask_cors import CORS
from flask_oauth import OAuth
from datetime import datetime
import json

# Route Prefix: /auth
auth = Blueprint('auth', __name__)

# Got APP_ID and APP_SECRET from Mappening app with developers.facebook.com
DEBUG = True
auth.debug = DEBUG
auth.secret_key = FACEBOOK_SECRET_KEY

# Flask-Login - configure application for login
login_manager = LoginManager()

# Required to allow Blueprints to work with flask_login
# on_load is run when Blueprint is first registered to the app
# Enable session protection to prevent user sessions from being stolen
# By default is in "basic" mode. Can be set to "None or "strong"
@auth.record_once
def on_load(state):
    login_manager.init_app(state.app)
    # login_manager.session_protection = "strong"

    print("Login manager set up with auth Blueprint!")

# Can use user ID as remember token
# Must change user's ID to invalidate login sessions
# Can achieve this with session tokens rather than the user's ID
# Would modify get_id() method to return session token rather than user's ID
# Return None if ID is not valid, will remove ID from session and continue processing
@login_manager.user_loader
def user_loader(user_id):
    db_user = user_utils.get_user(user_id)
    if db_user:
        return User(db_user['account']['id'], db_user['account']['is_active'], db_user['account']['is_admin'])
    return None

# TODO: move this to users but don't require admin privileges?
@auth.route('/current', methods=['GET'])
def get_current_user():
    if not current_user.is_authenticated:
      return "No user is logged in!"

    user = user_utils.get_user(current_user.get_id())
    if user:
        return jsonify(user)
    return "Could not get current user!"

@auth.route('/')
def auth_redirect():
    if current_user.is_authenticated:
        # return redirect(url_for('main page route'))
        return "Already logged in!"
    return redirect(url_for('auth.login'))

@auth.route('/login')
def login():
    return facebook_oauth.authorize(
      callback=url_for('auth.facebook_authorized',
      next=request.args.get('next') or None, _external=True))

# Checks whether authentication works or access is denied
@auth.route('/login/authorized')
@facebook_oauth.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        return "Access denied: reason=%s error=%s" % (
                request.args["error_reason"],
                request.args["error_description"]
            )
    session['oauth_token'] = (resp['access_token'], '')
    session['expires'] = resp['expires_in']
    print("Token expires in " + str(resp['expires_in']))

    # me = facebook_oauth.get("/me")
    # return str(me.data)

    me = facebook_oauth.get('/me?fields=id,name,first_name,last_name,email,picture')
    userID = me.data['id']
    userName = me.data['name']
    accessToken = resp['access_token']

    # If user exists in collection, logs them in
    # Otherwise, registers new user and logs them in
    # TODO get email if we can
    fb_user = user_utils.get_user(userID)
    if not fb_user:
        user_utils.add_user(userID, userName, me.data['first_name'], me.data['last_name'])
        user = User(userID)
        login_user(user)
        return "Successfully registered new user!"
    else:
        users.update_user(userID)
        user = User(userID, fb_user['account']['is_active'], fb_user['account']['is_admin'])
        login_user(user)
        return "Successfully logged in with Facebook!"

# Log out user.
# Will no longer be able to access any route decorated with @login_required
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return "Successfully logged out!"
