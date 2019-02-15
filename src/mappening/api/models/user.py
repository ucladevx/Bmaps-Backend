from mappening.auth.facebook import facebook_oauth
from mappening.auth.google import google_oauth

from flask import session
from flask_login import UserMixin

# UserMixin provides default implementations for methods user objs should have
class User(UserMixin):
    def __init__(self, user_id, active=True, admin=False):
        self.user_id = user_id
        self.active = active
        self.admin = admin

    # Get unicode id to uniquely identify user
    # Can be used to load user from user_loader callback
    def get_id(self):
        return unicode(self.user_id)

    # True if user has an activated account that they can log in to
    # Otherwise account will be rejected/suspended from use
    def is_active(self):
        return self.active

    # Determine whether user is anonymous
    def is_anonymous(self):
        return False

    # True is user is authenticated with proper credentials
    # Must be true for users to fulfill criteria of login_required
    def is_authenticated(self):
        return True

    # True if user has admin privileges (can interact with user info)
    def is_admin(self):
        return self.admin

@facebook_oauth.tokengetter
def get_facebook_oauth_token():
    return session.get("oauth_token")

@google_oauth.tokengetter
def get_google_oauth_token():
    return session.get("oauth_token")
