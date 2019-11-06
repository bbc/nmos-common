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

from nmoscommon import nmoscommonconfig
try:
    from pyipputils import ipphostname
    ippUtilsAvailable = True
except ImportError:
    ippUtilsAvailable = False
    ipphostname = None  # used to make test patching work


class InterfaceController():

    def __init__(self, logger):
        self.logger = logger

    def get_default_interfaces(self):
        """Returns a list of interface IPs"""
        interfaces = self._get_default_interface_from_file()
        if interfaces == []:
            interfaces = self._get_default_interface_from_routing_rules()
        if interfaces == []:
            interfaces = self._get_default_interface_from_gateway()
        if interfaces == []:
            interfaces = self._get_all_interfaces()
        if interfaces == []:
            msg = "Could not find any interfaces"
            self.logger.writeError(msg)
        return interfaces

    def _get_all_interfaces(self):
        interfaces = []
        for interface in netifaces.interfaces():
            if (interface is not None) & (str(interface)[0:2] != 'lo'):
                try:
                    ipv4Addr = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
                    if str(ipv4Addr)[0:4] != "127.":
                        interfaces.append(ipv4Addr)
                except (KeyError, IndexError):
                    pass
        if interfaces != []:
            self.logger.writeDebug("Using all available IPv4 network interfaces:"
                                   "{}".format(interfaces))
        return interfaces

    def _get_default_interface_from_routing_rules(self):
        if ippUtilsAvailable:
            interfaces = [ipphostname.getLocalIP()]
            self.logger.writeDebug("Choosing interface using routing rules:"
                                   "{}".format(interfaces[0]))
            return interfaces
        else:
            self.logger.writeDebug("Could not find ipp-utils, will try using default gateway interface")
            return []

    def _get_default_interface_from_gateway(self):
        defaultGateways = netifaces.gateways()
        try:
            defaultInterfaceName = defaultGateways['default'][netifaces.AF_INET][1]
            defaultInterfaceDetails = netifaces.ifaddresses(defaultInterfaceName)
            defaultInterfaceIp = defaultInterfaceDetails[netifaces.AF_INET][0]['addr']
        except KeyError:
            return []
        self.logger.writeDebug("Choosing interface using the default gateway:"
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
            self.logger.writeDebug("Choosing interface from /etc/nmoscommon/config.json "
                                   "file: {}".format(interfaces))
        except KeyError:
            self.logger.writeDebug("No interface config file - will try and use routing rules")

        return interfaces
