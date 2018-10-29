#!/usr/bin/env python

# Copyright 2017 British Broadcasting Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from nmoscommon.mdns.dnsListener import DNSListener
from nmoscommon.mdns.dnsService import DNSService
from nmoscommon.mdns import dnsUtils
from nmoscommon.mdns.mdnsExceptions import DNSRecordNotFound
from threading import Timer


"""This class uses the DNSUtils class to check that the current domain
has the PTR record for DNS-SD, and then finds all the available services
and creates instances of dnsService to watch them. It then checks back to
see if there are new services at least twice in the duration of the shortest
TTL of any found service, or no less than once an hour, whichever is shorter"""


class DNSServiceController(object):

    def __init__(self, type, callback, logger, registerOnly):
        self.logger = logger
        self.type = type
        self.services = {}
        self.listener = DNSListener(callback, registerOnly)

    def start(self):
        services = self._getDNSServices()
        self._populateServices(services)
        self._scheduleCallback()

    def _scheduleCallback(self):
        interval = self._findServiceRefreshInterval()
        Timer(interval, self._checkForServiceUpdatesCallback)

    def _findServiceRefreshInterval(self):
        accumulator = 3600  # 3600 seconds = 1 hour
        for service in self.services.values():
            target = service.ttl/2
            if target < accumulator:
                accumulator = target
        return accumulator

    def _getDNSServices(self):
        if not dnsUtils.checkDNSSDActive():
            self.logger.writeError("DNS-SD pointer record not found on current domain")
            return
        try:
            return dnsUtils.discoverService(self.type)
        except DNSRecordNotFound:
            return []

    def _populateServices(self, pointerRecords):
        for record in pointerRecords:
            service = DNSService(
                record,
                self.type,
                self.listener,
                self._removeServiceCallback,
                self.logger
            )
            self.services[service.type] = service
            service.start()

    def _removeServiceCallback(self, serviceToRemove):
        serviceToRemove.close()
        self.services.pop(serviceToRemove.type)

    def _checkForServiceUpdatesCallback(self):
        serviceRecords = self._getDNSServices()
        for record in serviceRecords:
            service = DNSService(record)
            if service.type not in self.services:
                self.services[service.type] = service
                service.start()

    def close(self):
        for _, service in self.services.items():
            service.close()
