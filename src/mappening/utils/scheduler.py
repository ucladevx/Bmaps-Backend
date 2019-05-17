from mappening.api.utils.events import getting_data, processing_data
from mappening.utils.database import events_log_collection

import schedule
import time, datetime, pytz
from dateutil.tz import tzlocal
from threading import Thread

# "return a StringIO-like stream for reading and writing"
# basically allows stdoutput to be saved into a stream
from cStringIO import StringIO
import sys, traceback

# (hour, minute) pairs for when to refresh events every day (using 24 hour clock), IN LA TIME
update_time_tuples = [(5, 0), (13, 10), (19, 10)]
event_refresh_tag = 'event-refresh'

# log output of update event call in DB!
# store stdout into string, then save and print it out
def get_new_events_with_logs():
    """
    stdout is file descriptor? like a pointer to a location to print (e.g. terminal output)
    what this does is save the original place of stdout printing (the terminal) before the output
    is redirected to a string, so that when string printing is done, it can get pointed back to
    its original location (the terminal) again if needed
    note: sys.__stdout__ ALWAYS points to the terminal anyway, could use it to redirect back
    """
    print('\n\n\n\n\n\n\n\n######\n\n######\n\n######\n\n')
    print('BEGIN POPULATING EVENTS DATABASE')
    print('\n\n######\n\n######\n\n######\n\n\n\n\n\n\n')

    log_dict = {}

    orig_stdout = sys.stdout
    saved_output = StringIO()
    # save all output of event updating call only
    sys.stdout = saved_output
    try:
        event_utils.update_ucla_events_database()
    except KeyboardInterrupt:
        print('Received KeyboardInterrupt somehow.')
    except SystemExit:
        print('Requested to exit system.')
    # all other exceptions: note that error occurred
    except:
        print(traceback.format_exc())
        log_dict['ERROR'] = True
    sys.stdout = orig_stdout
    saved_output_str = saved_output.getvalue()
    
    # save into mLab
    log_timestr = pytz.timezone('America/Los_Angeles') \
                    .localize(datetime.datetime.now()) \
                    .strftime('%Y-%m-%d %H:%M:%S')
    log_dict[log_timestr] = saved_output_str
    events_log_collection.insert_one(log_dict)
    # print out into terminal anyway
    print(saved_output_str)

def update_for_today():
    # remove current refresh and replace with new ones, in case of daylight savings maybe
    schedule.clear(event_refresh_tag)
    today = pytz.timezone('America/Los_Angeles').localize(datetime.datetime.now())

    for (hour, minute) in update_time_tuples:
        today = today.replace(hour=hour, minute=minute)
        adjusted_time = today.astimezone(pytz.UTC).strftime('%H:%M')
        # call update_u_e_d with no arguments, so defaults used
        schedule.every().day.at(adjusted_time).do(get_new_events_with_logs).tag(event_refresh_tag)
        print('Refresh at {0}, in UTC'.format(adjusted_time))
    print('Schedule {0} times on {1}'.format(len(update_time_tuples), str(today.date())))

def event_thread_func():
    update_for_today()
    # need to reschedule every day, so that time zone changes (like DST) take effect
    schedule.every().day.at('00:00').do(update_for_today).tag('daily-refresh')

    # old way: this is time inside Docker container, which is UTC!
    # schedule.every().day.at('21:10').do(event_utils.update_ucla_events_database)
    
    while True:
        schedule.run_pending()
        # kind of like a check every interval of time, if any jobs should run
        time.sleep(30)
