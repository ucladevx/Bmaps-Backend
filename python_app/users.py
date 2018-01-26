# Interacting with users collection in mlab

from flask import Flask, jsonify, redirect, url_for, request, Blueprint
from flask_cors import CORS, cross_origin
from datetime import datetime
import pymongo
import json
import os

Users = Blueprint('Users', __name__)

# Enable Cross Origin Resource Sharing (CORS)
cors = CORS(Users)

# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
MLAB_USERNAME = os.getenv('MLAB_USERNAME')
MLAB_PASSWORD = os.getenv('MLAB_PASSWORD')

uri = 'mongodb://{0}:{1}@ds044709.mlab.com:44709/mappening_data'.format(MLAB_USERNAME, MLAB_PASSWORD)

# Set up database connection
client = pymongo.MongoClient(uri)
db = client['mappening_data'] 
users_collection = db.map_users

error_codes_to_messages = {
  0: 'USER_ALREADY_EXISTS',
  1: 'ADDING_USER_FAILED',
  2: 'USER_DOES_NOT_EXIST',
  3: 'REMOVING_USER_FAILED',
  4: 'USER_PREFERENCE_ALREADY_EXISTS',
  5: 'ADDING_USER_PREFERENCE_FAILED',
  6: 'USER_PREFERENCE_DOES_NOT_EXIST',
  7: 'REMOVING_USER_PREFERENCE_FAILED',
  8: 'NO_USER_PREFERENCES',
}

success_codes_to_messages = {
  0: 'ADDED_USER',
  1: 'REMOVED_USER',
  2: 'USER_EXISTS',
  3: 'ADDED_PREFERENCE',
  4: 'REMOVED_PREFERENCE',
  5: 'USER_PREFERENCE_EXISTS'
}

# Error messages for handling users
@Users.route('/api/user-error', methods=['GET'])
def error_message():
    return error_codes_to_messages[int(request.args['error_code'])]

# Success messages for handling users
@Users.route('/api/user-success', methods=['GET'])
def success_message():
    return success_codes_to_messages[int(request.args['success_code'])]

# Add a new user to users collection 
# {user_id, user_name, user_firstname, user_lastname}
@Users.route('/api/add-user')
def add_user():
    user_id = request.args['user_id']

    # Check if user already exists in collection
    if users_collection.find({'user_id': user_id}).count() > 0:
      return redirect(url_for('Users.error_message', error_code=0))

    # Insert new user
    users_collection.insert_one({
        "user_id": user_id, 
        "user_name": request.args['user_name'], 
        "user_firstname": request.args['user_firstname'], 
        "user_lastname": request.args['user_lastname'],
        "joined_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "preferences": []
      })

    # Check that user was successfully added to collection
    if users_collection.find({'user_id': user_id}).count() > 0:
      return redirect(url_for('Users.success_message', success_code=0))
    else:
      return redirect(url_for('Users.error_message', error_code=1))

# Remove a user by user_id from users collection
@Users.route('/api/remove-user/<user_id>')
def remove_user(user_id):
    # Check that user exists to remove
    if users_collection.find_one({'user_id': user_id}) == None:
      return redirect(url_for('Users.error_message', error_code=2))

    # Delete user
    users_collection.find_one_and_delete({'user_id': user_id})

    # Check that user was successfully deleted from collection
    if users_collection.find_one({'user_id': user_id}) == None:
      return redirect(url_for('Users.success_message', success_code=1))
    else:
      return redirect(url_for('Users.error_message', error_code=3))

# Add user preference
@Users.route('/api/add-user-preference')
def add_user_preference():
    pref = request.args['preference']
    u_id = request.args['user_id']

    user = users_collection.find_one({'user_id': u_id})

    # Check that user exists
    if user == None:
      return redirect(url_for('Users.error_message', error_code=2))

    # Update user to add preference
    # If preference was already in user list, does not add duplicate
    if pref in user['preferences']:
      return redirect(url_for('Users.error_message', error_code=4))
    else:
      users_collection.update({'user_id': u_id}, 
        {'$push': {'preferences': pref}})

    # Check that preference was successfully added to user
    user = users_collection.find_one({'user_id': u_id})
    if pref in user['preferences']:
      return redirect(url_for('Users.success_message', success_code=3))
    else:
      return redirect(url_for('Users.error_message', error_code=5))

# Remove user preference
@Users.route('/api/remove-user-preference')
def remove_user_preference():
    pref = request.args['preference']
    u_id = request.args['user_id']

    user = users_collection.find_one({'user_id': u_id})

    # Check that user exists
    if user == None:
      return redirect(url_for('Users.error_message', error_code=2))

    # If preference exists in user preferences list, remove it
    if pref in user['preferences']:
      users_collection.update({'user_id': u_id}, 
        {'$pull': {'preferences': pref}})
    else:
      return redirect(url_for('Users.error_message', error_code=6))      

    # Check that preference was successfully removed from user preferences
    user = users_collection.find_one({'user_id': u_id})
    if pref in user['preferences']:
      return redirect(url_for('Users.error_message', error_code=7))
    else:
      return redirect(url_for('Users.success_message', success_code=4))

# Get a user preferences from user_id 
@Users.route('/api/user-preferences/<user_id>', methods=['GET'])
def get_user_preferences(user_id):
    # Check that user exists
    if users_collection.find_one({'user_id': user_id}) == None:
      return redirect(url_for('Users.error_message', error_code=2))

    # Get user preferences
    preferences = users_collection.find_one({'user_id': user_id})['preferences']

    # Check if preferences is empty
    if not preferences:
        return redirect(url_for('Users.error_message', error_code=8))

    return jsonify(preferences)

# Check whether a user preference exists for a certain user_id
@Users.route('/api/user-preference-exists', methods=['GET'])
def user_preference_exists():
    pref = request.args['preference']
    u_id = request.args['user_id']

    user = users_collection.find_one({'user_id': u_id})

    # Check that user exists
    if user == None:
      return redirect(url_for('Users.error_message', error_code=2))

    # Check if preference exists in user preferences list
    if pref in user['preferences']:
      return redirect(url_for('Users.success_message', success_code=5))
    else:
      return redirect(url_for('Users.error_message', error_code=6))

# Get all users with that preference
@Users.route('/api/users-with-preference/<pref>', methods=['GET'])
def get_users_with_preference(pref):
    output = []
    for doc in users_collection.find():
      if pref in doc['preferences']:
        output.append({'user_id': doc['user_id'],
                       'user_name': doc['user_name']})

    return jsonify(output)

# Check that a user exists
@Users.route('/api/user-exists/<user_id>')
def user_exists(user_id):
    # Check that user exists
    if users_collection.find_one({'user_id': user_id}) != None:
      return redirect(url_for('Users.success_message', success_code=2))
    else:
      return redirect(url_for('Users.error_message', error_code=2))

# Get a user_name from user_id 
@Users.route('/api/user-name/<user_id>', methods=['GET'])
def get_user_name(user_id):
    # Check that user exists
    if users_collection.find_one({'user_id': user_id}) == None:
      return redirect(url_for('Users.error_message', error_code=2))

    # Get user email
    return users_collection.find_one({'user_id': user_id})['user_name']

# Get when user joined from user_id 
@Users.route('/api/user-joined/<user_id>', methods=['GET'])
def get_when_user_joined(user_id):
    # Check that user exists
    if users_collection.find_one({'user_id': user_id}) == None:
      return redirect(url_for('Users.error_message', error_code=2))

    # Get user email
    return users_collection.find_one({'user_id': user_id})['joined_time']
