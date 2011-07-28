# -*- coding: utf-8 -*-
#
# Copyright 2011 Kenichi Sato <ksato9700@gmail.com>
#

#
# import
#
from wsgiref.handlers import format_date_time
from wsgiref.util import request_uri, shift_path_info, FileWrapper

import os
import time
import urllib
import urllib2
import urlparse
import calendar

from openid.server import server
from openid.store.filestore import FileOpenIDStore

#
# constant
#
_content_type_map = {
    ".ico": "image/x-icon",
    ".jpg": "image/jpeg",
    ".js": "text/javascript",
    ".css": "text/css",
    ".png": "image/PNG",
    ".PNG": "image/PNG",
    ".gif": "image/GIF",
    ".html": "text/html",
    ".svg": "image/svg+xml",
    ""    : "text/plain",
}

_http_response_message = {
    200: "200 OK",
    201: "201 Created",
    301: "301 Moved Permanently",
    304: "304 Not Modified",
    400: "400 Bad Request",
    403: "403 Forbidden",
    404: "404 Not Found",
    500: "500 Internal Server Error"
    }

#
# internal function
#
def _create_response_headers(content_type, content_length, last_modified=None):
    headers = []
    headers.append(("Content-type", content_type))
    headers.append(("Content-length", str(content_length)))
    headers.append(("Last-Modified",  format_date_time(last_modified)))
    return headers

def _html_response(code, message):
    return (code, _create_response_headers("text/html", len(message)),  message)


#
# class
#
class SasApp:
    def __init__(self, backend, debug):
        self.backend = backend
        self.debug = debug

        store = FileOpenIDStore('store')
        oidurl = 'aaaa'
        self.oidserver = server.Server(store, oidurl)

    def _create_response(self, environ):
        print environ
        path_info = environ['PATH_INFO']
        if_modified_since = environ.get('HTTP_IF_MODIFIED_SINCE','').split(';')[0]

        add_params = {}
        if environ.get('REQUEST_METHOD') == 'POST':
            rfile = environ['wsgi.input']
            length = int(environ.get('CONTENT_LENGTH', 0))
            query_string = rfile.read(length)
            post_params = urlparse.parse_qs(query_string)
        else:
            post_params = None

        p0 = shift_path_info(environ)

        if p0 in ("login"):
            return (404, [], [])
        else:
            path = path_info[1:]
            try:
                f = open(path, 'rb')
            except Exception as e:
                # print e
                return (404, [], [])

            fs = os.fstat(f.fileno())
            if if_modified_since and \
                    (int(fs.st_mtime) <= calendar.timegm( \
                time.strptime(if_modified_since, 
                              "%a, %d %b %Y %H:%M:%S %Z"))):
                    return (304, [], [])
            else:
                dotindex = path.rfind('.')
                if dotindex < 0:
                    ext = ''
                else:
                    ext = path[dotindex:]
                return (200, _create_response_headers(_content_type_map[ext], fs[6], fs.st_mtime), FileWrapper(f))
        

    def __call__(self, environ, start_response):
        code, headers, message = self._create_response(environ)
        try:
            start_response(_http_response_message[code], headers)
        except IndexError:
            print "unknown code : %d" % code
            raise

        return message
