#!/usr/bin/env python

from __future__ import absolute_import
from socket import inet_ntoa
from ...logger import Logger


class DNSListener(object):

    def __init__(self, callbackMethod, registerOnly):
        self.logger = Logger("zeroconf mDNS")
        self.callback = callbackMethod
        self.registerOnly = registerOnly

    def add_service(self, zeroconf, type, name):
        action = "add"
        self._respondToClient(zeroconf, type, name, action)

    def remove_service(self, zeroconf, type, name):
        # Called when a new mDNS service is discovered
        if not self.registerOnly:
            action = "remove"
            self._respondToClient(zeroconf, type, name, action)

    def _respondToClient(self, zeroconf, type, name, action):
        info = zeroconf.get_service_info(type, name)
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
