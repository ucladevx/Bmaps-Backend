Users
=====

Welcome to the Mappening Users API! The simplest way to access the API is to go to the url `whatsmappening.io/api/v2/users <https://whatsmappening.io/api/v2/users>`_. See the explanation of the API below. The Users API is NOT intended to be a public API, admin permissions required to access any other user data.

User
----

.. |user| replace:: `User`_

A |user| object is a JSON with the following keys:

.. data:: account

    .. |account| replace:: :data:`account`

    The |account| object contains info related to the user's account with Mappening. Unique identifiers and user status/access permissions are set in the |account| fields.

    .. code-block:: rest
        :caption: |account| Object Structure:

        account: { 
          id: "unique_int", 
          is_active: true, 
          is_admin: false, 
          username: "str", 
          password_hash: "str", 
          time_joined: "datetime", 
          time_updated: "datetime"
        }

    .. attribute:: id
        :noindex:

        Uniquely identifies the |user| object. Should be a unique int, typically from Facebook accounts.

    .. attribute:: is_active

        Specifies whether or not a |user| is active. If true, |user| has an activated account that they can log in to, otherwise account will be rejected/suspended from use. |user| information remains in the database if deactivated.

    .. attribute:: is_admin

        Specifies whether or not a |user| has admin privileges. An admin can grant and remove privileges at will. Should probably create a superpowered admin but devs are too lazy.

    .. attribute:: username

        TODO: implement username/password accounts rather than just Facebook Authentication.

    .. attribute:: password_hash

        TODO: implement username/password accounts rather than just Facebook Authentication.

    .. attribute:: time_joined

        The date and time in UTC that the |user| registered a |user| account with Mappening.

    .. attribute:: time_updated
        :noindex:

        The date and time in UTC that the |user| last logged in or their |user| info was last updated.

.. data:: app

    .. |app| replace:: :data:`app`

    The |app| object contains the app-related information for the |user|, or information that gives each |user| a personalized experience on Mappening.

    .. code-block:: rest
        :caption: |app| Object Structure:

        app: { 
          filters: [`filter`, `filter`], 
          favorites: [`event_id`, `event_id`], 
          past_events: [`event_id`, `event_id`]
        }

    .. attribute:: filter

        Keeps track of what filters the |user| is currently using. If conflicting filters are present (such as `now` and `upcoming`), they are both present in the database but the Events filtering API will only return appropriate results for the first received filter. 

        Allowed values: *'now', 'upcoming', 'period', 'morning', 'afternoon', 'night', 'oncampus', 'offcampus', 'nearby', 'popular', 'food'*

    .. attribute:: favorites

        The events that the |user| has favorited. Only the event ID is stored in the database and there is no guarantee that the event ID is a valid ID.

    .. attribute:: past_events

        The events that the |user| has (TODO:) attended in the past. Only the event ID is stored in the database and there is no guarantee that the event ID is a valid ID.

.. data:: personal_info

    .. |personal_info| replace:: :data:`personal_info`

    The |personal_info| object contains |user| personal information to help customize interaction with each |user|.

    .. code-block:: rest
        :caption: |personal_info| Object Structure:

        personal_info: { 
          email: "mappeningdevx@gmail.com", 
          full_name: "Dora D. DevX", 
          first_name: "Dora", 
          last_name: "DevX" 
        }

    .. attribute:: email

        The string email of the |user|. May not be present in which case the field will be an empty string. TODO: email validation.

    .. attribute:: full_name

        The string full name of the |user|. Not limited to just first and last name. The value is not updated if the first and last names are updated.

    .. attribute:: first_name

        The string first name of the |user|.

    .. attribute:: last_name

        The string last name of the |user|.

.. code-block:: rest
    :caption: Sample |user| Object

    {
      "account": {
        "id": "1557193131009244", 
        "is_active": true, 
        "is_admin": true, 
        "password_hash": "", 
        "time_joined": "2018-05-12 12:26:03", 
        "time_updated": "2018-05-13 07:08:49", 
        "username": ""
      }, 
      "app": {
        "favorites": [
          "42", 
          "69"
        ], 
        "filters": [
          "now",
          "popular",
          "food"
        ], 
        "past_events": [
          "101", 
          "821"
        ]
      }, 
      "personal_info": {
        "email": "katrina@thewijayas.com", 
        "first_name": "Katrina", 
        "full_name": "Katrina Wijaya", 
        "last_name": "Wijaya"
      }
    }

API Docs
--------

.. automodule:: mappening.api.users
   :members:
