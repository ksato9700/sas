# -*- coding: utf-8 -*-
#
# Copyright 2011 Kenichi Sato <ksato9700@gmail.com>
#

#
# import
#
from mako.lookup import TemplateLookup
from mako.exceptions import RichTraceback

from wsgiref.handlers import format_date_time
from wsgiref.util import request_uri, shift_path_info, FileWrapper

import os
import time
import urllib
import urllib2
import urlparse
import calendar
import Cookie

from openid.server import server
from openid.store.filestore import FileOpenIDStore

#
# constant
#
mylookup = TemplateLookup(directories=['templates'], format_exceptions=True,
                          output_encoding='utf-8', encoding_errors='replace',
                          module_directory='/tmp/sas_mako_modules')
                          
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

def _http_redirect(location, headers=[]):
    headers.append(('Location', location))
    return (301, headers, [])

#
# class
#
class SasApp:
    def __init__(self, backend, debug):
        self.backend = backend
        self.debug = debug
        self.oidserver = None

    def _set_oidserver(self, environ):
        store = FileOpenIDStore('store')
        self.baseurl = "%s://%s" % (environ['wsgi.url_scheme'], environ['HTTP_HOST'])
        oidurl = self.baseurl + '/openid'
        self.oidserver = server.Server(store, oidurl)
        
    def _create_view(self, ttype, args):
        try:
            mytemplate = mylookup.get_template('%s.mako' % ttype)
            return mytemplate.render(args=args)
        except:
            traceback = RichTraceback()
            for (filename, lineno, function, line) in traceback.traceback:
                print "File %s, line %s, in %s" % (filename, lineno, function)
                print line, "\n"
                print "%s: %s" % (str(traceback.error.__class__.__name__),
                                  traceback.error)
            
    def _create_response(self, environ):
        if not self.oidserver:
            self._set_oidserver(environ)

        path_info = environ['PATH_INFO']
        if_modified_since = environ.get('HTTP_IF_MODIFIED_SINCE','').split(';')[0]

        cookie_str = environ.get('HTTP_COOKIE', '')
        if cookie_str:
            cookie = Cookie.SimpleCookie(cookie_str)
            userid = cookie['userid'].value
            username = cookie['username'].value
            handle = cookie['handle'].value
        else:
            userid = None
            username = None

        add_params = {}
        if environ.get('REQUEST_METHOD') == 'POST':
            rfile = environ['wsgi.input']
            length = int(environ.get('CONTENT_LENGTH', 0))
            query_string = rfile.read(length)
            post_params = urlparse.parse_qs(query_string)
        else:
            post_params = {}

        p0 = shift_path_info(environ)

        if p0 == "":
            if userid:
                message = self._create_view("main", (self, userid, username, handle) )
                return _html_response(200, message)
            else:
                return _http_redirect("/signin")
        elif p0 == "signin":
            message = self._create_view("signin", ("/", "/"))
            return _html_response(200, message)
        elif p0 == "signin_submit":
            success_url = post_params['success_url'][0]
            fail_url    = post_params['fail_url'][0]
            if 'cancel' in post_params:
                return _http_redirect(fail_url)

            elif 'signout' in post_params:
                headers = []
                for key, morsel in cookie.items():
                    morsel['expires'] = -86400
                    headers.append(("Set-Cookie", morsel.OutputString()))
                return _http_redirect(success_url, headers=headers)

            elif 'username' in post_params:
                username = post_params['username'][0]
                password  = post_params['password'][0]

                account_obj = self.backend.authenticate(username, password)
                if account_obj:
                    headers = [
                        ('Set-Cookie', "userid=%d; path=/" % account_obj["userid"]),
                        ('Set-Cookie', "handle=%s; path=/" % account_obj["handle"]),
                        ('Set-Cookie', "username=%s; path=/" % username),
                        ]
                    return _http_redirect(success_url, headers=headers)
                else:
                    return _http_redirect(fail_url)
            else:
                return _http_redirect(fail_url)
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
                return (200, _create_response_headers(_content_type_map[ext], fs[6], 
                                                      fs.st_mtime), FileWrapper(f))

    def __call__(self, environ, start_response):
        code, headers, message = self._create_response(environ)
        try:
            start_response(_http_response_message[code], headers)
        except IndexError:
            print "unknown code : %d" % code
            raise

        return message
