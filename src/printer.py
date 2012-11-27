#!/usr/bin/python3
import io
import cairo
import csv
import datetime
import mapnik
import locale 
import os
import subprocess
import sys
import zipfile
from operator import attrgetter
import xml.etree.ElementTree as ET

debug_log = ''
external_logger = None
configs_dir = None

max_address_rows = 30
num_address_cols = 3

layout_row = '''                            <fo:table-row border-width="0" margin="0 0 0 0" width="100%%">
%s
                            </fo:table-row>
'''

layout_fo_number = '''                              <fo:table-cell width="9mm">
                                <fo:block border-width="0" margin="0 0 0 0" border-bottom="0.5pt" margin-right="2mm" white-space="pre" text-align="right">%s</fo:block>
                              </fo:table-cell>
                              <fo:table-cell width="37mm">
                                <fo:block border-width="0" margin="0 0 0 0" border-bottom="0.5pt" white-space="pre" text-align="left">%s</fo:block>
                              </fo:table-cell>
'''
layout_fo_street = '''                              <fo:table-cell width="46mm" border-bottom="0.5pt" border-bottom-style="solid" vertical-align="bottom" font-weight="bold" text-align="left"><fo:block  white-space="pre" text-align="left">%s</fo:block></fo:table-cell>
                              <fo:table-cell width="0mm" border-bottom="0.5pt" border-bottom-style="solid"><fo:block/></fo:table-cell>
'''
maps_layout_fo_template= '''<?xml version="1.0" encoding="utf-8"?>
<fo:root xmlns:fo="http://www.w3.org/1999/XSL/Format"  margin-left="0mm" margin-right="0mm">
  <fo:layout-master-set>
    <fo:simple-page-master margin-left="10mm" margin-right="5mm" page-height="297mm" page-width="210mm" margin-bottom="0mm" margin-top="4mm" master-name="pants">
      <fo:region-body xmlns:css="http://www.w3.org/1998/CSS" xmlns:xh="http://www.w3.org/1999/xhtml" xmlns:sp="urn:be-re-css:specificity"/>
    </fo:simple-page-master>
  </fo:layout-master-set>
  <fo:page-sequence format="1" master-reference="pants">
    <fo:flow flow-name="xsl-region-body">
      <fo:block border-width="0" font-family="Helvetica">
        <fo:block border-width="0">
          <fo:block border-width="0" margin="0 0 0 0" padding="0 0 0 0 0 0 0 0">
            <fo:table border-width="0" margin="0 0 0 0" table-layout="fixed" width="100%%">
              <fo:table-body border-width="0" end-indent="0">
                <fo:table-row>
                  <fo:table-cell border-width="0" margin="0 0 0 0" height="4mm" width="70mm" font-size="9pt" text-align="left" vertical-align="top">
                    <fo:block white-space="pre" border-width="0" margin="0 0 0 0">%s</fo:block>
                  </fo:table-cell>
                  <fo:table-cell white-space="pre" height="7mm" width="30mm" font-size="16pt" font-weight="bold" text-align="right" vertical-align="bottom" number-rows-spanned="2">
                    <fo:block border-width="0" margin="0 0 0 0" white-space="pre">%s</fo:block>
                  </fo:table-cell>
                  <fo:table-cell white-space="pre" height="4mm" width="65mm" font-size="9pt" vertical-align="top" text-align="left">
                    <fo:block border-width="0" margin="0 0 0 0" white-space="pre" margin-left="5mm">%s</fo:block>
                  </fo:table-cell>
                  <fo:table-cell white-space="pre" height="7mm" width="30mm" font-size="16pt" font-weight="bold" text-align="right" vertical-align="bottom" number-rows-spanned="2">
                    <fo:block border-width="0" margin="0 0 0 0" white-space="pre">%s</fo:block>
                  </fo:table-cell>
                </fo:table-row>
                <fo:table-row>
                  <fo:table-cell white-space="pre" height="3mm" width="70mm" font-size="5.5pt" text-align="left">
                    <fo:block border-width="0">%s</fo:block>
                  </fo:table-cell>
                  <fo:table-cell border-width="0" margin="0 0 0 0" white-space="pre" height="3mm" width="65mm" font-size="5.5pt" text-align="left">
                    <fo:block border-width="0" margin="0 0 0 0" margin-left="5mm">%s</fo:block>
                  </fo:table-cell>
                </fo:table-row>
                <fo:table-row>
                  <fo:table-cell border-width="0" margin="0 0 0 0" height="140mm" width="100mm" text-align="left" vertical-align="top" number-columns-spanned="2">
                    <fo:block border-width="0" margin="0 0 0 0" padding="0 0 0 0 0 0 0 0">
                      <fo:block-container border-width="0" margin="0 0 0 0" padding="0 0 0 0 0 0 0 0" width="138mm" height="100mm" reference-orientation="%d" end-indent="0">
                          <fo:block border-width="0" margin="0 0 0 0">
                            <fo:external-graphic height="100%%" width="100%%" src="url(file:./%s.svg)"/>
                          </fo:block>
                      </fo:block-container> 
                    </fo:block>
                  </fo:table-cell>
                  <fo:table-cell border-width="0" margin="0 0 0 0" margin-left="5mm" margin-top="2mm" text-align="left" vertical-align="top" height="140mm" width="95mm" number-columns-spanned="2">
                    <fo:block-container border-width="0" margin="0 0 0 0" padding="0 0 0 0 0 0 0 0" width="138mm" height="95mm" reference-orientation="270" end-indent="0">
                      <fo:block font-size="7.0pt" border-width="0" margin="0 0 0 0">
                        <fo:table border-width="0" margin="0 0 0 0" table-layout="fixed" width="100%%">
                          <fo:table-body border-width="0" margin="0 0 0 0" end-indent="0">
                           <fo:table-row border-width="0" margin="0 0 0 0"> 
                              <fo:table-cell width="9mm" border-width="0" margin="0 0 0 0">
                                <fo:block border-width="0" margin="0 0 0 0" margin-right="2mm" text-align="right"></fo:block>
                              </fo:table-cell>
                              <fo:table-cell width="37mm" border-width="0" margin="0 0 0 0">
                                <fo:block border-width="0" margin="0 0 0 0" text-align="left"></fo:block>
                              </fo:table-cell>
                              <fo:table-cell width="9mm" border-width="0" margin="0 0 0 0">
                                <fo:block border-width="0" margin="0 0 0 0" margin-right="2mm" text-align="right"></fo:block>
                              </fo:table-cell>
                              <fo:table-cell width="37mm" border-width="0" margin="0 0 0 0">
                                <fo:block border-width="0" margin="0 0 0 0" font-size="0.5pt" text-align="left"></fo:block>
                              </fo:table-cell>
                              <fo:table-cell width="9mm" border-width="0" margin="0 0 0 0">
                                <fo:block border-width="0" margin="0 0 0 0" margin-right="2mm" text-align="right"></fo:block>
                              </fo:table-cell>
                              <fo:table-cell width="37mm" border-width="0" margin="0 0 0 0">
                                <fo:block border-width="0" margin="0 0 0 0" text-align="left"></fo:block>
                              </fo:table-cell>
                            </fo:table-row>
%s
                          </fo:table-body>
                        </fo:table>
                      </fo:block>
                    </fo:block-container>
                  </fo:table-cell>
                </fo:table-row>
              </fo:table-body>
            </fo:table>
          </fo:block>
        </fo:block>
      </fo:block>
    </fo:flow>
  </fo:page-sequence>
</fo:root>
'''

overlay_skel = '''<?xml version="1.0" encoding="utf-8"?>
<Map srs="+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over" background-color="rgba(0,0,0,0)" minimum-version="2.0.0">
    <Style name="boundaries">
        <Rule>
         <PolygonSymbolizer fill="rgba(174,209,160,255)" />
        </Rule>
    </Style>
<Layer name="overlay" srs="+proj=latlong +datum=WGS84">
 <StyleName>boundaries</StyleName>
 <Datasource>
  <Parameter name="type">osm</Parameter>
  <Parameter name="file">%s</Parameter>
 </Datasource>
</Layer>
</Map>
'''

named_skel = '''    <node id="%d" changeset="0" version="1"  timestamp="2012-10-10T21:40:19Z" visible="true" lon="%f" lat="%f"  >
        <tag k="name" v="%s" />
    </node>
'''

node_skel = '''    <node id="%d" changeset="0" version="1" timestamp="2012-10-10T21:40:19Z" visible="true"  lon="%f" lat="%f" />
'''

ref_skel =  '''        <nd ref="%d" />
'''
way_skel = '''    <way id="%d" changeset="0" version="1"  timestamp="2012-10-10T21:40:19Z" visible='true'>
%s        <tag k='way_area' v='100232' />
        <tag k='name' v='%s' />
    </way>
'''

osm_skel = '''<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6" generator="JOSM">
%s </osm>
'''

multi_polygon = '''<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6" generator="JOSM">
    %s
    <way id="-6" changeset="0" version="1" timestamp="2012-10-10T21:40:19Z" visible='true'>
        %s
    </way>
    <node id="-5" changeset="0" version="1" timestamp="2012-10-10T21:40:19Z" visible="true" lon="-180" lat="84"/>
    <node id="-4" changeset="0" version="1" timestamp="2012-10-10T21:40:19Z" visible="true" lon="180" lat="84"/>
    <node id="-3" changeset="0" version="1" timestamp="2012-10-10T21:40:19Z" visible="true" lon="180" lat="-84"/>
    <node id="-2" changeset="0" version="1" timestamp="2012-10-10T21:40:19Z" visible="true" lon="-180" lat="-84"/>
    <way id="-1" changeset="0" version="1" timestamp="2012-10-10T21:40:19Z" visible='true'>
       <nd ref="-2" />
       <nd ref="-3" />
       <nd ref="-4" />
       <nd ref="-5" />
       <nd ref="-2" />
    </way>
    <relation id="-1">
      <tag k="type" v="multipolygon" />
      <member type="way" ref="-1" role="outer" />
      <member type="way" ref="-6" role="inner" />
    </relation>
</osm>
''' 

def xml_escape(data):
    # must do ampersand first
    data = data.replace("&", "&amp;")
    data = data.replace("'", "&apos;")
    data = data.replace(">", "&gt;")
    data = data.replace("<", "&lt;")
    return data

class Coord:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
class BoxXandY:
    def __init__(self, minx, miny, maxx, maxy):
        self.min = Coord(minx, miny)    
        self.max = Coord(maxx, maxy)
        
    @classmethod
    def clone(cls, box):
        return cls(box.min.x, box.min.y, box.max.x, box.max.y)
    
    def expand_to_box(self, box):
        self.expand_to_point(box.min)
        self.expand_to_point(box.max)
            
    def expand_to_point(self, point):
        self.expand_to_x_y(point.x, point.y)
        
    def expand_to_x_y(self, x, y):
        if x < self.min.x:
            self.min.x = x
        if y < self.min.y:
            self.min.y = y
        if x > self.max.x:
            self.max.x = x
        if y > self.max.y:
            self.max.y = y
            
    def contains(self, point):            
        return self.contains_x_y(point.x, point.y)

    def contains_x_y(self, x, y):
        if x < self.min.x:
            return False 
        if y < self.min.y:
            return False 
        if x > self.max.x:
            return False 
        if y > self.max.y:
            return False 
        return True

    def width(self):
        return self.max.x - self.min.x

    def height(self):
        return self.max.y - self.min.y

    def center(self):
        return Coord((self.max.x + self.min.x) / 2.0,
                     (self.max.y + self.min.y) / 2.0)

class Territory:
    def __init__(self, name, locality, ring):
        self.name = name
        self.locality = locality
        self.ring = ring
        self.bbox = BoxXandY(ring[0].x, ring[0].y, ring[0].x, ring[0].y)
        for point in ring:
            self.bbox.expand_to_point(point)
        self.address_list = []

    def inside_ring(self, coord):
        if not self.bbox.contains(coord):
            return False
        nvert = len(self.ring)
        i = 0
        j = nvert - 1
        inside = False
        while i < nvert:
            if ( ((self.ring[i].y > coord.y) != (self.ring[j].y > coord.y)) and
                (coord.x < ((self.ring[j].x-self.ring[i].x) * (coord.y - self.ring[i].y) 
                / (self.ring[j].y - self.ring[i].y) + self.ring[i].x) )):
                inside = not inside
            j = i
            i = i + 1         
        return inside
        
    def assign_addresses(self, address_list):
        for i in address_list:
            if self.inside_ring(i.coord):
                self.address_list.append(i)
                    
class Address:
    
    def __init__(self, coord, name, street, number, postcode = None, city = None, country = None):
        if not street or not coord  or not (name or number):
            raise Exception('Must have coordinates and street name and either a number or house name')
        self.coord = coord        
        self.street = street        
        self.name = name if name else ''
        self.number = number if number else ''
        self.postcode = postcode if postcode else ''
        self.city = city if city else ''
        self.country = country if country else ''


    @classmethod
    def from_string(cls, name, street, number, longitude, latitude):
        coord = None
        if len(longitude) != 0 and len(latitude) != 0:
            coord = Coord(float(longitude), float(latitude))
        return cls(coord, name, street, number)            

def parse(filename):
    global_address_list = []
    territory_list = []

    tree = ET.parse(filename)
    coords = {}

    for node in tree.getroot().findall('node'):
        idx = node.get('id')
        coord = Coord(float(node.get('lon')), float(node.get('lat')))
        coords[idx] = coord
        addr_house_no = None
        addr_street = None
        addr_house_name = None
        addr_postcode = None
        addr_city = None
        addr_country = None
        for tag in node.findall('tag'):
            if tag.get('k') == 'addr:city':
                addr_city = tag.get('v')
            if tag.get('k') == 'addr:country':
                addr_country = tag.get('v')
            if tag.get('k') == 'addr:housename':
                addr_house_name = tag.get('v')
            if tag.get('k') == 'addr:housenumber':
                addr_house_no = tag.get('v')
            if tag.get('k') == 'addr:postcode':
                addr_postcode = tag.get('v')
            if tag.get('k') == 'addr:street':
                addr_street = tag.get('v')

        if addr_street and (addr_house_no or addr_house_name):
            global_address_list.append(Address(coord,
                                               addr_house_name,
                                               addr_street,
                                               addr_house_no,
                                               addr_postcode,
                                               addr_city,
                                               addr_country))
    if len(coords) == 0:
        raise Exception('Need some kind of address boundaries.')

    for way in tree.getroot().findall('way'):
        name = None
        locality = None
        for tag in way.findall('tag'):
            if tag.get('k') == 'name':
                name = tag.get('v')
            if tag.get('k') == 'locality':
                locality = tag.get('v')
        if name is not None:
            ring = []
            for nd in way.findall('nd'):
                idx = nd.get('ref')
                ring.append(coords[idx])
            territory_list.append(Territory(name, locality, ring))
    
    for i in territory_list:
        i.assign_addresses(global_address_list)
    
        
    return global_address_list, sorted(territory_list, key=attrgetter('name'))

def parse_cvs_addresses(csv_filename):
    address_list = []
    with open(csv_filename, 'rb') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            address_list.append(Address.from_string(row[0], row[1], row[2], row[3], row[4]))
    return address_list

def extract_address(filename):
    updated = False
    errors = False
    return errors, updated

def update_csv_list(address_list, csv_filename):
    with open(csv_filename, 'wb') as f:
        w = csv.writer(f, delimiter=',')
        for addr in address_list:
            w.writerow([addr.name.encode('utf-8'), addr.street.encode('utf-8'),
                     addr.number.encode('utf-8'), '%E' % addr.coord.x, '%E' % addr.coord.y])
    f.close

def write_address_list(address_list, csv_filename):
    with open(csv_filename, 'wt', encoding='utf8') as f:
        w = csv.writer(f, delimiter=',')
        for addr in address_list:
            w.writerow([addr.name, addr.street, addr.number, 
            str(addr.coord.x), str(addr.coord.y)])
    f.close

def is_address_in_territory(addr, territory_list):
    for i in territory_list:
        if addr in i.address_list:
            return True
    return False

def write_unallocated(address_list, territory_list, unallocated_filename):
    unallocated_list = []
    for addr in address_list:
        if not is_address_in_territory(addr, territory_list):
            unallocated_list.append(addr)
            
    with open(unallocated_filename, 'wt', encoding='utf8') as f:
        w = csv.writer(f, delimiter=',')
        for addr in unallocated_list:
            w.writerow([addr.name, addr.street, addr.number,
                       str(addr.coord.x), str(addr.coord.y)])
    f.close

def generate_pdf(territory, version, is_landscape):
    curr_st = ''
    addr = sorted(territory.address_list, key=attrgetter('street'))
    rows = []
    blank_entry = layout_fo_number % (' ', ' ')
    for i in addr:
        if curr_st != i.street: 
            curr_st = i.street
            if (len(rows) % max_address_rows) == (max_address_rows - 1):
                rows.append(blank_entry)
            rows.append(layout_fo_street % xml_escape(curr_st))
        rows.append(layout_fo_number % (xml_escape(i.number), xml_escape(i.name)))

    if len(rows) >= max_address_rows * num_address_cols:
        raise Exception('Too many addresses to fit')
        
    tmp = ''
    for i in range(max_address_rows):
        cells = ''
        for j in range(num_address_cols):
            idx = (j * max_address_rows) + i
            if idx < len(rows):
                cells += rows[idx]
            else:
                cells += blank_entry
        tmp += layout_row % cells
        #
    tmp = maps_layout_fo_template % (xml_escape(territory.locality), xml_escape(territory.name),
                                     xml_escape(territory.locality), xml_escape(territory.name),
                                     xml_escape(version), xml_escape(version), 270 if is_landscape else 0,
                                     territory.name, tmp)
    fo_name = territory.name + '.fo'
    f = open(fo_name, 'wt', encoding='utf8')
    f.write(tmp)
    f.close()
    r = subprocess.call(['fop', fo_name, territory.name + '.pdf'])
    f.close()
    if r != 0:
        raise Exception('Could not generate pdf for %s' % territory.name)
    os.remove(fo_name)
    os.remove(territory.name + '.svg')

def create_maps_config(fname, tname):
    fin = open(configs_dir + fname, 'r')
    fout = open(tname + '.xml', 'w')
    fout.write(fin.read().replace('@XX_PANTS_REPACE_WITH_NAME@', tname))
    fout.close()
    fin.close()

def copy_to_work(src_dir, fname):
    fin = open(src_dir + '/' + fname, 'r')
    fout = open(fname, 'w')
    fout.write(fin.read())
    fout.close()
    fin.close()
    
def copy_from_config_to_work(fname):
    fin = open(configs_dir + fname, 'r')
    fout = open(fname, 'w')
    fout.write(fin.read())
    fout.close()
    fin.close()

def get_mercator_bbox(bbox):
    bb = mapnik.Box2d(bbox.min.x, bbox.min.y, bbox.max.x, bbox.max.y)
    merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')
    longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
    return mapnik.ProjTransform(longlat, merc).forward(bb)

def generate_master_map(map_bbox, territory_list, project_name, version):
    
    counter = -10000000
    nodes = ''
    ways_dict = {}
    for i in territory_list:
        start = counter
        way_ref = ''
        for j in i.ring:
            nodes += node_skel % (counter,  j.x, j.y)
            way_ref += ref_skel % counter
            counter = counter + 1
        way_ref += ref_skel % start
        ways_dict[i.name] = way_ref

    ways = ''
    for i in territory_list:
        ways += way_skel % (counter, ways_dict[i.name], i.name)
        counter = counter + 1

    tmp = osm_skel % (nodes + ways)
    f = open('xx_generated_all_boundary.osm', 'wt', encoding='utf8')
    f.write(tmp)
    f.close()   
             
    nodes = ''             
    for i in territory_list:
        center = i.bbox.center()
        nodes += named_skel % (counter, center.x, center.y, i.name)
        counter = counter + 1
                     
    tmp = osm_skel % nodes
    f = open('xx_generated_all_labels.osm', 'wt', encoding='utf8')
    f.write(tmp)
    f.close()                     
    
    # Why does the world use x being width first?
    page_height, page_width = mapnik.printing.pagesizes['a0']
    bb =  get_mercator_bbox(map_bbox)
    is_landscape = (bb.maxy - bb.miny) < (bb.maxx - bb.minx)
    
    if is_landscape and page_height > page_width:
        page_height, page_width = page_width, page_height
    elif not is_landscape and page_height < page_width:
        page_height, page_width = page_width, page_height
        
    top_margin_height = 0.005
    top_title_height = 0.035
    logger('Generating master map pdf %fm x %fm' % (page_width, page_height - top_title_height))
    map_height_pt = (page_height - top_title_height) / mapnik.printing.pt_size
    map_width_pt = page_width / mapnik.printing.pt_size
    logger('Generating master map pdf %fpts x %fpts' % (map_width_pt, map_height_pt))
    copy_from_config_to_work('master.xml')    
    m = mapnik.Map(int(map_width_pt), int(map_height_pt))
    mapnik.load_map(m, 'master.xml')    
    m.zoom_to_box(bb)    
    surface = cairo.PDFSurface(project_name + '.pdf', m.width, 
                               m.height + top_title_height / mapnik.printing.pt_size )
    ctx = cairo.Context(surface)
    ctx.select_font_face("Helvetica", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(72)
    
    text_width = ctx.text_extents(project_name)[2]
    ctx.translate((page_width / mapnik.printing.pt_size - text_width) / 2.0, 
                  (top_title_height - top_margin_height) / mapnik.printing.pt_size)

    ctx.show_text(project_name)
    ctx.set_font_size(6.5)
    ctx.show_text(version)
    
    ctx = cairo.Context(surface)
    ctx.translate(0.0, top_title_height / mapnik.printing.pt_size)
    mapnik.render(m, ctx)        
    
    surface.finish()
    os.remove('xx_generated_all_labels.osm')
    os.remove('xx_generated_all_boundary.osm')
    os.remove('master.xml')
    return counter 

def generate_map(territory, counter, version):
    bb =  get_mercator_bbox(territory.bbox)
    is_landscape = (bb.maxy - bb.miny) < (bb.maxx - bb.minx)
    logger('BBox for %s is %d x %d and is %s' % (territory.name, bb.maxx - bb.minx, 
                                                 bb.maxy - bb.miny,
                                                 'landscape' if is_landscape else 'portrait')) 
    nodes = ''
    for i in territory.address_list:
        nodes += named_skel % (counter, i.coord.x, i.coord.y, i.number if len(i.number) else i.name)
        counter = counter + 1
        
    tmp = osm_skel % nodes
    f = open('xx_tmp_labels_' + territory.name + '.osm', 'wt', encoding='utf8')
    f.write(tmp)
    f.close()
    start = counter
    nodes = '' 
    way_ref = ''
    for i in territory.ring:
        nodes += node_skel % (counter,  i.x, i.y)
        way_ref += ref_skel % counter
        counter = counter + 1
    way_ref += ref_skel % start            
    
    tmp =  multi_polygon % (nodes, way_ref)
    f = open('xx_tmp_polygon_' + territory.name + '.osm', 'wt', encoding='utf8')
    f.write(tmp)
    f.close()

    page_width = 0.0999
    page_height = 0.138

    if is_landscape and page_height > page_width:
        page_height, page_width = page_width, page_height
    elif not is_landscape and page_height < page_width:
        page_height, page_width = page_width, page_height

    map_height_pt = page_height / mapnik.printing.pt_size
    map_width_pt = page_width / mapnik.printing.pt_size
    
    image_name = territory.name + '.svg'
    logger('Generating %s %fpts x %fpts' % (image_name, map_width_pt, map_height_pt))
    create_maps_config('maps.xml', territory.name)
    m = mapnik.Map(int(map_width_pt), int(map_height_pt))
    mapnik.load_map(m, territory.name + '.xml')    
    m.zoom_to_box(bb)
    surface = cairo.SVGSurface(image_name, m.width, m.height)    
    mapnik.render(m, surface)
    surface.finish()
    os.remove('xx_tmp_polygon_' + territory.name + '.osm')
    os.remove('xx_tmp_labels_' + territory.name + '.osm')
    os.remove(territory.name + '.xml')
    generate_pdf(territory, version, is_landscape)    
    return counter

def main(log_method, configs_directory, dest_directory, filename):
    global external_logger
    external_logger = log_method
    global configs_dir
    configs_dir = configs_directory + '/'
    if not filename.endswith('.xml'):
        raise Exception('Need an xml file extension. Filename %s invalid.' % filename)
    
    if filename.find('/') != -1:
        raise Exception('Need file relative to DestDir. Filename %s should not contain any "/".' 
                          % filename)
    project_name = filename[:-4]
    version = project_name + '-' +  datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    logger('Started: ' + version + ' in ' + dest_directory + ' for ' + filename)    
    output_dir = dest_directory + '/' + version
    try:
        os.mkdir(output_dir)
        os.chdir(output_dir)
        address_list, territory_list = parse(dest_directory + '/' + filename)
        num_address_allocated = 0
        for i in territory_list:
            logger('%s\t%3d' % (i.name,  len(i.address_list)))
            write_address_list(i.address_list, i.name + '.csv')
            num_address_allocated += len(i.address_list)
            
        logger('Read: %d addreses, %d addresses were allocated to %d territories.' 
               % (len(address_list), num_address_allocated, len(territory_list)))
        if num_address_allocated != len(address_list):
            logger('********************** WARNING *******************************')
            logger('Check the boundaries and/or recent data. Wrote to reject list.')
            write_unallocated(address_list, territory_list, 'unassigned_addresses.csv')
        
        if len(territory_list) == 0:
            logger('*********************** ERROR *******************************')            
            logger('Zero territories, means nothing to print. Bye')
            raise Exception('Nothing to assign to.')
        
        bbox = BoxXandY.clone(territory_list[0].bbox)
        for i in territory_list:
            bbox.expand_to_box(i.bbox)
            
        logger('********************** INFO *******************************')
        start_node = generate_master_map(bbox, territory_list, project_name, version)
        for i in territory_list:
            start_node = generate_map(i, start_node, version)

        zipfile_name = version + '.zip'
        logger('Creating zip file: ' + zipfile_name)
        copy_to_work(dest_directory, filename)
        z = zipfile.ZipFile(dest_directory + '/' + zipfile_name, 'w', zipfile.ZIP_DEFLATED)
        rootlen = len(dest_directory) + 1
        for base, dirs, files in os.walk(output_dir):
            for f in files:
                fn = os.path.join(base, f)
                z.write(fn, fn[rootlen:])
                logger('Added ' + fn)
        return zipfile_name
    finally:
        for base, dirs, files in os.walk(output_dir):
            for f in files:
                fn = os.path.join(base, f)
                os.remove(fn)
        os.rmdir(output_dir)

def stderr_logger(arg):
    sys.stderr.write(arg)
    sys.stderr.write('\n')
    sys.stderr.flush()
    
def logger(arg):
    if external_logger:
        external_logger(arg)
    global debug_log
    debug_log += arg + '\r\n' # for DOS users

if __name__ == '__main__':
    external_logger = stderr_logger
    if len(sys.argv) != 4:
        logger('Usage: ' + sys.argv[0] + ' Configsdirectory DestDirectory filename_in_DestDirectory')
        sys.exit(1)
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    try:
        output_filename = main(stderr_logger, sys.argv[1], sys.argv[2], sys.argv[3])
        logger(debug_log)        
        logger('Created: ' + output_filename)
    except Exception as e:
        logger('FAILED: %s' % str(e))
        raise
    
