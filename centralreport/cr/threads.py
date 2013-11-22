# -*- coding: utf-8 -*-

"""
    CentralReport - Threads module
        Contains threads used by CentralReport to perform periodic actions

    https://github.com/CentralReport
"""

import datetime
import threading
import time

from cr import collectors
from cr import log
import cr.host
from cr.utils.text import convert_text_to_bool
from cr.tools import Config


class Checks(threading.Thread):
    """
        Thread performing periodically checks.
    """

    # Last checks (with new entities classes)
    last_check_cpu = None
    last_check_date = None
    last_check_disk = None
    last_check_loadAverage = None
    last_check_memory = None

    performChecks = True  # True = perform checks...
    tickCount = 60  # Initial Count (Perform a check when starting)

    def __init__(self):
        threading.Thread.__init__(self)
        log.log_debug('ThreadChecks is starting...')  # Standard output


        if cr.host.get_current_host().os == cr.host.OS_MAC:
            self.MyCollector = collectors.MacCollector()
        elif cr.host.get_current_host().family == cr.host.FAMILY_LINUX:
            self.MyCollector = collectors.DebianCollector()
        else:
            raise TypeError

        # Perform a check every xx ticks (1 tick = 1 second)

        try:
            self.tickPerformCheck = int(Config.get_config_value('Checks', 'interval'))
        except:
            self.tickPerformCheck = 60

        log.log_debug('Interval between two checks: %s seconds' % self.tickPerformCheck)

        self.start()

    def run(self):
        """
            Executes checks.
        """

        while Checks.performChecks:
            if self.tickPerformCheck <= self.tickCount:
                log.log_debug('---- New check -----')

                # Checking CPU
                if convert_text_to_bool(Config.get_config_value('Checks', 'enable_cpu_check')):
                    log.log_debug('Doing a CPU check...')
                    Checks.last_check_cpu = self.MyCollector.get_cpu()

                # Checking memory
                if convert_text_to_bool(Config.get_config_value('Checks', 'enable_memory_check')):
                    log.log_debug('Doing a memory check...')
                    Checks.last_check_memory = self.MyCollector.get_memory()

                # Checking Load Average
                if convert_text_to_bool(Config.get_config_value('Checks', 'enable_load_check')):
                    log.log_debug('Doing a load average check...')
                    Checks.last_check_loadAverage = self.MyCollector.get_loadaverage()

                # Checking disks information
                if convert_text_to_bool(Config.get_config_value('Checks', 'enable_disks_check')):
                    log.log_debug('Doing a disk check...')
                    Checks.last_check_disk = self.MyCollector.get_disks()

                Checks.last_check_date = datetime.datetime.now()  # Update the last check date

                log.log_debug('All checks are done')
                log.log_debug('Next checks in %s seconds...' % self.tickPerformCheck)

                self.tickCount = 0

            self.tickCount += 1
            time.sleep(1)