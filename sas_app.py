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

from openid.extensions import sreg
from openid.server import server
from openid.store.filestore import FileOpenIDStore
from openid.consumer import discover

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
    302: "302 Found",
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

def _html_response(code, message, headers=[]):
    headers = headers + _create_response_headers("text/html", len(message))
    return (code, headers,  message)

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
        self.last_checked = {}
        self.approved_ids = {}

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
            
    def _is_authorized(self, identity_url, trust_root, userid):
        if userid is None or identity_url != self.baseurl + '/id/' + str(userid):
            return False
        key = (identity_url, trust_root)
        return self.approved_ids.get(key) is not None


    def _create_oid_response(self, response):
        webresponse = self.oidserver.encodeResponse(response)
        headers = [(k,v) for k,v in webresponse.headers.iteritems()]
        return _html_response(webresponse.code, 
                              webresponse.body if webresponse.body else "",
                              headers=headers,
                              )

    def _add_sreg_response(self, request, response, identity):
        userid = int(identity.split("/")[-1])
        account_info = self.backend.get_account_info(userid)
        sreg_req = sreg.SRegRequest.fromOpenIDRequest(request)
        sreg_resp = sreg.SRegResponse.extractResponse(sreg_req, account_info)
        response.addExtension(sreg_resp)

    def _approved(self, request, identifier=None):
        response = request.answer(True, identity=identifier)
        self._add_sreg_response(request, response, identifier)
        return response

    def _create_response(self, environ):
        if not self.oidserver:
            self._set_oidserver(environ)

        path_info = environ['PATH_INFO']
        if_modified_since = environ.get('HTTP_IF_MODIFIED_SINCE','').split(';')[0]

        cookie_str = environ.get('HTTP_COOKIE', '')
        userid = None
        username = None
        handle = None
        if cookie_str:
            cookie = Cookie.SimpleCookie(cookie_str)
            try:
                userid = int(cookie['userid'].value)
                account_info = self.backend.get_account_info(userid)
                username = account_info["email"]
                handle   = account_info["nickname"]
            except KeyError:
                pass

        if environ.get('REQUEST_METHOD') == 'POST':
            rfile = environ['wsgi.input']
            length = int(environ.get('CONTENT_LENGTH', 0))
            query_string = rfile.read(length)
        else: #GET
            query_string = environ.get('QUERY_STRING', '')
        query = urlparse.parse_qs(query_string)
        query = dict([(key,query[key][0]) for key in query.keys()])
        #print "query:", query

        p0 = shift_path_info(environ)

        if p0 == "":
            if userid:
                message = self._create_view("main",(self.baseurl,userid,username,handle))
                return _html_response(200, message)
            else:
                return _http_redirect("/signin")

        elif p0 == "id":
            userid = int(shift_path_info(environ))
            message = self._create_view("id", (self.baseurl, userid))
            return _html_response(200, message)

        elif p0 == "yadis":
            userid = int(shift_path_info(environ))
            types = (discover.OPENID_2_0_TYPE, discover.OPENID_1_0_TYPE)
            message = self._create_view("id", (self.baseurl, userid, types))
            return _html_response(200, message)

        elif p0 == "openidserver":
            try:
                request = self.oidserver.decodeRequest(query)
            except server.ProtocolError, why:
                self.display_response(why)
                return

            if request is None:
                message = self._create_view("about", self)
                return _html_response(200, message)

            if request.mode in ("checkid_immediate", "checkid_setup"):
                if self._is_authorized(request.identity, request.trust_root, userid):
                    return self._create_oid_response(self._approved(request))
                elif request.immediate:
                    return self._create_oid_response(request.answer(False))
                else:
                    self.last_checked[userid] = request
                    message = self._create_view("decide", (self.baseurl + "/id/",
                                                           userid,
                                                           request.identity,
                                                           request.idSelect(),
                                                           request.trust_root,
                                                           ))
                    return _html_response(200, message)
            else:
                response = self.oidserver.handleRequest(request)
                return self._create_oid_response(response)

        elif p0 == "allow":
            request = self.last_checked.get(userid)
            if 'yes' in query:
                if 'login_as' in query:
                    userid = int(query['login_as'])
                if request.idSelect():
                    identity = self.baseurl + '/id/' + query['identifier']
                else:
                    identity = request.identity

                trust_root = request.trust_root
                if query.get('remember', 'no') == 'yes':
                    self.approved_ids[(identity, trust_root)] = 'always'
                response = self._approved(request, identity)

            elif 'no' in query:
                response = request._answer(False)

            else:
                assert False, 'strange allow post.  %r' % (query,)

            return self._create_oid_response(response)
            
        elif p0 == "signin":
            message = self._create_view("signin", ("/", "/"))
            return _html_response(200, message)

        elif p0 == "signin_submit":
            success_url = query['success_url']
            fail_url    = query['fail_url']
            if 'cancel' in query:
                return _http_redirect(fail_url)

            elif 'signout' in query:
                headers = []
                for key, morsel in cookie.items():
                    morsel['expires'] = -86400
                    headers.append(("Set-Cookie", morsel.OutputString()))
                return _http_redirect(success_url, headers=headers)

            elif 'username' in query:
                username = query['username']
                password  = query['password']

                userid = self.backend.lookup_userid(username)
                if self.backend.authenticate(userid, password):
                    headers = [
                        ('Set-Cookie', "userid=%d; path=/" % userid),
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
