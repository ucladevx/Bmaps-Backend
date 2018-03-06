from Tkinter import *
import tkMessageBox
import tkSimpleDialog

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
unknown_locs_collection = db.tkinter_UCLA_locations
TODO_locs_collection = db.tkinter_UCLATODO_locations

class App:
  # Initialize unknown_locations to all locations
  # Only look at locations starting with a certain letter 
  # to make sure everyone's working on something different
  unknown_locations = []
  counter = 0
  lastAction = "none"
  lastLocation = {}

  def __init__(self, master):
    locations_cursor = unknown_locs_collection.find({}) #, {'_id': False})
    if locations_cursor.count() > 0:
      for loc in locations_cursor:
        # Locations we already processed and approved have `isUCLA = True`
        # Look for locations that haven't been processed and add to list
        if 'isUCLA' not in loc or not loc['isUCLA']:
          self.unknown_locations.append({ 'location': loc['location_name'], 'event': loc['event_name'] })
          self.counter += 1
    else:
        print 'Cannot find any locations in database!'
        quit()

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

    # Correct - location name belongs to a location within UCLA/Westwood
    # Tag location with `isUCLA = True` and keep in database
    self.correct = Button(frame, text="YES!", command=self.isCorrect)
    self.correct.pack(side=LEFT)

    # Wrong - location name does not belong to a location within UCLA/Westwood
    # Remove location from database, we don't need to worry about it
    self.wrong = Button(frame, text="NO!", command=self.isWrong)
    self.wrong.pack(side=LEFT)

    # Skip - don't know if in UCLA or not, or not sure
    # Just moves on to next location without modifying any databases
    self.skip = Button(frame, text="SKIP (idk)", command=self.skip)
    self.skip.pack(side=LEFT)

    # Undo - only undoes last YES/NO action
    self.undo = Button(frame, text="UNDO last YES/NO", command=self.undo)
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

    question = Label(root, text="         Is this event location in UCLA/Westwood?          ", font=("Open Sans", 20))
    question.pack()

    Label(root, textvariable=counterLabel, font=("Open Sans", 16)).pack()
    counterLabel.set("Locations Remaining: " + str(self.counter))

    Label(root, textvariable=locationLabel, font=("Open Sans Bold", 14), wraplength=450, justify=CENTER).pack()

    Label(root, textvariable=eventLabel, font=("Open Sans", 12), wraplength=450, justify=CENTER).pack()

    empty3 = Label(root, text="", font=("Open Sans", 10))
    empty3.pack()

    # Set all the labels for the display to the first event
    if self.unknown_locations:
      locationLabel.set(self.unknown_locations[0]['location'])
      eventLabel.set(self.unknown_locations[0]['event'])
    else:
      # No more locations to process, disable everything but HELP/QUIT
      locationLabel.set("No more locations to check")
      eventLabel.set("Thanks for your help!")
      self.correct.config(state = DISABLED)
      self.wrong.config(state = DISABLED)
      self.skip.config(state = DISABLED)

  def left(self, event):
    # print "Left key pressed"
    self.isCorrect()

  def right(self, event):
    # print "Right key pressed"
    self.isWrong()

  def isCorrect(self):
    print "Location in UCLA, marking as checked:                                " + self.unknown_locations[0]['location']

    self.undo.config(state = "normal")

    # Find location with matching name and tag it as correct
    location = unknown_locs_collection.find_one({'location_name': self.unknown_locations[0]['location']})
    if location:
      self.lastAction = "YES ucla"
      self.lastLocation = location

      location['isUCLA'] = True

      # Replace updated location in database
      unknown_locs_collection.replace_one({'_id': location['_id']}, location.copy()) 

    else:
      print "No such location found in db to replace, moving on...                " + self.unknown_locations[0]['location']

      self.lastAction = "YES none"
      self.lastLocation = self.unknown_locations[0]

    # Move on to next location, update display
    self.changeText()

  def isWrong(self):
    print "Location not in UCLA or an outlier, remove from database:            " + self.unknown_locations[0]['location']
    
    self.lastAction = "NO"
    self.lastLocation = self.unknown_locations[0]
    self.undo.config(state = "normal")

    # Delete location we don't care about from database
    unknown_locs_collection.delete_one({'location_name': self.unknown_locations[0]['location']})

    # Move on to next location, update display
    self.changeText()

  def undo(self):
    print "Undoing last yes/no!"

    self.enable()

    if self.lastAction == "NO":
      print "Reinserting location we just deleted..."
      # Reinsert location we just deleted
      unknown_locs_collection.insert_one({'location_name': self.lastLocation['location'], 'event_name': self.lastLocation['event']})

      # Add to beginning of locations list
      self.unknown_locations.insert(0, self.lastLocation)
      self.counter += 1

      # Update labels
      locationLabel.set(self.unknown_locations[0]['location'])
      eventLabel.set(self.unknown_locations[0]['event'])
      counterLabel.set("Locations Remaining: " + str(self.counter))
    elif self.lastAction == "YES none":
      print "Adding previous event back to the list of locations..."
      # Only skipped/moved past event
      # Add to beginning of locations list
      self.unknown_locations.insert(0, self.lastLocation)
      self.counter += 1

      # Update labels
      locationLabel.set(self.unknown_locations[0]['location'])
      eventLabel.set(self.unknown_locations[0]['event'])
      counterLabel.set("Locations Remaining: " + str(self.counter))
    elif self.lastAction == "YES ucla":
      print "Removing UCLA tag from previous event..."
      # Marked as ucla location
      # Find location with matching name and remove ucla tag
      location = unknown_locs_collection.find_one({'location_name': self.lastLocation['location_name']})
      if location:
        location.pop('isUCLA', None)

        # Replace updated location in database
        unknown_locs_collection.replace_one({'_id': location['_id']}, location.copy()) 

      # Add to beginning of locations list
      loc = { 'location': self.lastLocation['location_name'], 'event': self.lastLocation['event_name'] }
      self.unknown_locations.insert(0, loc)
      self.counter += 1

      # Update labels
      locationLabel.set(self.unknown_locations[0]['location'])
      eventLabel.set(self.unknown_locations[0]['event'])
      counterLabel.set("Locations Remaining: " + str(self.counter))
    else:
      # Not undoing last action as it wasn't a YES/NO
      print "Nothing to undo!"


    self.lastAction = "none"
    self.lastLocation = {}
    self.undo.config(state = DISABLED)

  def skip(self):
    print "Skipping this location, idk what to do with it...                    " + self.unknown_locations[0]['location']

    self.lastAction = "none"
    self.lastLocation = {}
    self.undo.config(state = DISABLED)

    # Find location with matching name and keep a count of how many times it has been skipped
    location = unknown_locs_collection.find_one({'location_name': self.unknown_locations[0]['location']})
    if location:
      if 'skip_count' in location:
        location['skip_count'] = location['skip_count'] + 1
        # If number of times it has been skipped is > 3 move to todo_locs db
        if location['skip_count'] > 3:
          print "Location has been skipped too often... moving to TODO db:            " + self.unknown_locations[0]['location']
          # Insert to one database and remove from original
          loc = unknown_locs_collection.find_one({'location_name': self.unknown_locations[0]['location']}, {'_id': False, 'skip_count': False, 'isUCLA': False})
          if loc:
            TODO_locs_collection.insert_one(loc)
            unknown_locs_collection.delete_one({'location_name': self.unknown_locations[0]['location']})
      else:
        location['skip_count'] = 1

      # Replace updated location in database
      unknown_locs_collection.replace_one({'_id': location['_id']}, location.copy()) 

    # Move on to next location, update display
    self.changeText()

  def helpInstructions(self):
    print "Displaying instructions!"

    # Display message dialog with instructions explaining the buttons and our website
    tkMessageBox.showinfo(
      "Instructions",
      "Hello! Thanks for your help checking whether or not these locations we scraped are even in UCLA/Westwood. Check us out at www.whatsmappening.io!\n\nHere's what the buttons do:\nCORRECT: The location name is in UCLA, approve the location! Also triggered with the LEFT arrow key.\n\nWRONG: The location isn't in UCLA/Westwood, reject it! Also triggered with the RIGHT arrow key.\n\nSKIP: Confused or don't know what to do with a particular location? Just skip it!\n\nFILTER: If multiple people are working on this at the same time, filter by letter so everyone is working on something different! By default/when first run, it has all locations there.\n\nHELP: As you can tell, this one leads to the instructions!\n\nQUIT: Exit from the display and be on your merry way! Thanks for your help!"
    )

  def quit(self, frame):
    print "Quitting tkinter thing..."

    # Prompt a yes/no response
    choice = tkMessageBox.askquestion("Ready to quit?", "Thanks for your help!", icon='warning')
    # If quitting, kill the chrome driver and the tkinter frame/display
    if choice == 'yes':
      frame.quit()
    else:
      print "Not done yet!"

  def changeText(self):

    # Remove location we just processed from list
    self.unknown_locations.pop(0)

    # Decrement number of events remaining to process
    self.counter -= 1
    counterLabel.set("Locations Remaining: " + str(self.counter))

    # Check that there are still locations left to process and update name label
    if self.unknown_locations:
      locationLabel.set(self.unknown_locations[0]['location'])
      eventLabel.set(self.unknown_locations[0]['event'])
    else:
      # No more locations to process, disable everything but HELP/QUIT
      self.disable()

  def filterLetter(self):
    self.lastAction = "none"
    self.lastLocation = {}

    print "Filter what locations we're looking at by letter..."
    print "Do this if multiple people are doing this at the same time"

    self.enable()
    self.undo.config(state = DISABLED)

    # Ask user for input to filter what locations you're looking at
    # Only look at locations starting with a certain letter 
    # to make sure everyone's working on something different
    letter_num = tkSimpleDialog.askinteger("Letter Number", "Ints (1-26) correspond to letters (a-z)\nEnter 0 to look at all locations", minvalue=0, maxvalue=26)

    if letter_num != None:
      if letter_num == 0:
        locations_cursor = unknown_locs_collection.find({})
        self.unknown_locations = []
        self.counter = 0
        if locations_cursor.count() > 0:
          for loc in locations_cursor:
            # Locations we already processed and approved have `isUCLA = True`
            # Look for locations that haven't been processed and add to list
            if 'isUCLA' not in loc or not loc['isUCLA']:
              self.unknown_locations.append({ 'location': loc['location_name'], 'event': loc['event_name'] })
              self.counter += 1
          if self.counter > 0:
            locationLabel.set(self.unknown_locations[0]['location'])
            eventLabel.set(self.unknown_locations[0]['event'])
            counterLabel.set("Locations Remaining: " + str(self.counter))
          else:
            print 'Cannot find any locations in database!'
            quit()
        else:
          print 'Cannot find any locations in database!'
          quit()
      else:
        FILTER_LETTER = chr(ord('a') + letter_num - 1)
        print "Looking at locations starting with letter " + FILTER_LETTER

        # Get all the locations that start with the letter
        filter_regex = re.compile('^' + FILTER_LETTER + '.*', re.IGNORECASE)
        locations_cursor = unknown_locs_collection.find({'location_name': filter_regex})
        
        # Append each location doc to a list to process (this is why we try to prevent overlap)
        # Empty list beforehand
        self.unknown_locations = []
        self.counter = 0
        if locations_cursor.count() > 0:
          for loc in locations_cursor:
            # Locations we already processed and approved have `isUCLA = True`
            # Look for locations that haven't been processed and add to list
            if 'isUCLA' not in loc or not loc['isUCLA']:
              self.unknown_locations.append({ 'location': loc['location_name'], 'event': loc['event_name'] })
              self.counter += 1
          if self.counter > 0:
            locationLabel.set(self.unknown_locations[0]['location'])
            eventLabel.set(self.unknown_locations[0]['event'])
            counterLabel.set("Locations Remaining: " + str(self.counter))
          else:
            print 'Cannot find any locations in database starting with letter ' + FILTER_LETTER
            counterLabel.set("Locations Remaining: " + str(self.counter))
            self.disable()
        else:
          print 'Cannot find any locations in database starting with letter ' + FILTER_LETTER
          counterLabel.set("Locations Remaining: " + str(self.counter))
          self.disable()
    else:
      print "No letter chosen for filtering, leaving unfiltered"

  def disable(self):
    # No more locations to process, disable everything but HELP/QUIT
    locationLabel.set("No more locations to check")
    eventLabel.set("Thanks for your help!")
    self.correct.config(state = DISABLED)
    self.wrong.config(state = DISABLED)
    self.skip.config(state = DISABLED)
    self.undo.config(state = DISABLED)

  def enable(self):
    # Enable buttons
    self.correct.config(state = "normal")
    self.wrong.config(state = "normal")
    self.skip.config(state = "normal")
    self.undo.config(state = "normal")

# Stark tkinter and set geometry/position of display
root = Tk()
# root.geometry('250x150+0+0')
# root.geometry("+%d+%d" % (450, 200))
root.geometry("+450+200")

# Global labels/strings
counterLabel = StringVar()
locationLabel = StringVar()
eventLabel = StringVar()

# Initializes App so tkinter/butttons are working
app = App(root)

# Pretty sure tkinter just loops back to the `root = Tk()` or something
root.mainloop()
