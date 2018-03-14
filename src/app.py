from mappening import app
from mappening.utils import scheduler

from flask import Flask

from threading import Thread

@app.route('/')
def index():
    return "Mappening is running!"

if __name__ == "__main__":
    # Another thread to run the periodic events update, daily
    event_update_thread = Thread(target = scheduler.event_thread_func)
    event_update_thread.start()

    code_update_date = "2/15/18"
    print("Updated on: {0}".format(code_update_date))

    print "Mappening is happening!"

    # Flask defaults to port 5000
    # If debug is true, runs 2 instances at once (so two copies of all threads)
    app.run(host='0.0.0.0', debug=False)

    

