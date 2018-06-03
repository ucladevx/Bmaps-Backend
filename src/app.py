# run this before anything else: checks for command line arguments
# default: no arguments, liked when using Makefile (normal API backend running)
import argparse
parser = argparse.ArgumentParser()
# to turn option into flag, use action= parameter: calls a predefined function
# store_true is one of many default functions for action=, later can check args.test = True
parser.add_argument('-t', '--test', help='Use a test database, to protect live data.', action='store_true')
parser.add_argument('-d', '--days-before', help='Specify # of days to go back in time for past events.', type=int)
parser.add_argument('-c', '--clear', help='Clear out old database data to start anew.', action='store_true')
args = parser.parse_args()

# if ever need to quit early, call sys.exit()
import sys

# there's an 'app' Flask object in mappening's __init__.py, which also links to blueprints to other modules

from mappening import app
from mappening.utils import scheduler
from mappening.api.utils import event_utils

from flask import Flask
import datetime

from threading import Thread

@app.route('/')
def index():
    return "Mappening is running!"

# https://www.jordanbonser.com/flask-session-timeout.html
# @app.before_request
# def before_request():
#     flask.session.permanent = True
#     app.permanent_session_lifetime = datetime.timedelta(minutes=20)

if __name__ == "__main__":
    print('Arguments passed: {0}'.format(args))
    # sys.exit()

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
    event_utils.update_ucla_events_database(use_test=args.test,
                                            days_back_in_time=dbit,
                                            clear_old_db=args.clear)

    # GOOD TO KNOW
    # to QUIT when not in Docker container: run Ctrl+\ (SIGQUIT, equivalent to kill -3 <pid>)
    # FORCE QUIT: Ctrl-Z to pause + put in background + add to 'jobs' list
    # THEN kill -9 %1 to UNCONDITIONALLY eliminate job #1, which is this python script

    # Flask defaults to port 5000
    # If debug is true, runs 2 instances at once (so two copies of all threads)
    app.run(host='0.0.0.0', debug=False)

