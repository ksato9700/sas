# -*- coding: utf-8 -*-
#
# Copyright 2011 Kenichi Sato <ksato9700@gmail.com>
#

class SampleBackend(object):
    def __init__(self):
        pass

    def authenticate(self, username, password):
        if username == 'john' and password == 'paul':
            return True
        else:
            return False

def backend():
    return SampleBackend()
