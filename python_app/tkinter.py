from Tkinter import *
import tkMessageBox

import pymongo
import os
from dotenv import load_dotenv

# Get environment vars for keeping sensitive info secure
# Has to come before blueprints that use the env vars
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
MLAB_USERNAME = os.getenv('MLAB_USERNAME')
MLAB_PASSWORD = os.getenv('MLAB_PASSWORD')

uri = 'mongodb://{0}:{1}@ds044709.mlab.com:44709/mappening_data'.format(MLAB_USERNAME, MLAB_PASSWORD)

# Set up database connection
client = pymongo.MongoClient(uri)
db = client['mappening_data'] 
unknown_locs_collection = db.test_unknown_locations

unknown_locations = []
locations_cursor = unknown_locs_collection.find({}, {'_id': False})
if locations_cursor.count() > 0:
  for loc in locations_cursor:
    unknown_locations.append(loc['location_name'])
else:
    print 'Cannot find any locations in database!'
    quit()

class App:

  def __init__(self, master):
    frame = Frame(master)
    frame.pack()

    self.button = Button(frame, text="QUIT", command= lambda: self.quit(frame))
    self.button.pack(side=LEFT)

    self.correct = Button(frame, text="CORRECT", command=self.isCorrect)
    self.correct.pack(side=LEFT)

    self.wrong = Button(frame, text="WRONG", command=self.isWrong)
    self.wrong.pack(side=LEFT)

    self.skip = Button(frame, text="SKIP", command=self.changeText)
    self.skip.pack(side=LEFT)

  def isCorrect(self):
    print "Location in UCLA, keep in database"
    self.changeText()

  def isWrong(self):
    print "Location not in UCLA or an outlier, remove from database"
    unknown_locs_collection.delete_one({'location_name': unknown_locations[0]})
    self.changeText()

  def quit(self, frame):
    choice = tkMessageBox.askquestion("Ready to quit?", "Thanks for your help!", icon='warning')
    if choice == 'yes':
      frame.quit()
    else:
      print "Not done yet!"

  def changeText(self):
    unknown_locations.pop(0)
    if unknown_locations:
      location.set(unknown_locations[0])
    else:
      location.set("No more locations to check")
      self.correct.config(state = DISABLED)
      self.wrong.config(state = DISABLED)
      self.skip.config(state = DISABLED)


root = Tk()

question = Label(root, text="Is this event location in UCLA/Westwood?", font=("Open Sans", 20))
question.pack()

location = StringVar()
Label(root, textvariable=location, font=("Open Sans", 14)).pack()

location.set(unknown_locations[0])

app = App(root)

root.mainloop()
