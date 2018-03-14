from mappening.auth.facebook import facebook_oauth

from flask import session
from flask_login import UserMixin

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

    # True is user is authenticated with proper credentials
    # Must be true for users to fulfill criteria of login_required
    def is_authenticated(self):
        return True

@facebook_oauth.tokengetter
def get_facebook_oauth_token():
    return session.get("oauth_token")
