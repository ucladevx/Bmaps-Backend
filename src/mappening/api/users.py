# TODO: test all the non-GET routes
# TODO: error checking on int parameters?

from mappening.utils.database import users_collection, dead_users_collection
from mappening.api.utils import user_utils

from flask import Flask, jsonify, redirect, url_for, request, Blueprint
from flask_login import current_user
from flask_cors import CORS, cross_origin
from datetime import datetime
import json

# Route Prefix: /api/v2/users
users = Blueprint('users', __name__)

@users.before_request
def check_admin_permissions():
    if not current_user.is_authenticated:
      return "No user is logged in!"
    if current_user.is_authenticated and not current_user.is_admin():
      return "User does not have permissions to access/modify user data."

# Get all users
@users.route('/', methods=['GET'])
def get_all_users():
    output = []

    users_cursor = users_collection.find({}, {'_id': False})
    if users_cursor.count() > 0:
      for user in users_cursor:
        output.append({'user': user})
    else:
        return 'Cannot find any users!'

    return jsonify({'users': output})

# Get a specific user's information
# Make helper function for auth that gets info for login
# Make separate function for frontend to use that gets info of current_user
@users.route('/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    # Check that user exists
    user = user_utils.get_user(user_id)
    if user:
        return jsonify(user)
    return "No such user with id " + str(user_id) + " found!"

# Update specific user's information
@users.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    active = request.args.get('active')
    admin = request.args.get('admin')
    password = request.args.get('password')
    first_name = request.args.get('first_name')
    last_name = request.args.get('last_name')
    email = request.args.get('email')

    # Check if user already exists in collection
    user = user_utils.get_user(user_id)
    if user:
        # Update access/update/login time (in UTC I think)
        user['account']['time_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Update all fields as passed in via optional parameters
        if active and active.lower() == "true": user['account']['is_active'] = True
        if active and active.lower() == "false": user['account']['is_active'] = False
        if admin and admin.lower() == "true": user['account']['is_admin'] = True
        if admin and admin.lower() == "false": user['account']['is_admin'] = False
        if password: user['account']['password_hash'] = password  # TODO: implement hashing/salting/do this better
        if first_name: user['personal_info']['first_name'] = first_name
        if last_name: user['personal_info']['last_name'] = last_name
        if email: user['personal_info']['email'] = email

        # Update database entry
        users_collection.replace_one({ "account.id": str(user_id) }, user.copy())

        return jsonify(user_utils.get_user(user_id))
    
    return "No such user with id " + str(user_id) + " found!"

# Add a new user to users collection 
@users.route('/', methods=['POST'])
def add_user_through_api():
  user_id = request.args.get('id')
  full_name = request.args.get('full_name', '')
  first_name = request.args.get('first_name', '')
  last_name = request.args.get('last_name', '')
  email = request.args.get('email', '')
  active = request.args.get('active')
  admin = request.args.get('admin')
  password = request.args.get('password', '')
  username = request.args.get('username', '')

  if not user_id:
    # TODO: add ID automatically, don't require it to be supplied
    return "User ID required to add a new user"

  if active and active.lower() == "false": 
    active = False
  else:
    active = True

  if admin and admin.lower() == "true": 
    admin = True
  else:
    admin = False

  return user_utils.add_user(user_id, full_name, first_name, last_name, email, active, admin, password, username)

# Reactivate a user
@users.route('/activate/<int:user_id>', methods=['PUT'])
def activate_user(user_id):
    # Check if user exists in collection
    user = user_utils.get_user(user_id)
    if user:
        # Update status to active
        user['account']['is_active'] = True
        user['account']['time_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Update database entry
        users_collection.replace_one({ "account.id": str(user_id) }, user.copy())

        return "Activated user with id " + str(user_id) + "!"
    
    return "No such user with id " + str(user_id) + " found!"

# Deactivate a user without deleting it from the database
@users.route('/deactivate/<int:user_id>', methods=['PUT'])
def deactivate_user(user_id):
    # Check if user exists in collection
    user = user_utils.get_user(user_id)
    if user:
        # Update status to inactive
        user['account']['is_active'] = False
        user['account']['time_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Update database entry
        users_collection.replace_one({ "account.id": str(user_id) }, user.copy())

        return "Deactivated user with id " + str(user_id) + "!"
    
    return "No such user with id " + str(user_id) + " found!"

# Remove a user by user_id
# Keep old user information in different database for the mems (and the info)
@users.route('/<int:user_id>', methods=['DELETE'])
def remove_user(user_id):
  # Check that user exists to remove
  user = user_utils.get_user(user_id)
  if not user:
    return "No such user with id " + str(user_id) + " found!"
  
  # Delete user from OG database
  users_collection.find_one_and_delete({'account.id': str(user_id)})
  
  # Check that user was successfully deleted from collection
  if user_utils.get_user(user_id):
    return "User with id " + str(user_id) + " was not deleted successfully!"
  
  # Insert to database for deleted users
  user['account']['time_deleted'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  dead_users_collection.insert_one(user)

  if dead_users_collection.find_one({'account.id': str(user_id)}, {'_id': False}):
    return "User was successfully removed from the database and saved to past users!"
  else:
    return "User with id " + str(user_id) + " was successfully deleted (but not saved to past users)!"
