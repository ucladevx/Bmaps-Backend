# Facebook Authentication
# TODO: logout, email

from flask import Flask, jsonify, redirect, url_for, session, request, Blueprint
from flask_oauth import OAuth

# Got APP_ID and APP_SECRET from Mappening app with developers.facebook.com
DEBUG = True
SECRET_KEY = 'development key'
FACEBOOK_APP_ID = '353855031743097'
FACEBOOK_APP_SECRET = '2831879e276d90955f3aafe0627d3673'

fb_auth = Blueprint('fb_auth', __name__)
fb_auth.debug = DEBUG
fb_auth.secret_key = SECRET_KEY
oauth = OAuth()

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

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')

@fb_auth.route('/register')
def register():
    return redirect(url_for('fb_auth.facebook_register'))

@fb_auth.route('/register/facebook')
def facebook_register():
    return facebook.authorize(
      callback=url_for('fb_auth.facebook_authorized',
      next=request.args.get('next') or None, _external=True))

# Checks whether authentication works or access is denied
@fb_auth.route('/register/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None or 'access_token' not in resp:
        flash('Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']))
        return redirect(url_for('fb_auth.login'))
    session['oauth_token'] = (resp['access_token'], '')

    # TODO: email is not always supplied, currently doesn't try to use email
    me = facebook.get('/me?fields=id,name,first_name,last_name,email,picture')

    # Returns success if new user was added, otherwise error if duplicate
    return redirect(url_for('Users.add_user', user_id=me.data['id'], 
        user_name=me.data['name'], user_firstname=me.data['first_name'], 
        user_lastname=me.data['last_name']))

# Only works if already logged in
@fb_auth.route('/user-id')
def facebook_user_id():
    me = facebook.get('/me?fields=id')
    return me.data['id']

if __name__ == '__main__':
    fb_auth.run()
