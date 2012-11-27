#!/usr/bin/python3
import cherrypy
import subprocess
import sys
import os
import select

uploads = {}
class Upload(object):
    def upload(self, uploadfile, filename):
        cherrypy.response.headers['Cache-Control'] = 'no-cache'
        uploads[filename] = uploadfile.file.read()
        return('''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
                    <html>%s</html>''' % (cherrypy.request.script_name + '/download/' + filename))
    upload._cp_config = {'tools.allow.on': True, 'tools.allow.methods': ['POST']}
    upload.exposed = True;

    def download(self, filename):
        cherrypy.response.headers['Cache-Control'] = 'no-cache'
        if filename.endswith('.xml'):
            cherrypy.response.headers['Content-Type'] = 'text/xml; charset=UTF-8'
        return uploads[filename]
    download._cp_config = {'tools.allow.on': True, 'tools.allow.methods': ['GET', 'POST']}
    download.exposed = True;
        