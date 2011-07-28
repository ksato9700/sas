#
# Copyright 2011 Kenichi Sato <ksato9700@gmail.com>
#

#
# import
#
import argparse
from wsgiref.simple_server import make_server

from sas_app import SasApp

#
# function
#
def address_string_wo_hostresolve(s):
    host = s.client_address[0]
    #host = socket.getfqdn(host)
    return host

def main():
    parser = argparse.ArgumentParser(description="Simple Auth Server")
    parser.add_argument("-p", "--port", type=int, dest="port", metavar="PORT", 
                        default=10100, help="port number to listen")
    parser.add_argument("-D", "--debug", type=int, dest="debug", metavar="DEBUG",
                        default=100, help="Debug") 
    parser.add_argument("backend", metavar="BECKEND", help="Backend")
    args = parser.parse_args()
    
    sas_app = SasApp(__import__(args.backend).backend(), debug=args.debug)
    server = make_server("", args.port, sas_app)
    server.RequestHandlerClass.address_string = address_string_wo_hostresolve

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        import sys
        sys.exit()

if __name__ == '__main__':
    main()
