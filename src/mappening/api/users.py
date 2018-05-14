# TODO: protect these api calls with some token or something
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

@users.route('/', methods=['GET'])
def get_all_users():
    """
    :Route: GET /

    :Description: Gets all users and their information

    :return: JSON of all user info

    :Requires: Admin permissions

    """
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
    """
    :Route: GET /<user_id>

    :Description: Gets single user with id `user_id`

    :param user_id: The unique ID of a specific user
    :type user_id: int

    :return: JSON of specific user info

    :Requires: Admin permissions

    """
    # Check that user exists
    user = user_utils.get_user(user_id)
    if user:
        return jsonify(user)
    return "No such user with id " + str(user_id) + " found!"

@users.route('/search', methods=['GET'])
def search_users():
    """
    :Route: GET /search?favorite=id

    :Description: Gets ID and name of users as filtered by a specified event ID. If user has specified event listed as a favorite then is included in results.
    
    :param favorite: An optional query component/parameter where the ID of an event is passed
    :type favorite: str or None

    :return: JSON of all users matching filters

    :Requires: Admin permissions

    """
    favorite = request.args.get('favorite')
    
    search_dict = {}
    output = []

    # Add to search dict
    if favorite:
      search_dict['app.favorites'] = favorite

    users_cursor = users_collection.find(search_dict, {'_id': False})
    if users_cursor.count() > 0:
      for user in users_cursor:
        output.append({'user_id': user['account']['id'], 'full_name': user['personal_info']['full_name']})

    return jsonify({ 'users': output })

# Update specific user's information
@users.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    :Route: PUT /<user_id>?active=false&admin=true&password=str&first_name=Katrina&last_name=Wijaya&email=mappeningdevx@gmail.com

    :Description: Updates user with id `user_id`. Updates any optional fields that are set as query parameters.

    :param user_id: The int ID of a specific user
    :type user_id: int

    :param active: An optional query component/parameter to update whether or not a user is active. If true, user has an activated account that they can log in to, otherwise account will be rejected/suspended from use
    :type active: boolean or None

    :param admin: An optional query component/parameter to update whether or not a user has admin permissions. All admins have same permissions so maybe should create a super admin.
    :type admin: boolean or None

    :param password: An optional query component/parameter to update the password for a user. TODO: actually supporting passwords/salting/hashing.
    :type password: str or None

    :param first_name: An optional query component/parameter to update the user's first name. Does not modify full name stored in database.
    :type first_name: str or None

    :param last_name: An optional query component/parameter to update the user's last name. Does not modify full name stored in database.
    :type last_name: str or None

    :param email: An optional query component/parameter to update the user's email. TODO: email verification.
    :type email: str or None

    :return: JSON of updated user or an error message

    :Requires: Admin permissions

    """
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
    """
    :Route: POST /?user_id=int&full_name=Katrina A. Wijaya&first_name=Katrina&last_name=Wijaya&email=mappeningdevx@gmail.com&active=false&admin=true&password=str&username=str

    :Description: Add a new user with required id `user_id` and any optional fields that are set as query parameters.

    :param user_id: The int ID of a specific user
    :type user_id: int

    :param full_name: An optional query component/parameter to update the user's full name.
    :type full_name: str or None

    :param first_name: An optional query component/parameter to update the user's first name. Does not modify full name stored in database.
    :type first_name: str or None

    :param last_name: An optional query component/parameter to update the user's last name. Does not modify full name stored in database.
    :type last_name: str or None

    :param email: An optional query component/parameter to update the user's email. TODO: email verification.
    :type email: str or None

    :param active: An optional query component/parameter to update whether or not a user is active. If true, user has an activated account that they can log in to, otherwise account will be rejected/suspended from use
    :type active: boolean or None

    :param admin: An optional query component/parameter to update whether or not a user has admin permissions. All admins have same permissions so maybe should create a super admin.
    :type admin: boolean or None

    :param password: An optional query component/parameter to update the password for a user. TODO: actually supporting passwords/salting/hashing.
    :type password: str or None

    :param username: An optional query component/parameter to update the username for a user. TODO: actually supporting usernames.
    :type username: str or None

    :return: Success/error message

    :Requires: Admin permissions

    """
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
    """
    :Route: PUT /activate/<user_id>

    :Description: Reactivates a user with id `user_id`. A user with an activated account can log in. Otherwise account is rejected/suspended from use.

    :param user_id: The unique ID of a specific user
    :type user_id: int

    :return: Success/error message

    :Requires: Admin permissions

    """
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
    """
    :Route: PUT /deactivate/<user_id>

    :Description: Deactivates a user with id `user_id` without deleting user from database. A user with an activated account can log in. Otherwise account is rejected/suspended from use.

    :param user_id: The unique ID of a specific user
    :type user_id: int

    :return: Success/error message

    :Requires: Admin permissions

    """
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
    """
    :Route: DELETE /<user_id>

    :Description: Removes a user with id `user_id`. User information stored in a different database.

    :param user_id: The unique ID of a specific user
    :type user_id: int

    :return: Success/error message

    :Requires: Admin permissions

    """
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

##### Get/add/remove filters #####

@users.route('/<int:user_id>/filter', methods=['GET'])
def get_user_filters(user_id):
    """
    :Route: GET /<user_id>/filter

    :Description: Gets all filters for a single user with id `user_id`

    :param user_id: The unique ID of a specific user
    :type user_id: int

    :return: JSON of specific user's filters

    :Requires: Admin permissions

    """
    # Check that user exists
    user = user_utils.get_user(user_id)
    if not user:
      return "No such user with id " + str(user_id) + " found!"

    # Get user filters
    return jsonify({ 'filters': user['app']['filters'] })

# Replace all filters
@users.route('/<int:user_id>/filter', methods=['PUT'])
def replace_user_filters(user_id):
    """
    :Route: PUT /<user_id>/filter?filter=now&filter=popular

    :Description: Replaces all filters for a single user with id `user_id`. New filters passed by query parameter are validated.

    :param user_id: The unique ID of a specific user
    :type user_id: int

    :param filter: An optional query component/parameter that takes a list of values. Passed in values are validated as filters before being added.
    :type filter: str or None

    :return: Success/error message

    :Requires: Admin permissions

    """
    new_filters = request.args.getlist('filter')

    # Check that user exists
    user = user_utils.get_user(user_id)
    if not user:
      return "No such user with id " + str(user_id) + " found!"

    valid_filters = [f for f in new_filters if user_utils.is_valid_filter(f)]

    users_collection.update({'account.id': str(user_id)}, {'$set': {'app.filters': valid_filters}})

    return "Replaced filters for user with id " + str(user_id)

@users.route('/<int:user_id>/filter', methods=['POST'])
def add_user_filters(user_id):
    """
    :Route: POST /<user_id>/filter?filter=now&filter=popular

    :Description: Add new filters for a single user with id `user_id`. New filters passed by query parameter are validated. Only new filters are added, aka no duplicates are inserted.

    :param user_id: The unique ID of a specific user
    :type user_id: int

    :param filter: An optional query component/parameter that takes a list of values. Passed in values are validated as filters before being added.
    :type filter: str or None

    :return: Success/error message

    :Requires: Admin permissions

    """
    new_filters = request.args.getlist('filter')

    # Check that user exists
    user = user_utils.get_user(user_id)
    if not user:
      return "No such user with id " + str(user_id) + " found!"

    # Get user filters
    updated = False
    added_filters = []
    old_filters = user['app']['filters']

    # Ignore filters already in filters list
    for new_f in [f for f in new_filters if f not in old_filters]:
      # Check that filter is valid and then add to filters list
      if user_utils.is_valid_filter(new_f):
        added_filters.append(new_f)
        updated = True
       
    if updated: 
      users_collection.update({'account.id': str(user_id)}, {'$push': {'app.filters': {'$each': added_filters}}})
      return "Added specified filters for user with id " + str(user_id)

    return "No filters specified to add to user with id " + str(user_id)

@users.route('/<int:user_id>/filter', methods=['DELETE'])
def remove_user_filters(user_id):
    """
    :Route: DELETE /<user_id>/filter?filter=now&filter=popular

    :Description: Remove filters for a single user with id `user_id`. Filters to remove are passed by query parameter. If no filters are specified, all of the user's filters are removed.

    :param user_id: The unique ID of a specific user
    :type user_id: int

    :param filter: An optional query component/parameter that takes a list of values.
    :type filter: str or None

    :return: Success/error message

    :Requires: Admin permissions

    """
    remove_filters = request.args.getlist('filter')

    # Check that user exists
    user = user_utils.get_user(user_id)
    if not user:
      return "No such user with id " + str(user_id) + " found!"

    # If no filters specified, remove all filters from the user
    if not remove_filters:
      users_collection.update({'account.id': str(user_id)}, {'$set': {'app.filters': []}})
      return "Removed all filters for user with id " + str(user_id)

    # Otherwise remove only the filters specified
    users_collection.update({'account.id': str(user_id)}, {'$pull': {'app.filters': {'$in': remove_filters}}})

    return "Removed specified filters for user with id " + str(user_id)

##### Get/add/remove favorite events by id #####

@users.route('/favorites', methods=['GET'])
def get_all_favorites():
    """
    :Route: GET favorites

    :Description: Gets all unique favorited events for all users.

    :return: JSON of all favorited events

    :Requires: Admin permissions

    """
    output = []
    users_cursor = users_collection.find({"app.favorites": {'$not': {'$size': 0}}})

    if users_cursor.count() > 0:
      for user in users_cursor:
        output = output + [fav for fav in user['app']['favorites'] if fav not in output]
    else:
        return 'Cannot find any users with favorites!'

    return jsonify({'favorites': output})

@users.route('/<int:user_id>/favorite', methods=['GET'])
def get_user_favorites(user_id):
    """
    :Route: GET /<user_id>/favorite

    :Description: Gets all favorited events for a single user with id `user_id`

    :param user_id: The unique ID of a specific user
    :type user_id: int

    :return: JSON of specific user's favorited events

    :Requires: Admin permissions

    """
    # Check that user exists
    user = user_utils.get_user(user_id)
    if not user:
      return "No such user with id " + str(user_id) + " found!"

    # Get user filters
    return jsonify({ 'filters': user['app']['favorites'] })

@users.route('/<int:user_id>/favorite', methods=['POST'])
def add_user_favorite(user_id):
    """
    :Route: POST /<user_id>/favorite?favorite=event_id&favorite=event_id

    :Description: Add new favorited events for a single user with id `user_id`. Only unique events are added, aka no duplicates are inserted.

    :param user_id: The unique ID of a specific user
    :type user_id: int

    :param favorite: An optional query component/parameter that takes a list of values. Passed in values are int event IDs which uniquely identify an event.
    :type favorite: int or None

    :return: Success/error message

    :Requires: Admin permissions

    """
    new_favorites = request.args.getlist('favorite')

    # Check that user exists
    user = user_utils.get_user(user_id)
    if not user:
      return "No such user with id " + str(user_id) + " found!"

    # Get user favorites
    updated = False
    added_favorites = []
    old_favorites = user['app']['favorites']

    # Ignore favorites already in favorites list
    for new_f in [f for f in new_favorites if f not in old_favorites]:
      added_favorites.append(new_f)
      updated = True
       
    if updated: 
      users_collection.update({'account.id': str(user_id)}, {'$push': {'app.favorites': {'$each': added_favorites}}})
      return "Added specified favorites for user with id " + str(user_id)

    return "No favorites specified to add to user with id " + str(user_id)

# If no favorite specified deletes all favorites, otherwise only deletes those specified
@users.route('/<int:user_id>/favorite', methods=['DELETE'])
def remove_user_favorites(user_id):
    """
    :Route: DELETE /<user_id>/favorite?favorite=event_id&favorite=event_id

    :Description: Remove favorited events for a single user with id `user_id`. If no favorited events are specified, all of the user's favorited events are removed.

    :param user_id: The unique ID of a specific user
    :type user_id: int

    :param favorite: An optional query component/parameter that takes a list of values. Passed in values are int event IDs which uniquely identify an event.
    :type favorite: int or None

    :return: Success/error message

    :Requires: Admin permissions

    """
    remove_favorites = request.args.getlist('favorite')

    # Check that user exists
    user = user_utils.get_user(user_id)
    if not user:
      return "No such user with id " + str(user_id) + " found!"

    # If no favorites specified, remove all favorites from the user
    if not remove_favorites:
      users_collection.update({'account.id': str(user_id)}, {'$set': {'app.favorites': []}})
      return "Removed all favorites for user with id " + str(user_id)

    # Otherwise remove only the favorites specified
    users_collection.update({'account.id': str(user_id)}, {'$pull': {'app.favorites': {'$in': remove_favorites}}})

    return "Removed specified favorites for user with id " + str(user_id)

##### Get/add/remove past events by id #####

@users.route('/<int:user_id>/past', methods=['GET'])
def get_user_past_events(user_id):
    """
    :Route: GET /<user_id>/past

    :Description: Gets all past events for a single user with id `user_id`

    :param user_id: The unique ID of a specific user
    :type user_id: int

    :return: JSON of specific user's past events

    :Requires: Admin permissions

    """
    # Check that user exists
    user = user_utils.get_user(user_id)
    if not user:
      return "No such user with id " + str(user_id) + " found!"

    # Get user filters
    return jsonify({ 'filters': user['app']['past_events'] })

@users.route('/<int:user_id>/past', methods=['POST'])
def add_user_past_events(user_id):
    """
    :Route: POST /<user_id>/past?past_event=event_id&past_event=event_id

    :Description: Add new past events for a single user with id `user_id`. Only unique events are added, aka no duplicates are inserted.

    :param user_id: The unique ID of a specific user
    :type user_id: int

    :param past_event: An optional query component/parameter that takes a list of values. Passed in values are int event IDs which uniquely identify an event.
    :type past_event: int or None

    :return: Success/error message

    :Requires: Admin permissions

    """
    new_past_events = request.args.getlist('past_event')

    # Check that user exists
    user = user_utils.get_user(user_id)
    if not user:
      return "No such user with id " + str(user_id) + " found!"

    # Get user past events
    updated = False
    added_events = []
    old_past_events = user['app']['past_events']

    # Ignore past events already in past events list
    for new_f in [f for f in new_past_events if f not in old_past_events]:
      added_events.append(new_f)
      updated = True
       
    if updated: 
      users_collection.update({'account.id': str(user_id)}, {'$push': {'app.past_events': {'$each': added_events}}})
      return "Added specified past events for user with id " + str(user_id)

    return "No past events specified to add to user with id " + str(user_id)

# If no favorite specified deletes all favorites, otherwise only deletes those specified
@users.route('/<int:user_id>/past', methods=['DELETE'])
def remove_user_past_events(user_id):
    """
    :Route: DELETE /<user_id>/past?past_event=event_id&past_event=event_id

    :Description: Remove past events for a single user with id `user_id`. If no past events are specified, all of the user's past events are removed.

    :param user_id: The unique ID of a specific user
    :type user_id: int

    :param past_event: An optional query component/parameter that takes a list of values. Passed in values are int event IDs which uniquely identify an event.
    :type past_event: int or None

    :return: Success/error message

    :Requires: Admin permissions

    """
    remove_past_events = request.args.getlist('past_event')

    # Check that user exists
    user = user_utils.get_user(user_id)
    if not user:
      return "No such user with id " + str(user_id) + " found!"

    # If no past events specified, remove all past events from the user
    if not remove_past_events:
      users_collection.update({'account.id': str(user_id)}, {'$set': {'app.past_events': []}})
      return "Removed all past events for user with id " + str(user_id)

    # Otherwise remove only the past events specified
    users_collection.update({'account.id': str(user_id)}, {'$pull': {'app.past_events': {'$in': remove_past_events}}})

    return "Removed specified past events for user with id " + str(user_id)
