from mappening.api.utils import user_utils
from mappening.api.models.user import User
from mappening.api import users
from google import google_oauth

from flask import Flask, jsonify, redirect, url_for, session, request, Blueprint
from flask_login import UserMixin, LoginManager, login_required, current_user, login_user, logout_user
from flask_cors import CORS
from flask_oauth import OAuth
from datetime import datetime
import json

# Route Prefix: /auth
auth = Blueprint('auth', __name__)

DEBUG = True
auth.debug = DEBUG

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
      return jsonify({})

    user = user_utils.get_user(current_user.get_id())
    if user:
        return jsonify(user)

    # Could not get current user
    return jsonify({})

@auth.route('/events/favorites', methods=['GET', 'POST'])
def user_events():
    if current_user.is_authenticated:
        currID = current_user.get_id()
        user = user_utils.get_user(currID)
        if not user:
            return "Could not get current user!"
        eventID = request.args.get('eid')
        if request.method == 'POST':
            # POST
            return user_utils.add_favorite(currID, eventID)
        elif request.method == 'DELETE':
            # DELETE
            return user_utils.remove_favorite(currID, eventID)
        else:
            # GET or anything else
            return jsonify(user['app']['favorites'])
    return redirect(url_for('auth.login'))

@auth.route('/')
def auth_redirect():
    if current_user.is_authenticated:
        # return redirect(url_for('main page route'))
        return "Already logged in!"
    return redirect(url_for('auth.login'))

@auth.route('/login')
def login():
    redirect_url = request.args.get('redirect')
    if current_user.is_authenticated:
        # Already logged in
        return redirect(redirect_url)
    return google_oauth.authorize(
      callback=url_for('auth.google_authorized',
      next=redirect_url or None, _external=True))

# Checks whether authentication works or access is denied
@auth.route('/login/authorized')
@google_oauth.authorized_handler
def google_authorized(resp):
    next = request.args.get('next')
    if resp is None:
        return "Access denied: reason=%s error=%s" % (
                request.args["error_reason"],
                request.args["error_description"]
            )
    session['oauth_token'] = (resp['access_token'], '')
    session['expires'] = resp['expires_in']
    print("Token expires in " + str(resp['expires_in']))

    me = google_oauth.get('userinfo')
    print(me.data)

    userID = me.data['id']
    userName = me.data['name'].title()
    accessToken = resp['access_token']
    email = me.data['email']

    domain = email.split('@')[1]
    if domain != 'ucla.edu' and domain != 'g.ucla.edu':
        return "Invalid email. UCLA email required."

    # If user exists in collection, logs them in
    # Otherwise, registers new user and logs them in
    # TODO get email if we can
    g_user = user_utils.get_user(userID)
    if not g_user:
        # Successfully registered new user
        user_utils.add_user(userID, userName, me.data['given_name'].title(), me.data['family_name'].title(), me.data['email'])
        user = User(userID)
        login_user(user)
        return "Successfully registered new user" if next == None else redirect(next)
    else:
        # Successfully logged in
        users.update_user(userID)
        user = User(userID, g_user['account']['is_active'], g_user['account']['is_admin'])
        login_user(user)
        return "Successfully logged in" if next == None else redirect(next)

# Log out user.
# Will no longer be able to access any route decorated with @login_required
@auth.route("/logout")
@login_required
def logout():
    redirect_url = request.args.get('redirect')
    logout_user()
    return "Successfully logged out!" if redirect_url == None else redirect(redirect_url)
