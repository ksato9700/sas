# -*- coding: utf-8 -*-
#
# Copyright 2011 Kenichi Sato <ksato9700@gmail.com>
#

import datetime

_user_credentials = {
    11111: "paul",
    22222: "noel",
}

_users = {
    11111: {
        "fullname":"John Lennon",
        "nickname":"john",
        "dob": datetime.datetime(1940,10,9),
        "email":"john@example.com",
        "gender": "male",
        "postcode":"12345",
        "country":"US",
        "language":"En",
        "timezone":"-0500",
        },
    22222: {
        "fullname":"William Gallagher",
        "nickname":"liam",
        "dob": datetime.datetime(1972,9,21),
        "email":"liam@example.com",
        "gender": "male",
        "postcode":"54321",
        "country":"GB",
        "language":"En",
        "timezone":"0000",
        },
    }

class SampleBackend(object):
    def __init__(self):
        pass

    def authenticate(self, userid, password):
        try:
            return _user_credentials[userid] == password
        except KeyError:
            return False

    def get_account_info(self, userid):
        return _users.get(userid)

    def lookup_userid(self, email):
        for uid in _users:
            if _users[uid]["email"] == email:
                return uid
        return None

def backend():
    return SampleBackend()
