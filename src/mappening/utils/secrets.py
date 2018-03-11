import os
from dotenv import load_dotenv

# Get environment vars for keeping sensitive info secure
# Has to come before blueprints that use the env vars
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

print "Opening the secret door..."

FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID')
FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')
FACEBOOK_SECRET_KEY = os.getenv('FACEBOOK_SECRET_KEY')
FACEBOOK_USER_ACCESS_TOKEN = os.getenv('FACEBOOK_USER_ACCESS_TOKEN')

MLAB_USERNAME = os.getenv('MLAB_USERNAME')
MLAB_PASSWORD = os.getenv('MLAB_PASSWORD')

APP_SECRET_KEY = os.getenv('APP_SECRET_KEY')

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

print "Got the .env secrets..."
