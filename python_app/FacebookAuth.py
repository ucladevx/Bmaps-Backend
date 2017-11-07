# Facebook Authentication
# TODO: logout, store user profiles

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

@fb_auth.route('/login')
def login():
    return redirect(url_for('fb_auth.facebook_login'))

@fb_auth.route('/login/facebook')
def facebook_login():
    return facebook.authorize(
      callback=url_for('fb_auth.facebook_authorized',
      next=request.args.get('next') or None, _external=True))

# Checks whether authentication works or access is denied
# If successful, returns some user data
@fb_auth.route('/login/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None or 'access_token' not in resp:
        flash('Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']))
        return redirect(url_for('fb_auth.login'))
    session['oauth_token'] = (resp['access_token'], '')

    # TODO: email is not always supplied
    me = facebook.get('/me?fields=id,name,email,picture')
    # return 'Logged in as id=%s name=%s' % (me.data['id'], me.data['name'])
    return jsonify(me.data)

if __name__ == '__main__':
    fb_auth.run()
