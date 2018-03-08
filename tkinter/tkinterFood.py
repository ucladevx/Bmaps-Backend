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
ml_collection = db.events_ml

class App:
  # Initialize events to all events
  # Only look at events starting with a certain letter 
  # to make sure everyone's working on something different
  events = []
  counter = 0
  lastAction = "none"
  lastEvent = {}

  def __init__(self, master):
    events_cursor = ml_collection.find({}) #, {'_id': False})
    if events_cursor.count() > 0:
      for event in events_cursor:
        # Events we already processed and approved have 'free_food' field
        # Look for events that haven't been processed and add to list
        if 'free_food' not in event:
          self.events.append({ 'name': event.get('name', "NO EVENT NAME"), 'description': event.get('description', "NO EVENT DESCRIPTION"), 'id': event['_id'] })
          self.counter += 1
    else:
        print 'Cannot find any events in database!'
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

    # Correct - event has free food
    # Tag event with `free_food = true` and keep in database
    self.correct = Button(frame, text="YES!", command=self.isCorrect)
    self.correct.pack(side=LEFT)

    # Wrong - event does not have free food
    # Tag event with `free_food = false` and keep in database
    self.wrong = Button(frame, text="NO!", command=self.isWrong)
    self.wrong.pack(side=LEFT)

    # Skip - don't know if it has free food or not
    # Just moves on to next event without modifying any databases
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

    question = Label(root, text="Does this event have free food?", font=("Open Sans", 20))
    question.pack()

    Label(root, textvariable=counterLabel, font=("Open Sans", 16)).pack()
    counterLabel.set("Events Remaining: " + str(self.counter))

    Label(root, textvariable=eventLabel, font=("Open Sans Bold", 14), wraplength=450, justify=CENTER).pack()

    Label(root, textvariable=descriptionLabel, font=("Open Sans", 12), wraplength=450, justify=CENTER).pack()

    empty3 = Label(root, text="", font=("Open Sans", 10))
    empty3.pack()

    # Set all the labels for the display to the first event
    if self.events:
      eventLabel.set(self.events[0]['name'])
      descriptionLabel.set(self.events[0]['description'])
    else:
      # No more events to process, disable everything but HELP/QUIT
      eventLabel.set("No more events to check")
      descriptionLabel.set("Thanks for your help!")
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
    print "Event has free food!                                                 " + self.events[0]['name']
    self.undo.config(state = "normal")

    # Find event with matching id and tag it as free food
    event = ml_collection.find_one({'_id': self.events[0]['id']})
    if event:
      self.lastAction = "free food"
      self.lastEvent = event

      event['free_food'] = True

      # Replace updated event in database
      ml_collection.replace_one({'_id': event['_id']}, event.copy()) 

    else:
      print "No such event found in db to replace, moving on...                   " + self.events[0]['name']

      self.lastAction = "NOT FOUND"
      self.lastEvent = self.events[0]

    # Move on to next event, update display
    self.changeText()

  def isWrong(self):
    print "Event does not have free food!                                       " + self.events[0]['name']
    self.undo.config(state = "normal")

    # Find event with matching id and tag it as no free food
    event = ml_collection.find_one({'_id': self.events[0]['id']})
    if event:
      self.lastAction = "free food"
      self.lastEvent = event

      event['free_food'] = False

      # Replace updated event in database
      ml_collection.replace_one({'_id': event['_id']}, event.copy()) 

    else:
      print "No such event found in db to replace, moving on...                   " + self.events[0]['name']

      self.lastAction = "NOT FOUND"
      self.lastEvent = self.events[0]

    # Move on to next event, update display
    self.changeText()

  def undo(self):
    print "Undoing last yes/no!"

    self.enable()

    if self.lastAction == "NOT FOUND":
      print "Adding previous event back to the list of events..."
      # Only skipped/moved past event
      # Add to beginning of events list
      self.events.insert(0, self.lastEvent)
      self.counter += 1

      # Update labels
      eventLabel.set(self.events[0]['name'])
      descriptionLabel.set(self.events[0]['description'])
      counterLabel.set("Events Remaining: " + str(self.counter))
    elif self.lastAction == "free food":
      print "Unmarking event and adding back to the list of events..."
      # Marked as free_food = true/false
      # Find event with matching id and remove free_food tag
      event = ml_collection.find_one({'_id': self.lastEvent['_id']})
      if event:
        event.pop('free_food', None)

        # Replace updated event in database
        ml_collection.replace_one({'_id': event['_id']}, event.copy()) 

        # Add to beginning of events list
        new_event = { 'name': event.get('name', "NO EVENT NAME"), 'description': event.get('description', "NO EVENT DESCRIPTION"), 'id': event['_id'] }
        self.events.insert(0, new_event)
        self.counter += 1

        # Update labels
        eventLabel.set(self.events[0]['name'])
        descriptionLabel.set(self.events[0]['description'])
        counterLabel.set("Events Remaining: " + str(self.counter))
      else:
        print "Didn't find an event to remove label from!"
    else:
      # Not undoing last action as it wasn't a YES/NO
      print "Nothing to undo!"


    self.lastAction = "none"
    self.lastEvent = {}
    self.undo.config(state = DISABLED)

  def skip(self):
    print "Skipping this event, idk what to do with it...                       " + self.events[0]['name']

    self.lastAction = "none"
    self.lastEvent = {}
    self.undo.config(state = DISABLED)

    # Move on to next event, update display
    self.changeText()

  def helpInstructions(self):
    print "Displaying instructions!"

    # Display message dialog with instructions explaining the buttons and our website
    tkMessageBox.showinfo(
      "Instructions",
      "Hello! Thanks for your help checking whether or not these events have free food or not. Check us out at www.whatsmappening.io!\n\nHere's what the buttons do:\nCORRECT: The event has free food! Also triggered with the LEFT arrow key.\n\nWRONG: The event doesn't have free food! How sad... Also triggered with the RIGHT arrow key.\n\nUNDO: Undoes the last CORRECT/WRONG you did!\n\nSKIP: Confused or don't know what to do with a particular event? Just skip it!\n\nFILTER: If multiple people are working on this at the same time, filter by letter so everyone is working on something different! By default/when first run, it has all events there.\n\nHELP: As you can tell, this one leads to the instructions!\n\nQUIT: Exit from the display and be on your merry way! Thanks for your help!"
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
    # Remove event we just processed from list
    self.events.pop(0)

    # Decrement number of events remaining to process
    self.counter -= 1
    counterLabel.set("Events Remaining: " + str(self.counter))

    # Check that there are still events left to process and update name label
    if self.events:
      eventLabel.set(self.events[0]['name'])
      descriptionLabel.set(self.events[0]['description'])
    else:
      # No more events to process, disable everything but HELP/QUIT
      self.disable()

  def filterLetter(self):
    self.lastAction = "none"
    self.lastEvent = {}

    print "Filter what events we're looking at by letter..."
    print "Do this if multiple people are doing this at the same time"

    self.enable()
    self.undo.config(state = DISABLED)

    # Ask user for input to filter what events you're looking at
    # Only look at events starting with a certain letter 
    # to make sure everyone's working on something different
    letter_num = tkSimpleDialog.askinteger("Letter Number", "Ints (1-26) correspond to letters (a-z)\nEnter 0 to look at all events", minvalue=0, maxvalue=26)

    if letter_num != None:
      if letter_num == 0:
        events_cursor = ml_collection.find({})
        self.events = []
        self.counter = 0
        if events_cursor.count() > 0:
          for event in events_cursor:
            # Events we already processed and approved have 'free_food' field
            # Look for events that haven't been processed and add to list
            if 'free_food' not in event:
              self.events.append({ 'name': event.get('name', "NO EVENT NAME"), 'description': event.get('description', "NO EVENT DESCRIPTION"), 'id': event['_id'] })
              self.counter = self.counter + 1
          if self.counter > 0:
            eventLabel.set(self.events[0]['name'])
            descriptionLabel.set(self.events[0]['description'])
            counterLabel.set("Events Remaining: " + str(self.counter))
          else:
            print 'Cannot find any events in database!'
            quit()
        else:
          print 'Cannot find any events in database!'
          quit()
      else:
        FILTER_LETTER = chr(ord('a') + letter_num - 1)
        print "Looking at events starting with letter " + FILTER_LETTER

        # Get all the events that start with the letter
        filter_regex = re.compile('^' + FILTER_LETTER + '.*', re.IGNORECASE)
        events_cursor = ml_collection.find({'name': filter_regex})
        
        # Append each event doc to a list to process (this is why we try to prevent overlap)
        # Empty list beforehand
        self.events = []
        self.counter = 0
        if events_cursor.count() > 0:
          for event in events_cursor:
            # Events we already processed and approved have 'free_food' field
            # Look for events that haven't been processed and add to list
            if 'free_food' not in event:
              self.events.append({ 'name': event.get('name', "NO EVENT NAME"), 'description': event.get('description', "NO EVENT DESCRIPTION"), 'id': event['_id'] })
              self.counter += 1
          if self.counter > 0:
            eventLabel.set(self.events[0]['name'])
            descriptionLabel.set(self.events[0]['description'])
            counterLabel.set("Events Remaining: " + str(self.counter))
          else:
            print 'Cannot find any events in database starting with letter ' + FILTER_LETTER
            counterLabel.set("Events Remaining: " + str(self.counter))
            self.disable()
        else:
          print 'Cannot find any events in database starting with letter ' + FILTER_LETTER
          counterLabel.set("Events Remaining: " + str(self.counter))
          self.disable()
    else:
      print "No letter chosen for filtering, leaving unfiltered"

  def disable(self):
    # No more events to process, disable everything but HELP/QUIT
    eventLabel.set("No more events to check")
    descriptionLabel.set("Thanks for your help!")
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

# Labels/strings
counterLabel = StringVar()
eventLabel = StringVar()
descriptionLabel = StringVar()

# Initializes App so tkinter/butttons are working
app = App(root)

# Pretty sure tkinter just loops back to the `root = Tk()` or something
root.mainloop()
