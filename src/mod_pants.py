#!/usr/bin/python3
import cherrypy
import mapnik
import math
import os
import printer
import setup
import tile
import time
import upload 


class Pants(object):
    def __init__(self, docs_root):
        self.pants_html = docs_root + '/pants.html'
    def index(self):
        with open(self.pants_html, 'rb') as f:
            return f.read()
    index.exposed = True

if __name__ == '__main__':
    fcgi_run = True if not os.environ.get('PANTS_FCGI') is None else False
    if fcgi_run:
       cherrypy.config.update({'engine.autoreload_on': False})
       cherrypy.server.unsubscribe()
       cherrypy.engine.autoreload.unsubscribe()
    
    root = os.environ.get('PANTS_ROOT')
    assert not root is None, 'root needs to be set as env(PANTS_ROOT)'
    configs = os.environ.get('PANTS_CONFIG_DIR')
    assert not configs is None, 'configs directory needs to be set as env(PANTS_CONFIG_DIR)'

    htdocs = os.environ.get('PANTS_HTDOCS')
    assert not htdocs is None, 'need location of html files needs to be set as env(PANTS_HTDOCS)'
    tmp = os.environ.get('PANTS_TILE_STYLE')
    assert not tmp is None, 'Please specify an XML filename for the mapstyle in the configs directory as env(PANTS_TILE_STYLE)'

    tile.Tile.map_tile_style = configs + '/' + tmp

    cherrypy.tree.mount(Pants(htdocs), root, {'/': {'tools.trailing_slash.on': False} })
    cherrypy.tree.mount(tile.Tile(), root + '/tile', {'/': {'tools.trailing_slash.on': False} })
    cherrypy.tree.mount(setup.Setup(), root + '/setup', {'/': {'tools.trailing_slash.on': True} })
    cherrypy.tree.mount(upload.Upload(), root + '/upload', {'/': {'tools.trailing_slash.on': True} })
#    cherrypy.tree.mount(printer.Printer(), root + '/printer', {'/': {'tools.trailing_slash.on': True} })

    if fcgi_run:
        f = cherrypy.process.servers.FlupFCGIServer(application=cherrypy.tree)
        s = cherrypy.process.servers.ServerAdapter(cherrypy.engine, httpserver=f)
        s.subscribe()

    cherrypy.engine.start()
    cherrypy.engine.block()
