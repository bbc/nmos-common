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

from socket import inet_ntoa
from ..logger import Logger


class DNSListener(object):

    def __init__(self, callbackMethod, registerOnly):
        self.logger = Logger("zeroconf mDNS")
        self.callback = callbackMethod
        self.registerOnly = registerOnly
        self.records = {}
        self.nameMap = {}

    def add_service(self, zeroconf, type, name):
        action = "add"
        info = zeroconf.get_service_info(type, name)
        try:
            self.records[type][name] = info
        except KeyError:
            self.records[type] = {}
            self.records[type][name] = info
        self._respondToClient(name, action, info)

    def remove_service(self, zeroconf, type, name):
        info = self.records[type].pop(name)
        if not self.registerOnly:
            action = "remove"
            self._respondToClient(name, action, info)

    def _respondToClient(self, name, action, info):
        callbackData = self._buildClientCallback(action, info)
        self.logger.writeDebug("mDNS Service {}: {}".format(action, callbackData))
        self.callback(callbackData)

    def _buildClientCallback(self, action, info):
        return {
            "action": action,
            "ip": inet_ntoa(info.address),
            "type": info.type,
            "name": info.name,
            "port": info.port
        }
