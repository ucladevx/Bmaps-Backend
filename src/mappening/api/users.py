# LMAO TODO FIX WOW SO MANY TODOS

# Interacting with users collection in mlab
from mappening.utils.database import users_collection

from flask import Flask, jsonify, redirect, url_for, request, Blueprint
from flask_cors import CORS, cross_origin
from datetime import datetime
import json
import os

users = Blueprint('users', __name__)

# TODO: implement
# Get all users with this preference
# @users.route('/users/<preference>', methods=['GET'])

# Get all preferences of this user
# @users.route('/<int:user_id>/<preference>', methods=['GET'])

# Add a preference to a specific user (WHICH?)
# @users.route('/<int:user_id>/<preference>', methods=['POST'])

# Remove a preference from a specific user
# @users.route('/<int:user_id>/<preference>', methods=['DELETE'])

# Get all users
# TODO: needs authentication (logged in user should have some superpower heh)
# https://stackoverflow.com/questions/45419802/how-to-protect-flask-restful-with-flask-user-management
@users.route('/', methods=['GET'])
def get_all_users():
    output = []

    users_cursor = users_collection.find({}, {'_id': False})
    if users_cursor.count() > 0:
      for user in users_cursor:
        output.append({"user": user})
    else:
        print('Cannot find any users!')

    return jsonify({'users': output})

# Get a specific user's information
# TODO: needs authentication? One user shouldn't be able to access someone else's info
# Make helper function for auth that gets info for login
# Make separate function for frontend to use that gets info of current_user
@users.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # Check that user exists
    user = users_collection.find_one({'user_id': user_id})
    if user != None:
        return user
    else:
        return None

# Update specific user's information with last logged in time
# TODO: generalize so any new info passed in will be updated (e.g. email)
# TODO: prtect with admin privileges
@users.route('/<int:user_id>', methods=['PUT'])
def update_user(userID):
    # Check if user already exists in collection
    user = get_user(userID)
    if user:
        user['last_accessed_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        users_collection.replace_one({ "user_id": userID }, user.copy())
    else:
        return "NO_SUCH_USER"

# Add a new user to users collection 
# {user_id, user_name, user_firstname, user_lastname}
# TODO: prtect with admin privileges
@users.route('/', methods=['POST'])
def add_user(userID, userName, firstName, lastName, accessToken):
  # user_id = request.args['user_id']
  # TODO: pass these in as request args

  # Check if user already exists in collection
  if get_user(userID):
    return "USER_ALREADY_EXISTS"

  # Insert new user
  users_collection.insert_one({
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


# @users.route('/deactivate/<int:user_id>', methods=['PUT']) # Deactivate user
# TODO: Implement

# Remove a user by user_id
# Keep old user information in different database for the mems (and the info)
# TODO: restrict accessssss
@users.route('/<int:user_id>', methods=['DELETE'])
def remove_user(user_id):
  # Check that user exists to remove
  if not get_user(userID):
    return "USER_DOES_NOT_EXIST"
  
  # Delete user
  users_collection.find_one_and_delete({'user_id': user_id})
  
  # Check that user was successfully deleted from collection
  if get_user(userID):
    return "USER_WAS_NOT_DELETED_BOO"
  else:
    return "USER_WAS_DELETED_YAY"
