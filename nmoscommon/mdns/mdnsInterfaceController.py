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

from .mdnsInterface import MDNSInterface
from .mdnsExceptions import NoNetworkInterfacesFoundException
from ..interfaceController import InterfaceController


class MDNSInterfaceController(object):

    def __init__(self, logger):
        self.logger = logger
        self.interfaces = {}
        self.defaultInterfaces = []
        self._set_default_interfaces()

    def addInterface(self, ip):
        if ip not in self.interfaces.keys():
            self.interfaces[ip] = MDNSInterface(ip)
        return self.interfaces[ip]

    def getInterfaces(self, interfaceIps):
        if interfaceIps == []:
            return self.defaultInterfaces
        else:
            interfaceList = []
            for ip in interfaceIps:
                interfaceList.append(self.addInterface(ip))
                self.logger.writeDebug("Switching to using mDNS interface provided:{}".format(ip))
            return interfaceList

    def close(self):
        for key, interface in self.interfaces.items():
            interface.close()

    def _set_default_interfaces(self):
        ifaceController = InterfaceController(self.logger)
        interfaces = ifaceController.get_default_interfaces()

        if interfaces == []:
            msg = "Could not find any interfaces for mDNS use"
            self.logger.writeError(msg)
            raise NoNetworkInterfacesFoundException(msg)
        for interface in interfaces:
            self.defaultInterfaces.append(self.addInterface(interface))
