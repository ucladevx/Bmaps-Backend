# TODO LMAO HOW TO WEB DEV

# Get all possible user preferences
@users.route('/', methods=['GET'])

# Check if a preference is valid
@users.route('/<preference>', methods=['GET'])

# Add a preference
@users.route('/<preference>', methods=['POST'])

# Delete a preference from all users with it

# Add user preference
@users.route('/api/add-user-preference')
def add_user_preference():
    pref = request.args['preference']
    u_id = request.args['user_id']

    user = map_users_collection.find_one({'user_id': u_id})

    # Check that user exists
    if user == None:
      return redirect(url_for('Users.error_message', error_code=2))

    # Update user to add preference
    # If preference was already in user list, does not add duplicate
    if pref in user['preferences']:
      return redirect(url_for('Users.error_message', error_code=4))
    else:
      map_users_collection.update({'user_id': u_id}, 
        {'$push': {'preferences': pref}})

    # Check that preference was successfully added to user
    user = map_users_collection.find_one({'user_id': u_id})
    if pref in user['preferences']:
      return redirect(url_for('Users.success_message', success_code=3))
    else:
      return redirect(url_for('Users.error_message', error_code=5))

# Remove user preference
@users.route('/api/remove-user-preference')
def remove_user_preference():
    pref = request.args['preference']
    u_id = request.args['user_id']

    user = map_users_collection.find_one({'user_id': u_id})

    # Check that user exists
    if user == None:
      return redirect(url_for('Users.error_message', error_code=2))

    # If preference exists in user preferences list, remove it
    if pref in user['preferences']:
      map_users_collection.update({'user_id': u_id}, 
        {'$pull': {'preferences': pref}})
    else:
      return redirect(url_for('Users.error_message', error_code=6))      

    # Check that preference was successfully removed from user preferences
    user = map_users_collection.find_one({'user_id': u_id})
    if pref in user['preferences']:
      return redirect(url_for('Users.error_message', error_code=7))
    else:
      return redirect(url_for('Users.success_message', success_code=4))

# Get a user preferences from user_id 
@users.route('/api/user-preferences/<user_id>', methods=['GET'])
def get_user_preferences(user_id):
    # Check that user exists
    if map_users_collection.find_one({'user_id': user_id}) == None:
      return redirect(url_for('Users.error_message', error_code=2))

    # Get user preferences
    preferences = map_users_collection.find_one({'user_id': user_id})['preferences']

    # Check if preferences is empty
    if not preferences:
        return redirect(url_for('Users.error_message', error_code=8))

    return jsonify(preferences)

# Check whether a user preference exists for a certain user_id
@users.route('/api/user-preference-exists', methods=['GET'])
def user_preference_exists():
    pref = request.args['preference']
    u_id = request.args['user_id']

    user = map_users_collection.find_one({'user_id': u_id})

    # Check that user exists
    if user == None:
      return redirect(url_for('Users.error_message', error_code=2))

    # Check if preference exists in user preferences list
    if pref in user['preferences']:
      return redirect(url_for('Users.success_message', success_code=5))
    else:
      return redirect(url_for('Users.error_message', error_code=6))

# Get all users with that preference
@users.route('/api/users-with-preference/<pref>', methods=['GET'])
def get_users_with_preference(pref):
    output = []
    for doc in map_users_collection.find():
      if pref in doc['preferences']:
        output.append({'user_id': doc['user_id'],
                       'user_name': doc['user_name']})

    return jsonify(output)
