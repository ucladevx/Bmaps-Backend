# Interacting with users collection in mlab

from flask import Flask, redirect, url_for, request, Blueprint
import pymongo

Users = Blueprint('Users', __name__)

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
    5: 'REMOVING_USER_FAILED'
}

# Error messages for adding a new user
@Users.route('/user-results', methods=['GET'])
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
        "user_lastname": request.args['user_lastname']})

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

if __name__ == '__main__':
    Users.run()
