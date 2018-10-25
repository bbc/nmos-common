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


class DNSServiceController(object):

    def __init__(self, type, callback, logger, registerOnly):
        self.logger = logger
        self.type = type
        self.services = []
        self.listener = DNSListener(callback, registerOnly)

    def start(self):
        services = self._getDNSServices()
        self._populateServices(services)

    def _getDNSServices(self):
        if not dnsUtils.checkDNSSDActive():
            self.logger.writeError("DNS-SD pointer record not found on current domain")
            return
        return dnsUtils.getServiceTypes()

    def _populateServices(self, pointerRecords):
        for record in pointerRecords:
            service = DNSService(record, self.listener, self.logger)
            self.services.append(service)

    def close(self):
        for service in self.services:
            service.close()