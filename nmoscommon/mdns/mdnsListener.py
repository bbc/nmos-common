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
from six.moves import queue
from threading import Thread


class MDNSListener(object):

    def __init__(self, callbackMethod, registerOnly):
        self.logger = Logger("zeroconf mDNS")
        self.callback = callbackMethod
        self.registerOnly = registerOnly
        self.records = {}
        self.nameMap = {}
        self._resolve_queue = queue.Queue()

    def add_service(self, zeroconf, srv_type, name):
        self._resolve_queue.put((srv_type, name, zeroconf))
        resolveThread = Thread(target=self._resolve_service_details)
        resolveThread.daemon = True
        resolveThread.start()

    def _resolve_service_details(self):
        threadParameters = self._resolve_queue.get()
        srv_type = threadParameters[0]
        name = threadParameters[1]
        zeroconf = threadParameters[2]
        info = zeroconf.get_service_info(srv_type, name)
        if info is not None:
            self._update_record(srv_type, name, info)
            self._respondToClient(name, "add", info)
        self._resolve_queue.task_done()

    def _update_record(self, srv_type, name, info):
        try:
            self.records[srv_type][name] = info
        except KeyError:
            self.records[srv_type] = {}
            self.records[srv_type][name] = info

    def remove_service(self, zeroconf, srv_type, name):
        info = self.records[srv_type].pop(name)
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
            "type": info.type,
            "name": info.name,
            "port": info.port,
            "hostname": info.server.rstrip("."),
            "address": inet_ntoa(info.address),
            "txt": info.properties
        }
