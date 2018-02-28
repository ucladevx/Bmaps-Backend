from Tkinter import *
import tkMessageBox
import tkSimpleDialog

import webbrowser

import time
from selenium import webdriver

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
tkinter_unknown_collection = db.tkinter_unknown_locations
tkinter_known_collection = db.tkinter_known_locations
tkinter_TODO_collection = db.tkinter_TODO_locations
# TODO: merge tkinter_known_locations into existing UCLA_locations
# TODO: manually fix tkinter_TODO_locations
# TODO: keep checking unknown locations until tkinter_unknown_locations is empty

unknown_locations = []
locations_cursor = tkinter_unknown_collection.find({}) #, {'_id': False})
if locations_cursor.count() > 0:
  for loc in locations_cursor:
    unknown_locations.append(loc)
else:
    print 'Cannot find any locations in database!'
    quit()

dr = webdriver.Chrome()

# Get initial window size
width = dr.get_window_size()['width']
height = dr.get_window_size()['height']

# Set window size
dr.set_window_size(width, height - 200)

# Get window position
x = dr.get_window_position()['x']
y = dr.get_window_position()['y']

# Set window position
dr.set_window_position(x, y + 225);

dr.get("https://stackoverflow.com/")
# dr.get("http://whatsmappening.io")
# BUG: cannot start with a google site or else it'll give "unknown error: $ is not defined"
# Also other websites but idk why
# dr.get("http://www.google.com/maps/")

class App:

  def __init__(self, master):
    frame = Frame(master)
    frame.pack()

    self.correct = Button(frame, text="CORRECT location data!", command=self.isCorrect)
    self.correct.pack(side=LEFT)

    self.wrong = Button(frame, text="Location data is WRONG!", command=self.isWrong)
    self.wrong.pack(side=LEFT)

    self.fail = Button(frame, text="Wrong location found!", command=self.isFail)
    self.fail.pack(side=LEFT)

    self.skip = Button(frame, text="SKIP location", command=self.changeText)
    self.skip.pack(side=LEFT)

    self.help = Button(frame, text="HELP", command=self.helpInstructions)
    self.help.pack(side=LEFT)

    self.button = Button(frame, text="QUIT", command= lambda: self.quit(frame))
    self.button.pack(side=LEFT)

  def isCorrect(self):
    print "Coordinates are correct! Add to different database and remove from test database"

    tkinter_known_collection.insert_one(unknown_locations[0])
    tkinter_unknown_collection.delete_one({'_id': unknown_locations[0]['_id']})

    self.changeText()

  def isWrong(self):
    print "Coordinates are wrong, enter correct location data and update database"
    print "Leaving location in database for secondary verification"

    latitude = tkSimpleDialog.askfloat("Latitude", "Enter latitude value:", initialvalue=unknown_locations[0]['db_loc']['loc_latitude'], minvalue=34.05, maxvalue=34.08)
    longitude = tkSimpleDialog.askfloat("Longitude", "Enter longitude value:",initialvalue=unknown_locations[0]['db_loc']['loc_longitude'], minvalue=-118.46, maxvalue=-118.43)
    name = tkSimpleDialog.askstring("Alternate Name", "Enter alternate name or click cancel:")

    updated = False
    if latitude != unknown_locations[0]['db_loc']['loc_latitude']:
      print "New latitude: " + str(latitude)
      unknown_locations[0]['db_loc']['loc_latitude'] = latitude
      updated = True
    if longitude != unknown_locations[0]['db_loc']['loc_longitude']:
      print "New longitude: " + str(longitude)
      unknown_locations[0]['db_loc']['loc_longitude'] = longitude
      updated = True
    if name and name.lower() not in (alt.lower() for alt in unknown_locations[0]['db_loc']['loc_alt_names']):
      print "New name: " + name
      unknown_locations[0]['db_loc']['loc_alt_names'].append(name)
      updated = True

    if updated:
      print "Updating location in database..."
      tkinter_unknown_collection.replace_one({'_id': unknown_locations[0]['_id']}, unknown_locations[0]) 

    self.changeText()

  def isFail(self):
    print "Not even the right location found... add to different database for manual correction"
    print "Removing from test database"

    tkinter_TODO_collection.insert_one(unknown_locations[0])
    tkinter_unknown_collection.delete_one({'_id': unknown_locations[0]['_id']})

    self.changeText()

  def helpInstructions(self):
    print "Displaying instructions!"

    tkMessageBox.showinfo(
      "Instructions",
      "Hello! Thanks for your help checking whether or not our locations are right. Check us out at www.whatsmappening.io!\n\nHere's what the buttons do:\n\nCORRECT: The information displayed and the pin on the map all seem to be right, approve the location!\n\nWRONG: Something seems to be wrong... the location name matches the location data, but perhaps the coordinates are off. Please fix the coordinates for us!\n\nWrong location found: The location name doesn't seem to match the location data displayed... we'll take care of this one from here!\n\nSKIP: Confused or don't know what to do with a particular location? Just skip it!\n\nHELP: As you can tell, this one leads to the instructions!\n\nQUIT: Exit from the displays and be on your merry way! Thanks for your help!"
    )

  def quit(self, frame):
    choice = tkMessageBox.askquestion("Ready to quit?", "Thanks for your help!", icon='warning')
    if choice == 'yes':
      dr.quit()
      frame.quit()
    else:
      print "Not done yet!"

  def changeText(self):
    unknown_locations.pop(0)
    if unknown_locations:
      location.set("LOCATION NAME: " + unknown_locations[0]['unknown_loc']['loc_name'])
      latitude_str.set("LATITUDE: " + str(unknown_locations[0]['db_loc']['loc_latitude']))
      longitude_str.set("LONGITUDE: " + str(unknown_locations[0]['db_loc']['loc_longitude']))

      alt_names = "ALTERNATIVE NAMES:\n=================="
      for name in unknown_locations[0]['db_loc']['loc_alt_names']:
        alt_names = alt_names + "\n" + name
      alternate_names.set(alt_names)

      # Open Maps display to next coordinates
      dr.get(unknown_locations[0]['db_loc']['map_url'])
    else:
      location.set("No more locations to check!")
      latitude_str.set("Thanks for all your help!")
      longitude_str.set("")
      alternate_names.set("~ Mappening Team ~")

      self.correct.config(state = DISABLED)
      self.wrong.config(state = DISABLED)
      self.fail.config(state = DISABLED)
      self.skip.config(state = DISABLED)


root = Tk()
root.geometry("+%d+%d" % (300, 0))

question = Label(root, text="Is this location in the correct place?", font=("Open Sans", 20))
question.pack()

location = StringVar()
Label(root, textvariable=location, font=("Open Sans", 14)).pack()

latitude_str = StringVar()
Label(root, textvariable=latitude_str, font=("Open Sans", 12)).pack()

longitude_str = StringVar()
Label(root, textvariable=longitude_str, font=("Open Sans", 12)).pack()

alternate_names = StringVar()
Label(root, textvariable=alternate_names, font=("Open Sans", 12)).pack()

location.set("LOCATION NAME: " + unknown_locations[0]['unknown_loc']['loc_name'])
latitude_str.set("LATITUDE: " + str(unknown_locations[0]['db_loc']['loc_latitude']))
longitude_str.set("LONGITUDE: " + str(unknown_locations[0]['db_loc']['loc_longitude']))

alt_names = "ALTERNATIVE NAMES:\n=================="
for name in unknown_locations[0]['db_loc']['loc_alt_names']:
  alt_names = alt_names + "\n" + name
alternate_names.set(alt_names)

dr.get(unknown_locations[0]['db_loc']['map_url'])

app = App(root)

root.mainloop()
