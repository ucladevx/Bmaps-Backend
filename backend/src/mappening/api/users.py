# Interacting with users collection in mlab
from mappening.utils.database import *

from flask import Flask, jsonify, redirect, url_for, request, Blueprint
from flask_cors import CORS, cross_origin
from datetime import datetime
import json
import os

users = Blueprint('users', __name__)

# Get all users with this preference
# @users.route('/users/<preference>', methods=['GET'])

# Get all preferences of this user
# @users.route('/<id:user_id>/<preference>', methods=['GET'])

# Add a preference to a specific user (WHICH?)
# @users.route('/<id:user_id>/<preference>', methods=['POST'])

# Remove a preference from a specific user
# @users.route('/<id:user_id>/<preference>', methods=['DELETE'])

@users.route('/', methods=['GET']) # Get all users, needs authentication
def get_all_users():
    output = []

    users_cursor = map_users_collection.find({}, {'_id': False})
    if users_cursor.count() > 0:
      for user in users_cursor:
        output.append({"user": user})
    else:
        print 'Cannot find any users!'

    return jsonify({'users': output})

@users.route('/<id:user_id>', methods=['GET']) # Get user info
def get_user(user_id):
    # Check that user exists
    user = map_users_collection.find_one({'user_id': user_id})
    if user != None:
        return user
    else:
        return None

@users.route('/<id:user_id>', methods=['PUT']) # Update user info
def update_user(userID):
    # Check if user already exists in collection
    user = get_user(userID)
    if user:
        user['last_accessed_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        map_users_collection.replace_one({ "user_id": userID }, user.copy())
    else:
        return "NO_SUCH_USER"

# Add a new user to users collection 
# {user_id, user_name, user_firstname, user_lastname}
@users.route('/', methods=['POST']) # Create user, login = post as well
def add_user(userID, userName, firstName, lastName, accessToken):
  # user_id = request.args['user_id']

    # Check if user already exists in collection
    if get_user(userID):
      return "USER_ALREADY_EXISTS"

    # Insert new user
    map_users_collection.insert_one({
        "user_id": userID, 
        "user_name": userName, 
        "user_firstname": firstName, 
        "user_lastname": lastName,
        "joined_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "last_accessed_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "preferences": []
      })

    # Check that user was successfully added to collection
    if get_user(userID):
      return "ADDED_USER"
    else:
      return "ADDING_USER_FAILED"


@users.route('/deactivate/<id:user_id>', methods=['PUT']) # Deactivate user

# Remove a user by user_id from users collection
@users.route('/<id:user_id>', methods=['DELETE']) # Remove user (put in past user db)
def remove_user(user_id):
    # Check that user exists to remove
    if map_users_collection.find_one({'user_id': user_id}) == None:
      return redirect(url_for('Users.error_message', error_code=2))

    # Delete user
    map_users_collection.find_one_and_delete({'user_id': user_id})

    # Check that user was successfully deleted from collection
    if map_users_collection.find_one({'user_id': user_id}) == None:
      return redirect(url_for('Users.success_message', success_code=1))
    else:
      return redirect(url_for('Users.error_message', error_code=3))
