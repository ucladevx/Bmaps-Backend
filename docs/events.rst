Events
======

Welcome to the Mappening Events API! Through a RESTful interface, this API provides information on all the events happening around UCLA. The simplest way to access this data is to go to the url `whatsmappening.io/api/v1/events <https://whatsmappening.io/api/v1/events>`_ to get a comprehensive listing of all upcoming UCLA events. See the explanation of |event| objects below. The Events API offers various ways to search and filter the event data and also allows for independent processing and filtering.

Event
-----

.. |event| replace:: `Event`_

An |event| object is a GeoJSON with the following keys:

.. data:: geometry

    .. |geometry| replace:: :data:`geometry`

    The |geometry| object contains the coordinates for the |event| in the format required by Mapbox. The |geometry| data must be set according to the location information of the |event|. If no location information is provided or can be supplied through the locations API, the event pin cannot be displayed with Mapbox.

    .. code-block:: rest
        :caption: |event| Object Structure:

        geometry: { type: "Point", coordinates: [ ``latitude``, ``longitude`` ]}

    .. attribute:: type

        The *type* of the |geometry| object. Should always be of value ``"Point"`` as |event| locations are treated as a point with a singular ``(latitude, longitude)`` pair.

        .. note:: An |geometry|'s type will always be of value "Point".

    .. attribute:: geometry.coordinates

        The *coordinates* of the |geometry| object. Contains ``latitude`` and ``longitude`` Number values that correspond to the location of the |event|.

        :latitude: a Number value between the range ``(-90, 90)``

        :longitude: a Number value between the range ``(-180, 180)``

.. data:: id

    .. |id| replace:: :data:`id`

    The |id| contains a unique *ID* for the |event| object.

    .. note:: Each |id| is unique. This allows for searching for events by index.

.. data:: properties

    .. |properties| replace:: :data:`properties`

    Contains all the |event| information and will be explored further below.

    .. code-block:: rest
        :caption: |properties| Object Structure:

        properties: { 
          category: "<NONE>", 
          duplicate_occurence: false, 
          is_cancelled: false, 
          name: "Mappening Launch", 
          start_time: "2018-08-21T04:20:00-0700", 
          stats: { attending: #, interested: #, maybe: #, noreply: # }
        }
        
    **Mandatory Event Properties**

        These properties must have a valid value for every event.

        .. attribute:: category

            The *category* of the |event|. All the categories can be seen by dynamically calling ``/categories``. About half of events have a category and the rest have <NONE>.

        .. attribute:: name

            The String of the |event|'s name. A specific event can be searched by calling ``/name/<event_name>``.

        .. attribute:: stats

            The JSON for events from Facebook with attendance stats with a ~6 hour accuracy. Contains 4 keys: ``attending``, ``noreply``, ``interested``, and ``maybe``, each with an integer value.

        .. attribute:: start_time

            The String start time of the |event| in the format ``Sat, 17 Feb 2018 23:30:00 GMT-0800``.
            
        .. attribute:: is_cancelled

            The Boolean indicating that the |event| is cancelled.
            
        .. attribute:: duplicate_occurrence

            The Boolean indicating this is a single |event| taking place on multiple days i.e a weekly farmers market, not a multiday event like a hackathon.

    **Potential Event Properties**

        If these details/properties aren't present, the JSON keys won't be present.

        .. attribute:: cover_picture

            The String url to the cover picture associated with the |event|.

        .. attribute:: time_updated

            The time the |event| was last updated.

        .. attribute:: description

            The String of the |event|'s description.

        .. attribute:: place

            A JSON with a ``location`` key with a mandatory ``country``, ``city``, ``latitude``, and ``longitude``. Other potential place details such as ``name`` can be seen in the example event below.

        .. attribute:: hoster

            The String of the host name.

        .. attribute:: ticket_uri

            The link to the |event|'s ticketing.

        .. attribute:: end_time

            The String end time of the |event| in the format ``Sat, 17 Feb 2018 23:30:00 GMT-0800``.

        .. attribute:: free_food

            Whether or not the |event| has free food, currently just a strong NO.

.. code-block:: rest
    :caption: Sample |event| Object

    {
      geometry: {
        coordinates: [-118.44681959102,
          34.070367696979
        ],
        type: "Point"
      },
      id: "175752283196850",
      properties: {
        category: "Tech",
        cover_picture: "https://scontent.xx.fbcdn.net/v/t31.0-8/s720x720/27021656_1621551394602436_6299488329760837839_o.jpg?oh=057a6b50a89f8a1fa3684c7c25563b86&oe=5B035F3D",
        description: "LA Hacks is one of the biggest student-run hackathons on the West Coast, held every spring at UCLA's iconic Pauley Pavilion. Over 1000 students from distinguished universities across the nation work together in teams to challenge themselves and create something beyond their comfort level - all in the span of 36 hours. Collaborate and build creative solutions to problems, while pushing the limits of your mind and body to make something amazing. From Evan Spiegel (CEO, Snapchat) and Sean Rad (CEO, Tinder), to 8 time gold medalist, Apolo Ohno, and a special pre-screening of HBO's Silicon Valley, LA Hacks has welcomed many leaders and role models in tech. With industry mentors, technical workshops, and founder panels, LA Hacks works to broaden the scope of technology. EVENT DETAILS: Date: March 30th - April 1st, 2018 Location: Pauley Pavilion WHO WE ARE: LA Hacks epitomizes innovation, perseverance, and also pushing hackers to test their potential. We are UCLA students from many corners of campus, all united by one big goal: to give over 1000 college students the opportunity to come together and collaborate with industry leaders and innovative companies to develop impactful products with cutting-edge technologies.",
        end_time: "2018-04-01T15:00:00-0700",
        hoster: "LA Hacks",
        is_cancelled: false,
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

-----------------
API DOCS
-----------------

.. automodule:: mappening.api.events
   :members:

