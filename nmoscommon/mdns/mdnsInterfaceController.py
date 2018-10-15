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

import netifaces
from .mdnsInterface import MDNSInterface


class MDNSInterfaceController(object):

    def __init__(self):
        self.interfaces = {}
        self.defaultInterface = self._findDefaultInterface()

    def _findDefaultInterface(self):
        defaultGateways = netifaces.gateways()
        defaultInterfaceName = defaultGateways[netifaces.AF_INET][0][1]
        defaultInterfaceDetails = netifaces.ifaddresses(defaultInterfaceName)
        defaultInterfaceIp = defaultInterfaceDetails[netifaces.AF_INET][0]['addr']
        return self.addInterface(defaultInterfaceIp)

    def addInterface(self, ip):
        if ip not in self.interfaces.keys():
            self.interfaces[ip] = MDNSInterface(ip)
        return self.interfaces[ip]

    def getInterfaces(self, interfaceIps):
        if interfaceIps == []:
            return [self.defaultInterface]
        else:
            interfaceList = []
            for ip in interfaceIps:
                interfaceList.append(self.addInterface(ip))
            return interfaceList

    def close(self):
        for key, interface in self.interfaces.items():
            interface.close()
