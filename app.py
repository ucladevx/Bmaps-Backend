# Starter app.py that connects to mlab database

from flask import Flask
import pymongo

app = Flask(__name__)

### Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
uri = 'mongodb://devx_dora:3map5me@ds044709.mlab.com:44709/mappening_data' 

# Set up database connection.
client = pymongo.MongoClient(uri)
db = client.get_default_database()

# Sample entry
MAP_POST = {
  "name": "Dora",
  "id": 111
}

MAP_POSTS = [
  {
      "name": "Boots",
      "id": 180
  },
  {
      "name": "Swiper",
      "id": 404
  }
]

@app.route('/')
def printFromDB():
    # Get collection (group of documents). Nothing is required to create a 
    # collection; it is created automatically when we insert.
    # Alternative format: map_collection = db['map_test']
    map_collection = db.map_test

    # Insert a document into the collection
    map_collection.insert_one(MAP_POST)
    map_collection.insert_many(MAP_POSTS)

    # Find a document in the collection
    # find_one() gets first document in collection
    print (map_collection.find_one())
    # find_one() with search term
    print (map_collection.find_one({"id": 404}))
    # find_one() with search term to print particular field
    print (map_collection.find_one({"id": 111})['name'])

    # Find more than one document in a collection
    # find() returns a Cursor instance, which allows us to iterate over all 
    # matching documents.
    for post in map_collection.find():
      # print(post['name'] + " is #" + post['id']) 
      print("{} = {}".format(post['name'], post['id']))

    # Get count of documents matching a query
    print (map_collection.count())
    print (map_collection.find({"name": "Dora"}).count())

    # Update an entry
    # Set value of entry
    query = {'name': 'Swiper'}
    map_collection.update_one(query, {'$set': {'id': 444}})
    print (map_collection.find_one({"name": "Swiper"}))
    # Increment value of entry
    query = {'id': 444}
    map_collection.update_one(query, {'$inc': {'id': 111}})
    print (map_collection.find_one({"name": "Swiper"}))
    
    # Clear collection 
    ### Since this is an example, we'll clean up after ourselves.
    db.drop_collection('map_test')

    # Only close the connection when your app is terminating
    client.close()

    return "Success!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
    # Flask defaults to port 5000
