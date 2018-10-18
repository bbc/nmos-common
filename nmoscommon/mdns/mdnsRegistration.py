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

from zeroconf import ServiceInfo
from socket import inet_aton


class MDNSRegistration(object):

    def __init__(self, interfaces, name, regtype, port, txtRecord=None):
        if not txtRecord:
            txtRecord = {}
        self.name = name.replace(".", "-")
        self.regtype = regtype
        self.port = port
        self.txtRecord = txtRecord
        self.interfaces = interfaces
        self.info = {}

    def register(self):
        nameList = self._makeNamesUnique()
        regtype = self.regtype + ".local."
        for interface in self.interfaces:
            name = nameList[interface.ip] + "." + self.regtype + ".local."
            self.info[interface.ip] = ServiceInfo(
                type_=regtype,
                name=name,
                port=self.port,
                properties=self.txtRecord,
                address=inet_aton(interface.ip)
            )
            interface.registerService(self.info[interface.ip])

    def update(self, name=None, regtype=None, port=None, txtRecord=None):
        if name is not None:
            self.name = name
        if regtype is not None:
            self.regtype = regtype
        if port is not None:
            self.port = port
        if self.txtRecord is not None:
            self.txtRecord = txtRecord
        self.unRegister()
        self.register()

    def _makeNamesUnique(self):
        if len(self.interfaces) == 1:
            return {self.interfaces[0].ip: self.name}
        else:
            nameList = {}
            for interface in self.interfaces:
                # Zeroconf cannot deal with "." in names, so have to replace with dashes
                noDotIp = interface.ip.replace(".", "-")
                nameList[interface.ip] = self.name + "_{}".format(noDotIp)
            return nameList

    def unRegister(self):
        for interface in self.interfaces:
            interface.unregisterService(self.info[interface.ip])
