from mappening.utils.database import users_collection, dead_users_collection

from flask import Flask, jsonify, redirect, url_for, request, Blueprint
from flask_login import current_user
from flask_cors import CORS, cross_origin
from datetime import datetime

# Get single user
def get_user(user_id):
    # Check that user exists
    user = users_collection.find_one({'account.id': str(user_id)}, {'_id': False})
    if user:
        return user
    return None

# Add a new user to users collection 
def add_user(user_id, full_name, first_name, last_name, email='', is_active=True, is_admin=False, password='', username=''):
  # Check if user already exists in collection
  if get_user(user_id):
    return "User with id " + str(user_id) + " already exists!"

  # Insert new user
  users_collection.insert_one({
    "account": {
      "id": user_id,
      "is_active": is_active,
      "is_admin": is_admin,
      "password_hash": password,  # TODO: we don't actually support username/passwords
      "username": username,
      "time_joined": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # in UTC I think
      "time_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    },
    "personal_info": {
      "full_name": full_name,
      "first_name": first_name,
      "last_name": last_name,
      "email": email
    },
    "app": {
      "filters": [],
      "favorites": [],
      "past_events": []
    }
  })

  # Check that user was successfully added to collection
  if get_user(user_id):
    return "User with id " + str(user_id) + " successfully added!"
  else:
    return "Adding user with id " + str(user_id) + " failed!"

# Check that filter is one of accepted filters
def is_valid_filter(f):
  valid_filters = ['now', 'upcoming', 'period', 'morning', 'afternoon', 'night', 'oncampus', 'offcampus', 'nearby', 'popular', 'food']
  
  if f in valid_filters:
    return True
  return False
