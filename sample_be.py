# -*- coding: utf-8 -*-
#
# Copyright 2011 Kenichi Sato <ksato9700@gmail.com>
#

_users = {
    "john": ("paul", 11111, "beatles"),
    "liam": ("noel", 22222, "oasis"),
}

class SampleBackend(object):
    def __init__(self):
        pass

    def authenticate(self, username, password):
        account_info = _users.get(username, None)
        if account_info and account_info[0] == password:
            return {
                "userid": account_info[1],
                "handle": account_info[2],
                }
        else:
            return None

def backend():
    return SampleBackend()
