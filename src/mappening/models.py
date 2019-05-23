from mappening import db
import datetime
import decimal

def handle_value(value):
    if value is None:
        return None
    elif isinstance(value, datetime.date):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return float(value)

class BaseModel(db.Model):
    """ Common methods for all models """
    __abstract__ = True

    def serialize(self):
        """ Returns object data in format easy to jsonify """
        return {
            column: value if not isinstance(value, (datetime.date, decimal.Decimal)) else handle_value(value)
            for column, value in self.__dict__.items() if column not in ('_sa_instance_state')
        }

class User(BaseModel):
    __table__ = BaseModel.metadata.tables['user_account']

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

