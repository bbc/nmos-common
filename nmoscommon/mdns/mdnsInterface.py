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

import socket
from zeroconf_monkey import Zeroconf
from nmoscommon.logger import Logger
from .mdnsExceptions import InterfaceNotFoundException


class MDNSInterface(object):

    def __init__(self, interfaceIp):
        self.logger = Logger('MDNSInterface')
        self.ip = interfaceIp
        self._establish_interface()

    def _establish_interface(self):
        try:
            self.zeroconf = Zeroconf([self.ip])
        except socket.error:
            msg = "Could not find interface with IP {}".format(self.ip)
            self.logger.writeError(msg)
            raise InterfaceNotFoundException(msg)

    def registerService(self, info):
        self.zeroconf.register_service(info)

    def unregisterService(self, info):
        self.zeroconf.unregister_service(info)

    def close(self):
        self.zeroconf.close()
