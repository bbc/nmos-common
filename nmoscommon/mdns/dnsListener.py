#!/usr/bin/env python
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
        self._respondToClient(zeroconf, type, name, action, info)

    def remove_service(self, zeroconf, type, name):
        info = self.records[type].pop(name)
        if not self.registerOnly:
            action = "remove"
            self._respondToClient(zeroconf, type, name, action, info)

    def _respondToClient(self, zeroconf, type, name, action, info):
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
