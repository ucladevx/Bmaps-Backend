from mappening.utils.database import *
import event_caller

from flask import Flask, jsonify, request, json, Blueprint
from tqdm import tqdm

pages = Blueprint('pages', __name__)

# TODO: new endpoint to manually add Facebook page to DB
# event_caller.add_facebook_page returns array of 1 or multiple pages (if search)
# assume that if search returns multiple, insert/update up to the first 3 (hopefully desired page included there)
# use URL parameters, either id= or name=, and optional type=page, group, or place if needed (default = group)
@pages.route('/add/id/<page_id>', defaults={'page_type': 'group'}, methods=['POST'])
@pages.route('/add/id/<page_id>/<page_type>', methods=['POST'])
def add_page_from_id(page_id, page_type):
    """
    :Route: /add/id/<page_id>/<page_type>

    :Description: Find official page info from Graph API given search items, and add to or update the page collection on DB as needed.

    :param str page_id: a unique identifier used to find a page. Either a long number or a page's unique string ID (found in its Facebook URL TODO: example). Preferred method of search.

    :param page_type: the case-insensitive type of page desired, either 'page', 'place', or 'group'. Defaults to 'group' if not specified.
    :type page_type: str or None
    
    """
    page_type = page_type.lower()

    page_result = event_caller.add_facebook_page_from_id(page_id, page_type)
    if 'error' in page_result:
        return page_result['error']

    found_same_page = saved_pages_collection.find_one({'id': page_result['id']})

    return page_result

@pages.route('/add/search/<search_string>', defaults={'page_type': 'group'}, methods=['POST'])
@pages.route('/add/search/<search_string>/<page_type>', methods=['POST'])
def add_page_from_search(search_string, page_type):
    """
    :Route: /add/search/<search_string>/<page_type>

    :Description: Find official page info from Graph API given search items, and add to or update the page collection on DB as needed.

    :param str search-string: if 'page_id' parameter is not available, set this to a search word / phrase as specific as possible. Will attempt to find closely matching pages on Facebook and save them to DB.
    
    :param page_type: the case-insensitive type of page desired, either 'page', 'place', or 'group'. Defaults to 'group' if not specified.
    :type page_type: str or None
    
    """
    page_type = page_type.lower()
    
    page_result = event_caller.add_facebook_page_from_search(search_string, page_type)
    if 'error' in page_result:
        return page_result['error']

    found_same_page = saved_pages_collection.find_one({'id': page_result['id']})

    return page_result

# TODO is this supposed to be a public route
# Now refresh pages we search separately, can be done way less frequently than event search
@pages.route('/refresh-page-database')
def refresh_page_database():
    # separately run from refreshing events, also check for new pages under set of search terms
    print('Refreshing pages...')

    # update just like accumulated events list
    # remember: find() just returns a cursor, not whole data structure
    # saved_pages = saved_pages_collection.find()
    # returns a dict of IDs to names
    raw_page_data = event_caller.find_ucla_entities()
    print('Found them.')
    # raw_page_data = {"test_id": "test_name"}

    new_page_count = 0
    updated_page_count = 0
    # in contrast to raw_page_data, saved_pages_collection is list of {"id": <id>, "name": <name>}
    for page_id, page_name in tqdm(raw_page_data.iteritems()):
        # See if event already existed
        update_page = saved_pages_collection.find_one({'id': page_id})

        # If it existed then delete it, new event gets inserted in both cases
        if update_page:
            saved_pages_collection.delete_one({'id': page_id})
            updated_page_count += 1
            new_page_count -= 1
        saved_pages_collection.insert_one({'id': page_id, 'name': page_name})
        new_page_count += 1

    return 'Refreshed database pages: {0} new, {1} updated.'.format(new_page_count, updated_page_count)
