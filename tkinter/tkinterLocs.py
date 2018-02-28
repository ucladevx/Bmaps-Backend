from Tkinter import *
import tkMessageBox
import tkSimpleDialog

import time
from selenium import webdriver

import pymongo
import os
from dotenv import load_dotenv

import re

# Get environment vars for keeping sensitive info secure
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

# Only look at locations starting with a certain letter 
# to make sure everyone's working on something different
# Too lazy to make this work better so just change this manually and rerun when letter is out
########################### CHANGE THE LETTER #################################
FILTER_LETTER = 'g'
filter_regex = re.compile('^' + FILTER_LETTER + '.*', re.IGNORECASE)
locations_cursor = tkinter_unknown_collection.find({'unknown_loc.loc_name': filter_regex})
########################### CHANGE THE LETTER #################################

# locations_cursor = tkinter_unknown_collection.find({}) #, {'_id': False})

# Append each location doc to a list to process (this is why we try to prevent overlap)
if locations_cursor.count() > 0:
  for loc in locations_cursor:
    unknown_locations.append(loc)
else:
    print 'Cannot find any locations in database!'
    quit()

# Start driver aka chrome browser for displaying map pins/coordinates
# Could also use geckodriver with Firefox but go Google
dr = webdriver.Chrome()

# Get initial window size
width = dr.get_window_size()['width']
height = dr.get_window_size()['height']

# Set window size (hardcoded)
# TODO: don't hardcode but calculate using size of window or something
dr.set_window_size(width, height - 200)

# Get window position
x = dr.get_window_position()['x']
y = dr.get_window_position()['y']

# Set window position (hardcoded)
dr.set_window_position(x, y + 225);

# Random start site
# Issues when I tried to use google/google maps, got "unknown error: $ is not defined"
dr.get("https://stackoverflow.com/")

class App:

  def __init__(self, master):
    frame = Frame(master)
    frame.pack()

    # Single display with the following buttons:

    # Correct - location data matches location name
    # Will be removed from `unknown` database and added to `known` database
    self.correct = Button(frame, text="CORRECT location data!", command=self.isCorrect)
    self.correct.pack(side=LEFT)

    # Wrong - location data does not match location name (e.g. the coordinates aren't right)
    # Prompts user to input correct coordinates and an additional name (1 max)
    # Keeps modified location in `unknown` database for secondary verification
    self.wrong = Button(frame, text="Location data is WRONG!", command=self.isWrong)
    self.wrong.pack(side=LEFT)

    # Fail - location name doesn't seem to match with the location data the locations api found
    # Add to a separate `TODO` database for manual processing
    self.fail = Button(frame, text="Wrong location found!", command=self.isFail)
    self.fail.pack(side=LEFT)

    # Skip - don't know if right or not, or not sure
    # Just moves on to next location without modifying any databases
    self.skip = Button(frame, text="SKIP location", command=self.changeText)
    self.skip.pack(side=LEFT)

    # Help - displays instructions
    self.help = Button(frame, text="HELP", command=self.helpInstructions)
    self.help.pack(side=LEFT)

    # Quit - exit tkinter/displays
    # TODO: remove extra check to quit, let there in case we wanted to use similar code in future
    self.button = Button(frame, text="QUIT", command= lambda: self.quit(frame))
    self.button.pack(side=LEFT)

  def isCorrect(self):
    print "Coordinates are correct!"
    print "Add to different database and remove from test database: " + unknown_locations[0]['unknown_loc']['loc_name']

    # Insert to one database and remove from original
    tkinter_known_collection.insert_one(unknown_locations[0])
    tkinter_unknown_collection.delete_one({'_id': unknown_locations[0]['_id']})

    # Move on to next location, update all displays
    self.changeText()

  def isWrong(self):
    print "Coordinates are wrong, enter correct location data and update database"
    print "Leaving location in database for secondary verification: " + unknown_locations[0]['unknown_loc']['loc_name']

    # Prompt user to correct the coordinates
    # User can `cancel` or fill out prompts
    latitude = tkSimpleDialog.askfloat("Latitude", "Enter latitude value:", initialvalue=unknown_locations[0]['db_loc']['loc_latitude'], minvalue=34.05, maxvalue=34.08)
    longitude = tkSimpleDialog.askfloat("Longitude", "Enter longitude value:",initialvalue=unknown_locations[0]['db_loc']['loc_longitude'], minvalue=-118.46, maxvalue=-118.43)
    name = tkSimpleDialog.askstring("Alternate Name", "Enter alternate name or click cancel:")

    # If any changes were made then update original location object
    updated = False
    if latitude and latitude != unknown_locations[0]['db_loc']['loc_latitude']:
      print "New latitude: " + str(latitude)
      unknown_locations[0]['db_loc']['loc_latitude'] = latitude
      updated = True
    if longitude and longitude != unknown_locations[0]['db_loc']['loc_longitude']:
      print "New longitude: " + str(longitude)
      unknown_locations[0]['db_loc']['loc_longitude'] = longitude
      updated = True
    if name and name.lower() not in (alt.lower() for alt in unknown_locations[0]['db_loc']['loc_alt_names']):
      print "New name: " + name
      unknown_locations[0]['db_loc']['loc_alt_names'].append(name)
      updated = True

      # If updated, update location in database
    if updated:
      print "Updating location in database..."
      tkinter_unknown_collection.replace_one({'_id': unknown_locations[0]['_id']}, unknown_locations[0]) 
    else:
      print "Nothing changed, event is left unmodified..."

    # Move on to next location, update all displays
    self.changeText()

  def isFail(self):
    print "Not even the right location found... add to different database for manual correction"
    print "Removing from test database: " + unknown_locations[0]['unknown_loc']['loc_name']

    # Insert to one database and remove from original
    tkinter_TODO_collection.insert_one(unknown_locations[0])
    tkinter_unknown_collection.delete_one({'_id': unknown_locations[0]['_id']})

    # Move on to next location, update all displays
    self.changeText()

  def helpInstructions(self):
    print "Displaying instructions!"

    # Display message dialog with instructions explaining the buttons and our website
    tkMessageBox.showinfo(
      "Instructions",
      "Hello! Thanks for your help checking whether or not our locations are right. Check us out at www.whatsmappening.io!\n\nHere's what the buttons do:\n\nCORRECT: The information displayed and the pin on the map all seem to be right, approve the location!\n\nWRONG: Something seems to be wrong... the location name matches the location data, but perhaps the coordinates are off. Please fix the coordinates for us!\n\nWrong location found: The location name doesn't seem to match the location data displayed... we'll take care of this one from here!\n\nSKIP: Confused or don't know what to do with a particular location? Just skip it!\n\nHELP: As you can tell, this one leads to the instructions!\n\nQUIT: Exit from the displays and be on your merry way! Thanks for your help!"
    )

  def quit(self, frame):
    # Prompts a yes/no responce
    choice = tkMessageBox.askquestion("Ready to quit?", "Thanks for your help!", icon='warning')
    # If quitting, kill the chrome driver and the tkinter frame/display
    if choice == 'yes':
      dr.quit()
      frame.quit()
    else:
      print "Not done yet!"

  def changeText(self):
    # Remove location we just processed from list
    unknown_locations.pop(0)

    # Check that there are still locations left to process and update displays/labels
    if unknown_locations:
      location.set("LOCATION NAME: " + unknown_locations[0]['unknown_loc']['loc_name'])
      latitude_str.set("LATITUDE: " + str(unknown_locations[0]['db_loc']['loc_latitude']))
      longitude_str.set("LONGITUDE: " + str(unknown_locations[0]['db_loc']['loc_longitude']))

      alt_names = "ALTERNATIVE NAMES:\n=================="
      for name in unknown_locations[0]['db_loc']['loc_alt_names']:
        alt_names = alt_names + "\n" + name
      alternate_names.set(alt_names)

      # Open Maps display to current coordinates
      dr.get(unknown_locations[0]['db_loc']['map_url'])
    else:
      # No more locations to process, disable everything but HELP/QUIT
      location.set("No more locations to check!")
      latitude_str.set("Thanks for all your help!")
      longitude_str.set("")
      alternate_names.set("~ Mappening Team ~")

      self.correct.config(state = DISABLED)
      self.wrong.config(state = DISABLED)
      self.fail.config(state = DISABLED)
      self.skip.config(state = DISABLED)

# Stark tkinter and set geometry/position of display
root = Tk()
root.geometry("+%d+%d" % (300, 0))

# Define all the labels and strings used in the display
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

# Set all the labels for the display to the first event
location.set("LOCATION NAME: " + unknown_locations[0]['unknown_loc']['loc_name'])
latitude_str.set("LATITUDE: " + str(unknown_locations[0]['db_loc']['loc_latitude']))
longitude_str.set("LONGITUDE: " + str(unknown_locations[0]['db_loc']['loc_longitude']))

alt_names = "ALTERNATIVE NAMES:\n=================="
for name in unknown_locations[0]['db_loc']['loc_alt_names']:
  alt_names = alt_names + "\n" + name
alternate_names.set(alt_names)

dr.get(unknown_locations[0]['db_loc']['map_url'])

# Initializes App so tkinter/butttons are working
app = App(root)

# Pretty sure tkinter just loops back to the `root = Tk()` or something
root.mainloop()
