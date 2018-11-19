from mappening.utils.secrets import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from flask_oauth import OAuth

oauth = OAuth();
google_oauth = oauth.remote_app('google',
                          base_url='https://www.googleapis.com/oauth2/v1/',
                          authorize_url='https://accounts.google.com/o/oauth2/auth',
                          request_token_url=None,
                          request_token_params={'scope': 'profile email',
                                                'response_type': 'code'},
                          access_token_url='https://www.googleapis.com/oauth2/v3/token',
                          access_token_method='POST',
                          access_token_params={'grant_type': 'authorization_code'},
                          consumer_key=GOOGLE_CLIENT_ID,
                          consumer_secret=GOOGLE_CLIENT_SECRET)
