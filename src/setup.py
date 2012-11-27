#!/usr/bin/python3
import cherrypy
import subprocess
import sys
import os
import select

pgdata_mount = '/pgdata'
pgdata_init_file = pgdata_mount + '/pginit'
osmdata_init_file = pgdata_mount + '/osminit'
osm_data_tmp_file = pgdata_mount + '/tmp.osm.pbf'
tmp_shell_file = '/tmp/pants.sh'

shutdown_sh = str(('''#!/bin/sh -e
XSU="xpants_su"
ROOT="0"
echo -n .
${XSU} ${ROOT} /usr/bin/systemctl stop postgresql || true
sleep 0.3
echo -n .
sync
echo -n .
nohup /bin/sh -c "sleep 2; ${XSU} ${ROOT} /usr/bin/systemctl poweroff" 2>&1 > /dev/null &
exit 0
'''))

osm_tmp_sh = str(('''#!/bin/sh -e
XSU="xpants_su"
ROOT="0"
TMP_FILE=''' +  osm_data_tmp_file + 
'''
${XSU} ${ROOT} /bin/touch ${TMP_FILE}
${XSU} ${ROOT} /bin/chmod 666 ${TMP_FILE}
'''))

osm2pgsq_sh = str(('''#!/bin/sh -e
XSU="xpants_su"
ROOT="0"
TMP_FILE=''' + osm_data_tmp_file +
'''
OSM_INIT_FILE=''' + osmdata_init_file +
'''
if [ "x${1}" = "xappend" ] ; then
    osm2pgsql --append --style /usr/share/osm2pgsql/default.style --slim --database gis --cache 1024M ${TMP_FILE}
    exec ${XSU} ${ROOT} /bin/rm -f ${TMP_FILE} 
else 
    osm2pgsql --create --style /usr/share/osm2pgsql/default.style --slim --database gis --cache 1024M ${TMP_FILE}
    ${XSU} ${ROOT} /bin/rm -f ${TMP_FILE} 
    exec ${XSU} ${ROOT} /bin/touch ${OSM_INIT_FILE}
fi
'''))

def post_action(action):
    return ('''<form action="%s" method="post"/><script>setTimeout(function() 
            {document.forms[0].submit();}, 1);</script>''' % action)

def stream_exec_utf8(args, return_path):
    cherrypy.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
    cherrypy.response.status = 200
    p = subprocess.Popen(args, shell=False,
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    flist = [p.stdout, p.stderr]
    def doStuff():
        yield '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
                <html>
                    <body style="background-color: #000000;color: #D0D0D0;font-size: 16px;font-family: monospace;">
                    <pre style="font-size:20px;font-weight:bold;">PANTS Doing stuff...</pre>
                    <pre style=="font-size:16px;">'''
        while not p.returncode:
            i, o, e = select.select(flist, [], flist)
            for x in i:
                buf = x.read(1)
                if not buf:
                    yield ('<br/>Finished<br/>%s</body></html>' % post_action(return_path))
                    return
                yield buf
        yield ('</pre><br/>Finished<br/>%s</body></html>' % post_action(return_path))
    return doStuff()

def upload_form(create):
    return '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
            <html>
            <body style="background-color:#000000;color:#D0D0D0;font-size:16px;font-family: Verdana, Geneva, sans-serif;">
            <pre style="font-size:20px;font-weight:bold;">PANTS Map Uploader</pre>
            Please download some map data for a [region].osm.pbf file from: 
            <a style="color: #C0C000" ref href="http://download.geofabrik.de/"> http://download.geofabrik.de/</a><br/>
            Try one of the redacted versions <a style="color: #C0C000" ref href="http://download.geofabrik.de/openstreetmap/">
            http://download.geofabrik.de/openstreetmap/</a> first.<br/> If the data is unsuitable, you
            might have better success with one of pre-redaction files 
            <a style="color: #C0C000" ref href="http://download.geofabrik.de/osm-before-redaction/">http://download.geofabrik.de/osm-before-redaction/</a>.<br>  
                <form action="%s" method="post" enctype="multipart/form-data">
                    Select a file: <input type="file" name="inFile" />
                    <input type="submit" />
                </form>
            </body></html>''' % ('create' if create else 'append')

def create_tmp_sh(script):
    with open(tmp_shell_file, 'w+', encoding='utf8') as f:
        f.write(script)
    
def upload_file(inFile, param):
    create_tmp_sh(osm_tmp_sh)
    p = subprocess.Popen(['/bin/sh', '-e', tmp_shell_file], shell=False,
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()
    with open(osm_data_tmp_file, 'wb+') as f:
        while True:
            buf = inFile.file.read(1048576)
            if not buf:
                break
            f.write(buf)
    return ('''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
                <html>
                    <body style="background-color: #000000;">
                        <form action="run_osm2pgsql" method="post">
                            <input type="hidden" name="param" value = "%s"/>
                        </form>
                        <script>
                            setTimeout(function() 
                            {document.forms[0].submit();}, 1);
                        </script>
                    </body>
                </html>''' % param)

def block_exec_code(args):
    p = subprocess.Popen(args, shell=False,
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()
    return p.returncode

def pg_running():
    return block_exec_code(['/usr/bin/systemctl', 'status', 'postgresql']) == 0

class Setup(object):
    def start(self):
        cherrypy.response.headers['Cache-Control'] = 'no-cache'
        if os.path.exists(osmdata_init_file) and pg_running():
            return('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
                   + '<html><body style="background-color: #000000;"><meta http-equiv="refresh" content="0;URL=../"></body></html>')
        elif os.path.exists(pgdata_init_file) and pg_running():
            return('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
                    + '<html><body style="background-color: #000000;">' + post_action('upload') + '</body></html>')
        else:
            return('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
                   + '<html><body style="background-color: #000000;">' + post_action('clean') + '</body></html>')
    start.exposed = True
 
    def upload(self):
        cherrypy.response.headers['Cache-Control'] = 'no-cache'
        return upload_form(True)
    upload._cp_config = {'response.stream': True, 'tools.allow.on': True, 'tools.allow.methods': ['GET', 'POST']}
    upload.exposed = True;
    
    def clean(self):
        cherrypy.response.headers['Location'] = 'start'
        cherrypy.response.headers['Cache-Control'] = 'no-cache'
        cherrypy.response.status = 303
        return stream_exec_utf8(['/usr/bin/pgfullclean.sh', pgdata_mount, pgdata_init_file], 'start')
    clean._cp_config = {'response.stream': True, 'tools.allow.on': True, 'tools.allow.methods': ['POST']}    
    clean.exposed = True

    def create(self, inFile):
        cherrypy.response.headers['Content-Type'] = 'text/html; charset=UTF-8'        
        return upload_file(inFile, 'create') 
    create._cp_config = {'response.stream': True, 'tools.allow.on': True, 'tools.allow.methods': ['POST']}
    create.exposed = True
    
    def append(self, inFile):
        cherrypy.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        return upload_file(inFile, 'append')
    append._cp_config = {'response.stream': True, 'tools.allow.on': True, 'tools.allow.methods': ['POST']}    
    append.exposed = True

    def run_osm2pgsql(self, param):
        cherrypy.response.headers['Location'] = 'start'
        cherrypy.response.headers['Cache-Control'] = 'no-cache'
        cherrypy.response.status = 303
        cherrypy.response.headers['Content-Type'] = 'text/html; charset=UTF-8'        
        create_tmp_sh(osm2pgsq_sh)
        return stream_exec_utf8(['/bin/sh', '-e', tmp_shell_file, param], 'start')
    run_osm2pgsql._cp_config = {'response.stream': True, 'tools.allow.on': True, 'tools.allow.methods': ['POST']}    
    run_osm2pgsql.exposed = True

    def shutdown(self):
        cherrypy.response.headers['Location'] = 'start'
        cherrypy.response.headers['Cache-Control'] = 'no-cache'
        cherrypy.response.status = 303
        create_tmp_sh(shutdown_sh)
        return stream_exec_utf8(['/bin/sh', '-e', tmp_shell_file], 'end')
    shutdown._cp_config = {'response.stream': True, 'tools.allow.on': True, 'tools.allow.methods': ['POST']}    
    shutdown.exposed = True
    
    def end(self):
        return('''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
                    <html>
                       <body style="background-color:#000000;color:#D0D0D0;font-size:16px;font-family: Verdana, Geneva, sans-serif;">
                        <pre style="font-size:20px;font-weight:bold;">PANTS Shutting down...</pre><br/>Shutdown<br/></body></html>''')

    end._cp_config = {'response.stream': True, 'tools.allow.on': True, 'tools.allow.methods': ['GET', 'POST']}
    end.exposed = True;