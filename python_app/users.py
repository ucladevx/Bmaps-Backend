# Interacting with users collection in mlab

from flask import Flask, jsonify, redirect, url_for, request, Blueprint
from flask_cors import CORS, cross_origin
from datetime import datetime
import pymongo

Users = Blueprint('Users', __name__)

# Enable Cross Origin Resource Sharing (CORS)
cors = CORS(Users)

# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
uri = 'mongodb://devx_dora:3map5me@ds044709.mlab.com:44709/mappening_data'

# Set up database connection
client = pymongo.MongoClient(uri)
db = client['mappening_data'] 
users_collection = db.map_users

error_codes_to_messages = {
    0: 'SUCCESS',
    1: 'USER_EXISTS',
    2: 'USER_ALREADY_EXISTS',
    3: 'ADDING_USER_FAILED',
    4: 'USER_DOES_NOT_EXIST',
    5: 'REMOVING_USER_FAILED',
    6: 'USER_PREFERENCE_ALREADY_EXISTS',
    7: 'ADDING_USER_PREFERENCE_FAILED',
    8: 'USER_PREFERENCE_DOES_NOT_EXIST',
    9: 'REMOVING_USER_PREFERENCE_FAILED',
    10: 'NO_USER_PREFERENCES'
}

# Error messages for adding a new user
@Users.route('/api/user-results', methods=['GET'])
def error_message():
    return error_codes_to_messages[int(request.args['error_code'])]

# Add a new user to users collection 
# {user_id, user_name, user_firstname, user_lastname}
@Users.route('/api/add-user')
def add_user():
    user_id = request.args['user_id']

    # Check if user already exists in collection
    if users_collection.find({'user_id': user_id}).count() > 0:
      return redirect(url_for('Users.error_message', error_code=2))

    # Insert new user
    users_collection.insert_one({"user_id": user_id, 
        "user_name": request.args['user_name'], 
        "user_firstname": request.args['user_firstname'], 
        "user_lastname": request.args['user_lastname'],
        "joined_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "preferences": []})

    # Check that user was successfully added to collection
    if users_collection.find({'user_id': user_id}).count() > 0:
      return redirect(url_for('Users.error_message', error_code=0))
    else:
      return redirect(url_for('Users.error_message', error_code=3))

# Remove a user by user_id from users collection
@Users.route('/api/remove-user/<user_id>')
def remove_user(user_id):
    # Check that user exists to remove
    if users_collection.find_one({'user_id': user_id}) == None:
      return redirect(url_for('Users.error_message', error_code=4))

    # Delete user
    users_collection.find_one_and_delete({'user_id': user_id})

    # Check that user was successfully deleted from collection
    if users_collection.find_one({'user_id': user_id}) == None:
      return redirect(url_for('Users.error_message', error_code=0))
    else:
      return redirect(url_for('Users.error_message', error_code=5))

# Add user preference
@Users.route('/api/add-user-preference')
def add_user_preference():
    pref = request.args['preference']
    u_id = request.args['user_id']

    user = users_collection.find_one({'user_id': u_id})

    # Check that user exists
    if user == None:
      return redirect(url_for('Users.error_message', error_code=4))

    # Update user to add preference
    # If preferences list does not already exist, adds field
    # If preference was already in user list, does not add duplicate
    if pref in user['preferences']:
      return redirect(url_for('Users.error_message', error_code=6))
    else:
      users_collection.update({'user_id': u_id}, 
        {'$push': {'preferences': pref}})

    # Check that preference was successfully added to user
    user = users_collection.find_one({'user_id': u_id})
    if pref in user['preferences']:
      return redirect(url_for('Users.error_message', error_code=0))
    else:
      return redirect(url_for('Users.error_message', error_code=7))

# Remove user preference
@Users.route('/api/remove-user-preference')
def remove_user_preference():
    pref = request.args['preference']
    u_id = request.args['user_id']

    user = users_collection.find_one({'user_id': u_id})

    # Check that user exists
    if user == None:
      return redirect(url_for('Users.error_message', error_code=4))

    # If preference exists in user preferences list, remove it
    if pref in user['preferences']:
      users_collection.update({'user_id': u_id}, 
        {'$pull': {'preferences': pref}})
    else:
      return redirect(url_for('Users.error_message', error_code=8))      

    # Check that preference was successfully removed from user preferences
    user = users_collection.find_one({'user_id': u_id})
    if pref in user['preferences']:
      return redirect(url_for('Users.error_message', error_code=9))
    else:
      return redirect(url_for('Users.error_message', error_code=0))

# Get a user preferences from user_id 
@Users.route('/api/user-preferences/<user_id>', methods=['GET'])
def get_user_preferences(user_id):
    # Check that user exists
    if users_collection.find_one({'user_id': user_id}) == None:
      return redirect(url_for('Users.error_message', error_code=4))

    # Get user preferences
    preferences = users_collection.find_one({'user_id': user_id})['preferences']

    # Check if preferences is empty
    if not preferences:
        return redirect(url_for('Users.error_message', error_code=10))
        
    return jsonify(preferences)

# Check that a user exists
@Users.route('/api/user-exists/<user_id>')
def user_exists(user_id):
    # Check that user exists
    if users_collection.find_one({'user_id': user_id}) != None:
      return redirect(url_for('Users.error_message', error_code=1))
    else:
      return redirect(url_for('Users.error_message', error_code=4))

# Get a user_name from user_id 
@Users.route('/api/user-name/<user_id>', methods=['GET'])
def get_user_name(user_id):
    # Check that user exists
    if users_collection.find_one({'user_id': user_id}) == None:
      return redirect(url_for('Users.error_message', error_code=4))

    # Get user email
    return users_collection.find_one({'user_id': user_id})['user_name']

# Get a when user joined from user_id 
@Users.route('/api/user-joined/<user_id>', methods=['GET'])
def get_when_user_joined(user_id):
    # Check that user exists
    if users_collection.find_one({'user_id': user_id}) == None:
      return redirect(url_for('Users.error_message', error_code=4))

    # Get user email
    return users_collection.find_one({'user_id': user_id})['joined_time']
