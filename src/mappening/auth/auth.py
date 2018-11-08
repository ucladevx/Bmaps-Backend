from flask import Flask, redirect, url_for, session, Blueprint
from flask_oauth import OAuth
from google import google_oauth

REDIRECT_URI = '/oauth2callback'

# Route Prefix: /auth
auth = Blueprint('auth', __name__)

@auth.route('/')
def index():
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('auth.login'))

    access_token = access_token[0]
    from urllib2 import Request, urlopen, URLError

    headers = {'Authorization': 'OAuth '+access_token}
    req = Request('https://www.googleapis.com/oauth2/v1/userinfo',
                  None, headers)
    try:
        res = urlopen(req)
    except URLError, e:
        if e.code == 401:
            # Unauthorized - bad token
            session.pop('access_token', None)
            return redirect(url_for('auth.login'))
        return res.read()

    return res.read()

@auth.route('/login')
def login():
    callback=url_for('auth.authorized', _external=True)
    return google_oauth.authorize(callback=callback)

@auth.route(REDIRECT_URI)
@google_oauth.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    session['access_token'] = access_token, ''
    return redirect(url_for('index'))


@google_oauth.tokengetter
def get_access_token():
    return session.get('access_token')
