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
unknown_locs_collection = db.tkinter_UCLA_locations

unknown_locations = []
locations_cursor = unknown_locs_collection.find({}, {'_id': False})
if locations_cursor.count() > 0:
  for loc in locations_cursor:
    if 'isUCLA' in loc: 
      if not loc['isUCLA']:
        unknown_locations.append(loc['location_name'])
    else:
      unknown_locations.append(loc['location_name'])
else:
    print 'Cannot find any locations in database!'
    quit()

class App:

  def __init__(self, master):
    frame = Frame(master)
    frame.pack()

    self.correct = Button(frame, text="CORRECT", command=self.isCorrect)
    self.correct.pack(side=LEFT)

    self.wrong = Button(frame, text="WRONG", command=self.isWrong)
    self.wrong.pack(side=LEFT)

    self.skip = Button(frame, text="SKIP", command=self.changeText)
    self.skip.pack(side=LEFT)

    self.help = Button(frame, text="HELP", command=self.helpInstructions)
    self.help.pack(side=LEFT)

    self.button = Button(frame, text="QUIT", command= lambda: self.quit(frame))
    self.button.pack(side=LEFT)

  def isCorrect(self):
    print "Location in UCLA, marking as checked: " + unknown_locations[0]

    location = unknown_locs_collection.find_one({'location_name': unknown_locations[0]})
    location['isUCLA'] = True

    unknown_locs_collection.replace_one({'_id': location['_id']}, location.copy()) 

    self.changeText()

  def isWrong(self):
    print "Location not in UCLA or an outlier, remove from database: " + unknown_locations[0]
    unknown_locs_collection.delete_one({'location_name': unknown_locations[0]})
    self.changeText()

  def helpInstructions(self):
    print "Displaying instructions!"

    tkMessageBox.showinfo(
      "Instructions",
      "Hello! Thanks for your help checking whether or not these locations we scraped are even in UCLA/Westwood. Check us out at www.whatsmappening.io!\n\nHere's what the buttons do:\nCORRECT: The location name is in UCLA, approve the location!\n\nWRONG: The location isn't in UCLA/Westwood, reject it!\n\nSKIP: Confused or don't know what to do with a particular location? Just skip it!\n\nHELP: As you can tell, this one leads to the instructions!\n\nQUIT: Exit from the display and be on your merry way! Thanks for your help!"
    )

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
root.geometry("+%d+%d" % (450, 200))

question = Label(root, text="Is this event location in UCLA/Westwood?", font=("Open Sans", 20))
question.pack()

location = StringVar()
Label(root, textvariable=location, font=("Open Sans", 14)).pack()

if unknown_locations:
  location.set(unknown_locations[0])
else:
  location.set("No more locations to check")
  self.correct.config(state = DISABLED)
  self.wrong.config(state = DISABLED)
  self.skip.config(state = DISABLED)

app = App(root)

root.mainloop()
