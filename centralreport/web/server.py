# CentralReport - Indev version
# Project by Charles-Emmanuel CAMUS - Avril 2012

import os
import threading
import cherrypy
import datetime
import calendar
from jinja2 import Environment, FileSystemLoader
import cr.utils.text as crUtilsText
from cr.tools import Config
from cr.threads import Checks
import cr.utils.date as crUtilsDate

class WebServer(threading.Thread):
#class WebServer():

    current_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(os.path.join(current_dir,'tpl')))

    def __init__(self):
        """
            Manage the small webserver
        """
        threading.Thread.__init__(self)

        # Start home
        #cherrypy.tree.graft(WebHomePages(), '/')

        # Register events...
        cherrypy.engine.subscribe('graceful', self.stop)

        # Update the configuration...
        cherrypy.config.update({'server.socket_host': Config.getConfigValue('Webserver','interface'), 'server.socket_port': int(Config.getConfigValue('Webserver','port'))})
        cherrypy.config.update({'tools.staticdir.root': WebServer.current_dir})
        cherrypy.config.update({'log.screen': False})
        #        cherrypy.config.update({'engine.timeout_monitor.on' : False})

        # Serving static content
        confStaticContent = {
            '/statics': {
                'tools.staticdir.dir': 'statics', 'tools.staticdir.on': True
            },
            '/css': {
                'tools.staticdir.dir': 'css',
                'tools.staticdir.on': True
            },
            '/img': {
                'tools.staticdir.dir': 'img',
                'tools.staticdir.on': True
            },
            '/js': {
                'tools.staticdir.dir': 'js',
                'tools.staticdir.on': True
            },
            '/media': {
                'tools.staticdir.dir': 'media',
                'tools.staticdir.on': True
            }
        }

        # Using Pages class (see below)
        webApplication = cherrypy.tree.mount(Pages(self.env), '/', confStaticContent)

        # Disable screen log (standard out)
        # http://stackoverflow.com/questions/4056958/cherrypy-logging-how-do-i-configure-and-use-the-global-and-application-level-lo
        webApplication.log.screen = False
        webApplication.log.access_file = None

        self.start()

    def run(self):
        """
            Starting the web server
        """

        # Go go go!
        # cherrypy.engine.start() --> Consumes lot of CPU, updated with cherrypy.server.start()
        cherrypy.server.start()
        cherrypy.engine.block()



    def stop(self):
        """
            When CherryPy is stopping, we restart it.
        """
        cherrypy.engine.stop()


class Pages:

    def __init__(self, env_template):
        self.env = env_template

    @cherrypy.expose
    def index(self):
        tmpl = self.env.get_template('index.tpl')

        tmpl_vars = dict()

        tmpl_vars['hostname'] = Checks.hostEntity.hostname

        tmpl_vars['last_check'] = Checks.last_check_date.strftime("%Y-%m-%d %H:%M:%S")

        tmpl_vars['cpu_percent'] = 100 - int(Checks.last_check_cpu.idle)
        tmpl_vars['memory_percent'] = ((int(Checks.last_check_memory.total) - int(Checks.last_check_memory.free)) * 100) / int(Checks.last_check_memory.total)
        tmpl_vars['loadaverage'] = Checks.last_check_loadAverage.last1m

        tmpl_vars['loadaverage_percent'] = (float(Checks.last_check_loadAverage.last1m) * 100) / int(Checks.hostEntity.cpuCount)

        tmpl_vars['uptime'] = int(Checks.last_check_loadAverage.uptime)

        # WIP (miniche)
        #tmpl_vars['uptime'] = crUtilsText.secondsToFullTime(int(Checks.last_check_loadAverage.uptime))
        #print(crUtilsDate.datetimeToTimestamp(Checks.last_check_date))
        #print(int(Checks.last_check_loadAverage.uptime))

        tmpl_vars['start_date'] = datetime.datetime.fromtimestamp(crUtilsDate.datetimeToTimestamp(Checks.last_check_date) - int(Checks.last_check_loadAverage.uptime)).strftime("%Y-%m-%d %H:%M:%S")

        # Testing displaying disks stats
        allChecksDisk = []

        for disk in Checks.last_check_disk.checks:
            checkDisk = {}
            checkDisk['name'] = str.replace(disk.name, '/dev/', '')
            checkDisk['free'] = crUtilsText.numberSeparators(round(disk.free,2), ' ')
            checkDisk['percent'] = int(round(disk.used,0) * 100 / int(disk.size))

            allChecksDisk.append(checkDisk)

        tmpl_vars['disks'] = allChecksDisk

        return tmpl.render(tmpl_vars)


    @cherrypy.expose
    def dashboard(self):

        tmpl = self.env.get_template("dashboard_mac.tpl")
        tmpl_vars = dict()

        tmpl_vars['last_check'] = Checks.last_check_date.strftime("%Y-%m-%d %H:%M:%S")
        tmpl_vars['host'] = Checks.hostEntity
        tmpl_vars['cpu'] = Checks.last_check_cpu
        tmpl_vars['memory'] = Checks.last_check_memory
        tmpl_vars['loadaverage'] = Checks.last_check_loadAverage
        tmpl_vars['disks'] = Checks.last_check_disk

        # Host informations
        #            tmpl_vars['hostname'] = ThreadMac.dict_machine['hostname']
        #
        #
        #            # CPU informations
        #            last_check = ThreadMac.last_dict_cpu['date']
        #            tmpl_vars['kernel'] = ThreadMac.dict_machine['kernel']
        #            tmpl_vars['kernel_version'] = ThreadMac.dict_machine['kernel_v']
        #            tmpl_vars['mac_model'] = ThreadMac.dict_machine['model']
        #            tmpl_vars['ncpu'] = ThreadMac.dict_machine['ncpu']
        #
        #            tmpl_vars['cpu_date'] = ThreadMac.last_dict_cpu['date'].strftime("%Y-%m-%d %H:%M:%S")
        #            tmpl_vars['cpu_model'] = ThreadMac.dict_machine['modelcpu']
        #            tmpl_vars['cpu_idle'] = ThreadMac.last_dict_cpu['idle']
        #            tmpl_vars['cpu_system'] = ThreadMac.last_dict_cpu['system']
        #            tmpl_vars['cpu_user'] = ThreadMac.last_dict_cpu['user']
        #
        #            # Memory informations
        #            tmpl_vars['mem_date'] = ThreadMac.last_dict_memory['date'].strftime("%Y-%m-%d %H:%M:%S")
        #            tmpl_vars['mem_free'] = ThreadMac.last_dict_memory['mem_free']
        #            tmpl_vars['mem_active'] = ThreadMac.last_dict_memory['mem_active']
        #            tmpl_vars['mem_inactive'] = ThreadMac.last_dict_memory['mem_inactive']
        #            tmpl_vars['mem_resident'] = ThreadMac.last_dict_memory['mem_resident']
        #            tmpl_vars['mem_total'] = ThreadMac.last_dict_memory['mem_size']
        #            tmpl_vars['mem_swap'] = ThreadMac.last_dict_memory['mem_swap']
        #
        #            # Load average informations
        #            tmpl_vars['load_date'] = ThreadMac.last_dict_loadavg['date'].strftime("%Y-%m-%d %H:%M:%S")
        #            tmpl_vars['load_1m'] = ThreadMac.last_dict_loadavg['load1m']
        #            tmpl_vars['load_5m'] = ThreadMac.last_dict_loadavg['load5m']
        #            tmpl_vars['load_15m'] = ThreadMac.last_dict_loadavg['load15m']
        #
        #            tmpl_vars['disks'] = ThreadMac.last_list_disk
        #            tmpl_vars['disks_test'] = ThreadMac.last_list_disk

        return tmpl.render(tmpl_vars)

    def error_page_404(status, message, traceback, version):
        """
            Our 404 error.
        """

        return "Oups... Error %s - Well, I'm very sorry but this page doesn't really exist!" % status
    cherrypy.config.update({'error_page.404': error_page_404})


    @cherrypy.expose
    def test(self):

        return '<h1>This is a test</h1> ... and it works!'
