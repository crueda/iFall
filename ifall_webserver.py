#!/usr/bin/env python
#-*- coding: UTF-8 -*-

# autor: Carlos Rueda
# date: 2015-03-25
# mail: carlos.rueda@deimos-space.com
# version: 1.0

##################################################################################
# version 1.0 release notes:
# Initial version
##################################################################################


import string, cgi, time
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import time
import sys
import xml.etree.ElementTree as ET
import MySQLdb
import datetime
import os
from SocketServer import ThreadingMixIn
import threading
import os
import logging, logging.handlers

#### VARIABLES #########################################################
MAX_THREADS = 51

INTERNAL_LOG_FOLDER = "/var/log/ifall/ifall.log"
PID = "/var/tmp/webserver"
########################################################################

if os.access(os.path.expanduser(PID), os.F_OK):
        print "Checking if ifall web server is already running..."
        pidfile = open(os.path.expanduser(PID), "r")
        pidfile.seek(0)
        old_pd = pidfile.readline()
        # process PID
        if os.path.exists("/proc/%s" % old_pd) and old_pd!="":
			print "You already have an instance of the ifall web server running"
			print "It is running as process %s," % old_pd
			sys.exit(1)
        else:
			print "Trying to start ifall web server..."
			os.remove(os.path.expanduser(PID))

#This is part of code where we put a PID file in the lock file
pidfile = open(os.path.expanduser(PID), 'a')
print "ifall web server started with PID: %s" % os.getpid()
pidfile.write(str(os.getpid()))
pidfile.close()

# definimos los logs internos que usaremos para comprobar errores
try:
	logger = logging.getLogger('ifall')
	loggerHandler = logging.handlers.TimedRotatingFileHandler(INTERNAL_LOG_FOLDER, 'midnight', 1, backupCount=10)
	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	loggerHandler.setFormatter(formatter)
	logger.addHandler(loggerHandler)
	logger.setLevel(logging.DEBUG)
except:
	print '------------------------------------------------------------------'
	print '[ERROR] Error writing log at %s' % INTERNAL_LOG_FOLDER 
	print '[ERROR] Please verify path folder exits and write permissions'
	print '------------------------------------------------------------------'
	exit()

 
class MyHandler(BaseHTTPRequestHandler):
    def __init__(self, *args):
        self.subtype = 'application/xml'
        BaseHTTPRequestHandler.__init__(self, *args)
        
    def do_POST(self):
    	logger.info("en do_POST")
    	
        try:
			if threading.activeCount() > MAX_THREADS :
				logger.warn('%s -- Numero de hilos en ejecucion: %d', threading.currentThread().getName(), threading.activeCount()-1)
				logger.warn('Se ha alcanzado el numero maximo de hilos')
				self.send_response(202)
				
			else:
				# obtenemos el nombre del thread que va a manejar el POST
				threadName = threading.currentThread().getName()			
				logger.info('%s -- Numero de threads en ejecucion: %d', threadName, threading.activeCount()-1)
			
				# Obtenemos las cabeceras para verificar que la trama es de un sonim y obtenemos la longitud de los datos indicada en la cabecera
				clength = int(self.headers.getheader('content-length'))
			
				# Obtenemos la IP del dispositivo
				clientIP = self.client_address[0]		
				

				# Verificaciones previas
				#if ctype != "application/xml; charset=utf-8" or (cuser != "Sonim LWC 1.0" and cuser != "SMS inbox") :
				#	logger.error('%s -- Cabeceras incorrectas recibidas desde %s' , threadName, clientIP)
				#	logger.error('ctype: %s - cuser: %s', ctype, cuser);
				#	self.send_error(400, 'Bad request')
				#else :
					
				# Fijamos un timeout de 2 segundos para que el dispositivo envie los datos
				self.rfile._sock.settimeout(2)
				post_body = self.rfile.read(clength)
				logger.info(post_body)

				# Enviar respuesta
				self.send_response( 200 )

        except:
            	self.send_error(400, 'Bad request')

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	def finish_request(self, request, client_address):
		request.settimeout(10)
		# "super" can not be used because BaseServer is not created from object
		HTTPServer.finish_request(self, request, client_address)
		HTTPServer.close_request(self, request)
    
def main():
	
    if (len(sys.argv) == 3):
        host = sys.argv[1]
        port = sys.argv[2]
        timeout = 30
 
        try:
            def handler(*args):
                MyHandler(*args)  
            server = ThreadedHTTPServer((host, int(port)), MyHandler)
            server.serve_forever()
        except KeyboardInterrupt:
            server.socket.close()
        except socket.timeout:
			logger.info('Timeout en la conexion')
			
 
    else: 
        print "usage: python ifall-webserver.py <host> <port>"
        sys.exit()
 
if __name__ == '__main__':
    main()
    	
