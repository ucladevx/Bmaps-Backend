from mappening import db
import datetime

def handle_datetime(date):
  if date is None:
    return None
  return date.strftime("%Y-%m-%d %H:%M:%S")

class BaseModel(db.Model):
    """ Common methods for all models """
    __abstract__ = True

    def serialize(self):
        """ Returns object data in format easy to jsonify """
        return {
            column: value if not isinstance(value, datetime.date) else handle_datetime(value)
            for column, value in self.__dict__.items() if column not in ('_sa_instance_state')
        }

class User(BaseModel):
    __table__ = BaseModel.metadata.tables['g_user']

class Organizer(BaseModel):
    __table__ = BaseModel.metadata.tables['organizer']

class Address(BaseModel):
    __table__ = BaseModel.metadata.tables['address']

class Location(BaseModel):
    __table__ = BaseModel.metadata.tables['location']

class Event(BaseModel):
    __table__ = BaseModel.metadata.tables['event']

class Category(BaseModel):
    __table__ = BaseModel.metadata.tables['category']

class Event_Interest(BaseModel):
    __table__ = BaseModel.metadata.tables['event_interest']

class Event_Category(BaseModel):
    __table__ = BaseModel.metadata.tables['event_category']

