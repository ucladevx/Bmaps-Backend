from flask import Flask, redirect, url_for, session, request, Blueprint
from flask_oauth import OAuth
 
DEBUG = True
SECRET_KEY = 'development key'
FACEBOOK_APP_ID = '353855031743097'
FACEBOOK_APP_SECRET = '2831879e276d90955f3aafe0627d3673'
 
fb_auth_api = Blueprint('fb_auth_api', __name__)
fb_auth_api.debug = DEBUG
fb_auth_api.secret_key = SECRET_KEY
oauth = OAuth()

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

@fb_auth_api.route('/login')
def login():
    return redirect(url_for('fb_auth_api.facebook_login'))

@fb_auth_api.route('/login/facebook')
def facebook_login():
    return facebook.authorize(
      callback=url_for('fb_auth_api.facebook_authorized',
      next=request.args.get('next') or None, _external=True))


@fb_auth_api.route('/login/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None or 'access_token' not in resp:
        flash('Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']))
        return redirect(url_for('fb_auth_api.login'))
    session['oauth_token'] = (resp['access_token'], '')

    me = facebook.get('/me')
    return 'Logged in as id=%s name=%s' % (me.data['id'], me.data['name'])

if __name__ == '__main__':
    fb_auth_api.run()
