Events
======

Welcome to the Mappening Events API! Through this RESTful interface, we provide you with all the events happening around UCLA. The easiest way to use this is to simply go to the url `api.ucladevx.com/events <http://api.ucladevx.com/v2/events>`_ and take all the events. See the explanation of events below. We offer many ways to search and filter these events through our api though you could do it yourself.

-----------------
Event Object
-----------------
An *event* object is a GeoJSON which means it has the following keys:

* geometry: with a type of "Point" and coordinates for latitude and longitude
* id: a unique id for this event
* properties: this contains all the event information and will be explored below

**Mandatory Event Properties**

These properties must have a valid value for every event.

* category: All the categories can be seen by dynamically calling /event-categories. About half of events have a category and the rest have <NONE>
* name: String of event's name
* stats: JSON for events from Facebook with attendance stats from at ~6 hour accuracy. Will have 4 keys 'attending', 'noreply', 'interested', and 'maybe' each with a integer value.
* start_time: String start time of event in the format Sat, 17 Feb 2018 23:30:00 GMT-0800
* is_cancelled: Boolean indicating event is cancelled
* duplicate_occurrence: Boolean indicating this is a single event taking place on multiple days i.e a weekly farmers market, not a multiday event like a hackathon

**Potential Event Properties**
If these details aren't present, the JSON keys won't be present
* description: String description
* place: JSON with a location key with a mandatory country, city, latitude, and longitude. Other potential place details such as name can be seen in the example event below
* hoster: string of the host name
* ticket_uri: link to event ticketing
* end_time: String end time of event in the format Sat, 17 Feb 2018 23:30:00 GMT-0800
* free_food: If event has free food, currently just a strong NO

**Sample Event**::

{
  geometry: {
    coordinates: [-118.44681959102,
      34.070367696979
    ],
    type: "Point"
  },
  id: "175752283196850",
  properties: {
    cover_picture: "https://scontent.xx.fbcdn.net/v/t31.0-8/s720x720/27021656_1621551394602436_6299488329760837839_o.jpg?oh=057a6b50a89f8a1fa3684c7c25563b86&oe=5B035F3D",
    description: "LA Hacks is one of the biggest student-run hackathons on the West Coast, held every spring at UCLA's iconic Pauley Pavilion. Over 1000 students from distinguished universities across the nation work together in teams to challenge themselves and create something beyond their comfort level - all in the span of 36 hours. Collaborate and build creative solutions to problems, while pushing the limits of your mind and body to make something amazing. From Evan Spiegel (CEO, Snapchat) and Sean Rad (CEO, Tinder), to 8 time gold medalist, Apolo Ohno, and a special pre-screening of HBO's Silicon Valley, LA Hacks has welcomed many leaders and role models in tech. With industry mentors, technical workshops, and founder panels, LA Hacks works to broaden the scope of technology. EVENT DETAILS: Date: March 30th - April 1st, 2018 Location: Pauley Pavilion WHO WE ARE: LA Hacks epitomizes innovation, perseverance, and also pushing hackers to test their potential. We are UCLA students from many corners of campus, all united by one big goal: to give over 1000 college students the opportunity to come together and collaborate with industry leaders and innovative companies to develop impactful products with cutting-edge technologies.",
    end_time: "2018-04-01T15:00:00-0700",
    hoster: "LA Hacks",
    is_canceled: false,
    name: "LA Hacks 2018",
    place: {
      location: {
        city: "Los Angeles",
        country: "United States",
        latitude: 34.070367696979,
        longitude: -118.44681959102,
        state: "CA",
        street: "301 Westwood Plz",
        zip: "90095"
      },
      name: "Pauley Pavilion"
    },
    start_time: "2018-03-30T16:00:00-0700",
    stats: {
      attending: 179,
      interested: 1473,
      maybe: 1473,
      noreply: 293
    },
    time_updated: "2018-03-25 19:10:07.585374"
  },
  type: "Feature"
}

.. automodule:: mappening.api.events
   :members:
