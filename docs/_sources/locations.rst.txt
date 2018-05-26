Locations
=========

Welcome to the Mappening Locations API! The simplest way to access the API is to go to the url `www.mappening.io/api/v2/locations <https://www.mappening.io/api/v2/locations>`_. See the explanation of the API below. The Locations API mainly offers a way get location data for a specific Westwood/UCLA location. As the database is relatively young, some locations may be missing or may have incorrect data. If any inconsistencies are noted, please let us know at mappeningdevx@gmail.com

Location
--------

.. |location| replace:: `Location`_

A |location| object is a JSON with the following keys:

.. data:: alternative_names

    .. |alternative_names| replace:: :data:`alternative_names`

    The |alternative_names| list contains different names/aliases for a single location. Contains processed/tokenized versions of names as well.

.. data:: city

    .. |city| replace:: :data:`city`

    The |city| field contains the city the |location| is located in.

.. data:: country

    .. |country| replace:: :data:`country`

    The |country| field contains the country the |location| is located in.

.. data:: latitude

    .. |latitude| replace:: :data:`latitude`

    The |latitude| field contains the latitude the |location| is located at.

.. data:: longitude

    .. |longitude| replace:: :data:`longitude`

    The |longitude| field contains the longitude the |location| is located at.

.. data:: name
    :noindex:

    .. |name| replace:: :data:`name`

    The |name| field contains one of the main names of the |location|.

.. data:: state

    .. |state| replace:: :data:`state`

    The |state| field contains the state the |location| is located in.

.. data:: street

    .. |street| replace:: :data:`street`

    The |street| field contains the street the |location| is located in.

.. data:: zip

    .. |zip| replace:: :data:`zip`

    The |zip| field contains the zip the |location| is located in.

.. code-block:: rest
    :caption: Sample |location| Object

    {
      "alternative_names": [
        "Powell Library", 
        "UCLA Powell", 
        "UCLA Powell Library", 
        "Powell"
      ], 
      "city": "Los Angeles", 
      "country": "United States", 
      "latitude": 34.07161260000001, 
      "longitude": -118.4421809, 
      "name": "Powell Library", 
      "state": "CA", 
      "street": "120S Election Walk", 
      "zip": 90095
    }

API Docs
--------

.. automodule:: mappening.api.locations
   :members:

