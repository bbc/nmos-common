#!/usr/bin/env python
from zeroconf import ServiceBrowser, Zeroconf
from ..logger import Logger
import socket


class DNSSDException(Exception):
    pass


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
        callbackBuilder = ClientCallbackBuilder(
            name, type, action, self.logger
        )
        callbackData = callbackBuilder.getClientCallback()
        self.logger.writeDebug("mDNS Service {}: {}".format(action, callbackData))
        self.callback(callbackData)


class ClientCallbackBuilder(object):

    def __init__(self, name, type, action, logger):
        self.name = name
        self.type = type
        self.action = action
        self.logger = logger

    def getClientCallback(self):
        self.callbackObject = {}
        self._initCallbackObject()
        self._processmDNSNameField()
        return self.callbackObject

    def _initCallbackObject(self):
        self.callbackObject['type'] = self.type
        self.callbackObject['action'] = self.action

    def _processmDNSNameField(self):
        infoArray = self.name.split("_")
        try:
            self.callbackObject["name"] = infoArray[1]
            self.callbackObject["ip"] = self._reverseDNSLookup(infoArray[1]),
            self.callbackObject["port"] = infoArray[2]
        except IndexError:
            self.logger.writeError("Could not decode mDNS response{}".format(name))
            raise DNSSDException

    def _reverseDNSLookup(self, hostname):
        return socket.gethostbyaddr()


class MDNSSubscription(object):

    def __init__(self, zeroconf, listener, regtype):
        self.listener = listener
        self.regtype = regtype
        self.zeroconf = zeroconf
        self.browser = ServiceBrowser(zeroconf, regtype, listener)

    def close(self):
        self.browser.cancel()


class MDNSEngine(object):

    def start(self):
        self.zeroconf = Zeroconf()
        self.subscriptions = []

    def stop(self):
        self.zeroconf.close()

    def close(self):
        for sub in self.subscriptions:
            sub.close()
        self.subscriptions = []

    def run(self):
        pass

    def register(self, name, regtype, port, txtRecord=None, callback=None):
        pass

    def update(self, name, regtype, txtRecord=None):
        pass

    def unregister(self, name, regtype):
        pass

    def callback_on_services(self, regtype, callback, registerOnly=True, domain=None):
        listener = DNSListener(callback, registerOnly)
        subscription = MDNSSubscription(self.zeroconf, listener, regtype)
        self.subscriptions.append(subscription)
