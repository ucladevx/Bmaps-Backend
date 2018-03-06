from Tkinter import *
import tkMessageBox
import tkSimpleDialog

import time
from selenium import webdriver

import pymongo
import os
from dotenv import load_dotenv

import re
import copy

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
  # Initialize unknown_locations to all locations
  # Only look at locations starting with a certain letter 
  # to make sure everyone's working on something different
  unknown_locations = []
  counter = 0
  lastAction = "none"
  lastLocation = {}

  def __init__(self, master):
    self.allLocations()

    empty1 = Label(root, text="", font=("Open Sans", 10))
    empty1.pack()

    frame = Frame(master)
    # Key Bindings
    frame.bind('<Left>', self.left)
    frame.bind('<Right>', self.right)
    frame.focus_set()
    # Pack aka display
    frame.pack()

    # Single display with the following buttons:

    # Correct - location data matches location name
    # Will be removed from `unknown` database and added to `known` database
    self.correct = Button(frame, text="CORRECT!", command=self.isCorrect)
    self.correct.pack(side=LEFT)

    # Wrong - location data does not match location name (e.g. the coordinates aren't right)
    # Prompts user to input correct coordinates and an additional name (1 max)
    # Keeps modified location in `unknown` database for secondary verification
    self.wrong = Button(frame, text="WRONG Location Data!", command=self.isWrong)
    self.wrong.pack(side=LEFT)

    # Fail - location name doesn't seem to match with the location data the locations api found
    # Add to a separate `TODO` database for manual processing
    self.fail = Button(frame, text="Wrong location found!", command=self.isFail)
    self.fail.pack(side=LEFT)

    # Skip - don't know if right or not, or not sure
    # Just moves on to next location without modifying any databases
    self.skip = Button(frame, text="SKIP (idk)", command=self.skip)
    self.skip.pack(side=LEFT)

    # Undo - only undoes last CORRECT/WRONG action
    self.undo = Button(frame, text="UNDO last CORRECT/WRONG/FAIL", command=self.undo)
    self.undo.pack(side=LEFT)
    self.undo.config(state = DISABLED)

    # Filter Letter - if multiple people are working on this at same time
    # Filter by letter so everyone is wokring on something different
    self.filter = Button(frame, text="FILTER", command=self.filterLetter)
    self.filter.pack(side=LEFT)

    # Help - displays instructions
    self.help = Button(frame, text="HELP", command=self.helpInstructions)
    self.help.pack(side=LEFT)

    # Quit - exit tkinter/displays
    # TODO: remove extra check to quit, let there in case we wanted to use similar code in future
    self.button = Button(frame, text="QUIT", command= lambda: self.quit(frame))
    self.button.pack(side=LEFT)

    # Define all the labels and strings used in the display
    empty2 = Label(root, text="", font=("Open Sans", 10))
    empty2.pack()

    question = Label(root, text="Is this location in the correct place?", font=("Open Sans", 20))
    question.pack()

    Label(root, textvariable=counterLabel, font=("Open Sans", 16)).pack()

    Label(root, textvariable=locationLabel, font=("Open Sans Bold", 14), wraplength=450, justify=CENTER).pack()

    Label(root, textvariable=latitudeLabel, font=("Open Sans", 12)).pack()

    Label(root, textvariable=longitudeLabel, font=("Open Sans", 12)).pack()

    Label(root, textvariable=alternate_namesLabel, font=("Open Sans", 12)).pack()

    empty3 = Label(root, text="", font=("Open Sans", 10))
    empty3.pack()

    # Set all the labels for the display to the first event
    if self.unknown_locations:
      self.updateLabels()
    else:
      # No more locations to process, disable everything but HELP/QUIT
      self.disableLabels()

  def left(self, event):
    print "Left key pressed"
    # self.isCorrect()

  def right(self, event):
    print "Right key pressed"
    # self.isWrong()

  def isCorrect(self):
    print "Coordinates are correct!                                             " + self.unknown_locations[0]['unknown_loc']['loc_name']
    print "Adding to different database and remove from test database"

    self.undo.config(state = "normal")
    self.lastAction = "CORRECT"
    self.lastLocation = copy.deepcopy(self.unknown_locations[0])

    # Insert to one database and remove from original
    tkinter_known_collection.insert_one(self.unknown_locations[0])
    tkinter_unknown_collection.delete_one({'_id': self.unknown_locations[0]['_id']})

    # Move on to next location, update all displays
    self.changeText()

  def isWrong(self):
    print "Coordinates are wrong, enter correct location data:                  " + self.unknown_locations[0]['unknown_loc']['loc_name']
    print "Leaving location in database for secondary verification"

    self.undo.config(state = "normal")
    self.lastAction = "WRONG"
    self.lastLocation = copy.deepcopy(self.unknown_locations[0])

    # Prompt user to correct the coordinates
    # User can `cancel` or fill out prompts
    latitude = tkSimpleDialog.askfloat("Latitude", "Enter latitude value:", initialvalue=self.unknown_locations[0]['db_loc']['loc_latitude'], minvalue=34.05, maxvalue=34.08)
    longitude = tkSimpleDialog.askfloat("Longitude", "Enter longitude value:",initialvalue=self.unknown_locations[0]['db_loc']['loc_longitude'], minvalue=-118.46, maxvalue=-118.43)
    name = tkSimpleDialog.askstring("Alternate Name", "Enter alternate name or click cancel:")

    # If any changes were made then update original location object
    updated = False
    if latitude and latitude != self.unknown_locations[0]['db_loc']['loc_latitude']:
      print "New latitude: " + str(latitude)
      self.unknown_locations[0]['db_loc']['loc_latitude'] = latitude
      updated = True
    if longitude and longitude != self.unknown_locations[0]['db_loc']['loc_longitude']:
      print "New longitude: " + str(longitude)
      self.unknown_locations[0]['db_loc']['loc_longitude'] = longitude
      updated = True
    if name and name.lower() not in (alt.lower() for alt in self.unknown_locations[0]['db_loc']['loc_alt_names']):
      print "New name: " + name
      self.unknown_locations[0]['db_loc']['loc_alt_names'].append(name)
      updated = True

    # If updated, update location in database
    if updated:
      print "Updating location in database..."
      tkinter_unknown_collection.replace_one({'_id': self.unknown_locations[0]['_id']}, self.unknown_locations[0]) 
    else:
      print "Nothing changed, event is left unmodified..."

    # Move on to next location, update all displays
    self.changeText()

  def isFail(self):
    print "Locations API matched wrong location:                                " + self.unknown_locations[0]['unknown_loc']['loc_name']
    print "Moving to different database for manual correction."

    self.undo.config(state = "normal")
    self.lastAction = "FAIL"
    self.lastLocation = copy.deepcopy(self.unknown_locations[0])

    # Insert to one database and remove from original
    tkinter_TODO_collection.insert_one(self.unknown_locations[0])
    tkinter_unknown_collection.delete_one({'_id': self.unknown_locations[0]['_id']})

    # Move on to next location, update all displays
    self.changeText()

  def undo(self):
    print "Undoing last correct/wrong/fail!"

    self.enableLabels()

    if self.lastAction == "CORRECT":
      print "Undoing last CORRECT action..."
      tkinter_unknown_collection.insert_one(self.lastLocation)
      tkinter_known_collection.delete_one({'_id': self.lastLocation['_id']})

      # Add to beginning of events list
      self.unknown_locations.insert(0, self.lastLocation)
      self.counter += 1

      # Update labels
      self.updateLabels()

    elif self.lastAction == "WRONG":
      print "Undoing last WRONG action..."
      tkinter_unknown_collection.replace_one({'_id': self.lastLocation['_id']}, self.lastLocation) 

      # Add to beginning of events list
      self.unknown_locations.insert(0, self.lastLocation)
      self.counter += 1

      # Update labels
      self.updateLabels()

    elif self.lastAction == "FAIL":
      print "Undoing last FAIL action..."
      tkinter_unknown_collection.insert_one(self.lastLocation)
      tkinter_TODO_collection.delete_one({'_id': self.lastLocation['_id']})

      # Add to beginning of events list
      self.unknown_locations.insert(0, self.lastLocation)
      self.counter += 1

      # Update labels
      self.updateLabels()

    else:
      # Not undoing last action as it wasn't a YES/NO
      print "Nothing to undo!"

    self.lastAction = "none"
    self.lastLocation = {}
    self.undo.config(state = DISABLED)

  def skip(self):
    print "Skipping this location, idk what to do with it...                       " + self.unknown_locations[0]['unknown_loc']['loc_name']

    self.lastAction = "none"
    self.lastEvent = {}
    self.undo.config(state = DISABLED)

    # Move on to next event, update display
    self.changeText()

  def changeText(self):
    # Remove location we just processed from list
    self.unknown_locations.pop(0)

    # Decrement number of locations remaining to process
    self.counter -= 1
    counterLabel.set("Locations Remaining: " + str(self.counter))

    # Check that there are still locations left to process and update displays/labels
    if self.unknown_locations:
      self.updateLabels()
    else:
      self.disableLabels()

  def filterLetter(self):
    print "Filter what locations we're looking at by letter..."
    print "Do this if multiple people are doing this at the same time"

    self.lastAction = "none"
    self.lastLocation = {}
    self.enableLabels()
    self.undo.config(state = DISABLED)

    # Ask user for input to filter what locations you're looking at
    # Only look at locations starting with a certain letter 
    # to make sure everyone's working on something different
    letter_num = tkSimpleDialog.askinteger("Letter Number", "Ints (1-26) correspond to letters (a-z)\nEnter 0 to look at all locations", minvalue=0, maxvalue=26)

    if letter_num:
      FILTER_LETTER = chr(ord('a') + letter_num - 1)
      print "Looking at locations starting with letter " + FILTER_LETTER

      # Get all the locations that start with the letter
      filter_regex = re.compile('^' + FILTER_LETTER + '.*', re.IGNORECASE)
      locations_cursor = tkinter_unknown_collection.find({'unknown_loc.loc_name': filter_regex})
      
      # Append each location doc to a list to process (this is why we try to prevent overlap)
      # Empty list beforehand
      self.unknown_locations = []
      if locations_cursor.count() > 0:
        for loc in locations_cursor:
          self.unknown_locations.append(loc)
        self.updateLabels()
      else:
          print 'Cannot find any locations in database starting with letter ' + FILTER_LETTER
          self.disableLabels()
    else:
      print "No letter chosen for filtering, leaving unfiltered"

    if letter_num != None:
      if letter_num == 0:
        self.unknown_locations = []
        self.counter = 0
        self.allLocations()
        
        if self.counter > 0:
          self.updateLabels()
        else:
          print 'Cannot find any locations in database!'
          quit()
      else:
        FILTER_LETTER = chr(ord('a') + letter_num - 1)
        print "Looking at locations starting with letter " + FILTER_LETTER

        # Get all the locations that start with the letter
        filter_regex = re.compile('^' + FILTER_LETTER + '.*', re.IGNORECASE)
        locations_cursor = tkinter_unknown_collection.find({'unknown_loc.loc_name': filter_regex})

        # Append each location doc to a list to process (this is why we try to prevent overlap)
        # Empty list beforehand
        self.unknown_locations = []
        self.counter = 0
        if locations_cursor.count() > 0:
          for loc in locations_cursor:
            self.unknown_locations.append(loc)
            self.counter += 1
          if self.counter > 0:
            self.updateLabels()
          else:
            print 'Cannot find any locations in database starting with letter ' + FILTER_LETTER
            self.disableLabels()
        else:
          print 'Cannot find any locations in database starting with letter ' + FILTER_LETTER
          self.disableLabels()
    else:
      print "No letter chosen for filtering, leaving unfiltered"

  def helpInstructions(self):
    print "Displaying instructions!"

    # Display message dialog with instructions explaining the buttons and our website
    tkMessageBox.showinfo(
      "Instructions",
      "Hello! Thanks for your help checking whether or not our locations are right. Check us out at www.whatsmappening.io!\n\nHere's what the buttons do:\n\nCORRECT: The information displayed and the pin on the map all seem to be right, approve the location!\n\nWRONG: Something seems to be wrong... the location name matches the location data, but perhaps the coordinates are off. Please fix the coordinates for us!\n\nWrong location found: The location name doesn't seem to match the location data displayed... we'll take care of this one from here!\n\nSKIP: Confused or don't know what to do with a particular location? Just skip it!\n\nUNDO: Undo last CORRECT/WRONG/FAIL action.\n\nFILTER: If multiple people are working on this at the same time, filter by letter so everyone is working on something different! By default/when first run, it has all locations there.\n\nHELP: As you can tell, this one leads to the instructions!\n\nQUIT: Exit from the displays and be on your merry way! Thanks for your help!"
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

  # Populates unknown_locations with all locations left to process
  def allLocations(self):
    locations_cursor = tkinter_unknown_collection.find({}) #, {'_id': False})
    if locations_cursor.count() > 0:
      for loc in locations_cursor:
        self.unknown_locations.append(loc)
        self.counter += 1
    else:
        print 'Cannot find any locations in database!'
        quit()

  def disableLabels(self):
    # No more locations to process, disable everything but HELP/QUIT
    counterLabel.set("Locations Remaining: " + str(self.counter))
    locationLabel.set("No more locations to check!")
    latitudeLabel.set("Thanks for all your help!")
    longitudeLabel.set("")
    alternate_namesLabel.set("~ Mappening Team ~")

    self.correct.config(state = DISABLED)
    self.wrong.config(state = DISABLED)
    self.fail.config(state = DISABLED)
    self.skip.config(state = DISABLED)

  def enableLabels(self):
    # Enable buttons
    self.correct.config(state = "normal")
    self.wrong.config(state = "normal")
    self.fail.config(state = "normal")
    self.skip.config(state = "normal")

  # Updates all labels
  def updateLabels(self):
    counterLabel.set("Locations Remaining: " + str(self.counter))
    locationLabel.set("LOCATION NAME: " + self.unknown_locations[0]['unknown_loc']['loc_name'])
    latitudeLabel.set("LATITUDE: " + str(self.unknown_locations[0]['db_loc']['loc_latitude']))
    longitudeLabel.set("LONGITUDE: " + str(self.unknown_locations[0]['db_loc']['loc_longitude']))

    # Jank way to make columns
    alt_names = "ALTERNATIVE NAMES:\n=================="
    col = True
    for name in self.unknown_locations[0]['db_loc']['loc_alt_names']:
      if col:
        alt_names = alt_names + "\n" + name
        col = False
      else:
        alt_names = alt_names + "\t\t\t" + name
        col = True

    if len(self.unknown_locations[0]['db_loc']['loc_alt_names']) % 2 == 1:
      alt_names = alt_names + "\t\t\t\t\t\t"

    alternate_namesLabel.set(alt_names)

    dr.get(self.unknown_locations[0]['db_loc']['map_url'])

# Stark tkinter and set geometry/position of display
root = Tk()
# root.geometry("+%d+%d" % (300, 0))
root.geometry("+300+0")

locationLabel = StringVar()
latitudeLabel = StringVar()
longitudeLabel = StringVar()
alternate_namesLabel = StringVar()
counterLabel = StringVar()

# Initializes App so tkinter/butttons are working
app = App(root)

# Pretty sure tkinter just loops back to the `root = Tk()` or something
root.mainloop()
