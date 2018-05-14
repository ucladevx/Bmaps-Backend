Users
=====

Welcome to the Mappening Users API! The simplest way to access the API is to go to the url `whatsmappening.io/api/v2/users <https://whatsmappening.io/api/v2/users>`_. See the explanation of the API below. The Users API is NOT intended to be a public API, admin permissions required to access any other user data.

User
----

.. |user| replace:: `User`_

A |user| object is a JSON with the following keys

.. code-block:: rest
    :caption: Sample |user| Object

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

.. automodule:: mappening.api.users
   :members:
