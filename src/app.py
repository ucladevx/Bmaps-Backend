# Run this before anything else: checks for command line arguments
# Default: no arguments, liked when using Makefile (normal API backend running)
import argparse
parser = argparse.ArgumentParser()
# To turn option into flag, use action= parameter: calls a predefined function
# store_true is one of many default functions for action=, later can check args.test = True
parser.add_argument('-t', '--test', help='Use a test database, to protect live data.', action='store_true')
parser.add_argument('-d', '--days-before', help='Specify # of days to go back in time for past events.', type=int)
parser.add_argument('-c', '--clear', help='Clear out old database data to start anew.', action='store_true')
parser.add_argument('-p', '--prod', help='Run production version of Mappening backend', action='store_true')
args = parser.parse_args()

# There's an 'app' Flask object in mappening's __init__.py
# App object also links to blueprints to other modules
from mappening import app, db
from mappening.models import Address
from mappening.utils import scheduler
from mappening.api.utils.events import event_collector
from mappening.api.utils.eventbrite import eb_event_collector, eb_event_processor

from flask import Flask, jsonify, request
import datetime
from threading import Thread

# Used to check app is running, visit http://api.mappening.io:5000/
@app.route('/')
def index():
    return "The Mappening API is running!"

# Sample database route
@app.route('/db')
def test():
    return jsonify(addresses=[address.serialize() for address in Address.query.all()])

# https://www.jordanbonser.com/flask-session-timeout.html
# @app.before_request
# def before_request():
#     flask.session.permanent = True
#     app.permanent_session_lifetime = datetime.timedelta(minutes=20)

# Runs threads to periodically update events. Also updates database.
# For dev purposes, only call this when we are in prod.
def thread_scheduler(args):
    # Another thread to run the periodic events update, daily
    event_update_thread = Thread(target = scheduler.event_thread_func)
    event_update_thread.start()

    code_update_date = "6/1/18"
    print("Updated on: {0}".format(code_update_date))

    print("UPDATE EVENTS FIRST...\n")
    dbit = args.days_before
    # pass in args from command line, need to check it's there
    if not dbit or dbit < 1:
        dbit = 0
    event_collector.update_ucla_events_database(use_test=args.test,
                                            days_back_in_time=dbit,
                                            clear_old_db=args.clear)

# Flask defaults to port 5000
# If debug is true, runs 2 instances at once (so two copies of all threads)
if __name__ == "__main__":
    print('Arguments passed: {0}'.format(args))
    if not args.prod:
        print("\n~~~~~~~~~~~~~~~~~~~\n~~~ IN DEV MODE ~~~\n~~~~~~~~~~~~~~~~~~~\n")
        app.run(host='0.0.0.0', debug=True)
    else:
        print("\n~~~~~~~~~~~~~~~~~~~~\n~~~ IN PROD MODE ~~~\n~~~~~~~~~~~~~~~~~~~~\n")
        # TODO: Breaks EB deployment. cron jobs?
        thread_scheduler(args)
        app.run(host='0.0.0.0', debug=False)
