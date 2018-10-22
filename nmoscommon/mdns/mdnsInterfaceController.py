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
from nmoscommon import nmoscommonconfig
from nmoscommon.mdns.mdnsExceptions import NoNetworkInterfacesFoundException
try:
    from pyipputils import ipphostname
    ippUtilsAvailable = True
except ImportError:
    ippUtilsAvailable = False
    ipphostname = None  # used to make test patching work


class MDNSInterfaceController(object):

    def __init__(self, logger):
        self.logger = logger
        self.interfaces = {}
        self.defaultInterfaces = []
        self._get_default_interfaces()

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

    def _get_default_interfaces(self):
        interfaces = self._get_default_interface_from_file()
        if not interfaces:
            interfaces = self._get_default_interface_from_routing_rules()
        if not interfaces:
            interfaces = self._get_default_interface_from_gateway()
        if not interfaces:
            interfaces = self._get_all_interfaces()
        if not interfaces:
            msg = "Could not find any interfaces for mDNS use"
            self.logger.writeError(msg)
            raise NoNetworkInterfacesFoundException(msg)
        for interface in interfaces:
            self.defaultInterfaces.append(self.addInterface(interface))

    def _get_all_interfaces(self):
        toReturn = []
        for interface in netifaces.interfaces():
            interfaceDetails = netifaces.ifaddresses(interface)
            try:
                ipv4Addr = interfaceDetails[netifaces.AF_INET][0]['addr']
            except KeyError:
                pass
            toReturn.append(ipv4Addr)
        if toReturn == []:
            return False
        else:
            self.logger.writeDebug("Using all available IPv4 network interfaces for mDNS:"
                                   "{}".format(toReturn))
        return toReturn

    def _get_default_interface_from_routing_rules(self):
        if ippUtilsAvailable:
            interfaces = [ipphostname.getLocalIP()]
            self.logger.writeDebug("Choosing mDNS interface using routing rules:"
                                   "{}".format(interfaces[0]))
            return interfaces
        else:
            self.logger.writeDebug("Could not find ipp-utils, will try using default gateway interface")
            return False

    def _get_default_interface_from_gateway(self):
        defaultGateways = netifaces.gateways()
        try:
            defaultInterfaceName = defaultGateways[netifaces.AF_INET][0][1]
        except KeyError:
            return False
        defaultInterfaceDetails = netifaces.ifaddresses(defaultInterfaceName)
        defaultInterfaceIp = defaultInterfaceDetails[netifaces.AF_INET][0]['addr']
        self.logger.writeDebug("Choosing mDNS interface using the default gateway:"
                               " {}".format(defaultInterfaceIp))
        return [defaultInterfaceIp]

    def _get_default_interface_from_file(self):
        try:
            interfaces = []
            interfaceNames = nmoscommonconfig.config['interfaces']
            if interfaceNames == "*":
                return self._get_all_interfaces()
            for interfaceName in interfaceNames:
                interfaces.append(netifaces.ifaddresses(interfaceName)[netifaces.AF_INET][0]['addr'])
            self.logger.writeDebug("Choosing mDNS interface from /etc/nmoscommon/config.json "
                                   "file: {}".format(interfaces))
        except KeyError as e:
            self.logger.writeDebug("No interface config file - will try and use routing rules")
            return False
        else:
            return interfaces
