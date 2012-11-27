#!/usr/bin/python3

import cherrypy
import mapnik
import math
import os
import time
import base64


class Tile(object):
    map_tile_style = None
    pad = 128
    tile_size = 256
    view_size = tile_size + 2 * pad
    max_zoom = 26
    world_size = 2 * 20037508.34 # in meters for 90013 GoogleProjection

    def render(self):
        map_size = float(self.tile_size * (1 << self.z))
        # y's are cartesian but tiles increase in screen coords, ie towards ground
        bb = mapnik.Envelope(
                (float(self.x * self.tile_size - self.pad) / map_size - 0.5)  * self.world_size,
                ((float(-self.y - 1) * self.tile_size - self.pad) / map_size + 0.5) * self.world_size,
                ((float(self.x + 1) * self.tile_size + self.pad) / map_size - 0.5)  * self.world_size,
                (float(-self.y * self.tile_size + self.pad) / map_size + 0.5)  * self.world_size)
        m = mapnik.Map(self.view_size, self.view_size)
        mapnik.load_map(m, self.map_tile_style)
        img = mapnik.Image(self.view_size, self.view_size)        
        m.zoom_to_box(bb)
        mapnik.render(m, img)
        tile_data = img.view(self.pad, self.pad, self.tile_size, self.tile_size).tostring(self.ext)
        return tile_data 
        
    def default(self, z, x, y):
        self.z = int(z)
        self.x = int(x)
        tmp, self.ext = y.split('.')
        self.y = int(tmp)
        cherrypy.response.headers['Content-Type'] = 'image/' + self.ext
        cherrypy.response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
        cherrypy.response.headers['Cache-Control'] = 'max-age=60'
        if (self.z < 0 or self.z > self.max_zoom or 
            self.x < 0 or self.x >= (1 << self.z) or 
            self.y < 0 or self.y >= (1 << self.z)):
            return base64.b64decode(b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAHUlEQVQ4y2P8//9/PQMFgImBQjBqwKgBowYMFgMAZawDnC46+EwAAAAASUVORK5CYII=')
        return self.render()
    default.exposed = True   
