# Starter app.py that connects to mlab database
from mappening import app

from flask import Flask

import schedule
import time, datetime, pytz
from dateutil.tz import tzlocal
from threading import Thread

'''
DOCKER CONTAINER TIME ZONE IS UTC!
'''
# (hour, minute) pairs for when to refresh events every day (using 24 hour clock), IN LA TIME
update_time_tuples = [(5, 0), (13, 10), (19, 10)]
event_refresh_tag = 'event-refresh'

@app.route('/')
def index():
    return "Mappening is running!"

def update_for_today():
    # remove current refresh and replace with new ones, in case of daylight savings maybe
    schedule.clear(event_refresh_tag)
    today = pytz.timezone('America/Los_Angeles').localize(datetime.datetime.now())

    for (hour, minute) in update_time_tuples:
        today = today.replace(hour=hour, minute=minute)
        adjusted_time = today.astimezone(pytz.UTC).strftime('%H:%M')
        schedule.every().day.at(adjusted_time).do(update_ucla_events_database).tag(event_refresh_tag)
        print('Refresh at {0}, in UTC'.format(adjusted_time))
    print('Schedule {0} times on {1}'.format(len(update_time_tuples), str(today.date())))

def event_thread_func():
    # need to change the day every day, so that DST is accounted for when applicable
    update_for_today()
    schedule.every().day.at('00:00').do(update_for_today).tag('daily-refresh')

    # time INSIDE container, which is GMT both local and AWS, +8 hours from Los Angeles without DST
    # so 13:00 GMT --> 5 AM in LA, 21:00 GMT --> 1 PM, 03:00 GMT --> 7 PM, if DST: all LA hours +1
    # schedule.every().day.at('13:00').do(update_ucla_events_database)
    # # update later than the hour, removing events starting at those hours, for late people
    # schedule.every().day.at('21:10').do(update_ucla_events_database)
    # schedule.every().day.at('03:10').do(update_ucla_events_database)
    while True:
        schedule.run_pending()
        # kind of like a check every interval of time, if any jobs should run
        time.sleep(30)

if __name__ == "__main__":
    # # Another thread to run the periodic events update, daily
    # event_update_thread = Thread(target = event_thread_func)
    # event_update_thread.start()

    # code_update_date = "2/15/18"
    # print("Updated on: {0}".format(code_update_date))

    # if debug is true, will run 2 instances at once (so two copies of all threads)
    app.run(host='0.0.0.0', debug=False)
    # Flask defaults to port 5000

