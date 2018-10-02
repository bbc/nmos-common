#!/usr/bin/env python

from zeroconf import ServiceBrowser, Zeroconf


class DNSListener(object):
    pass


class MDNSEngine(object):
    def __init__(self):
        self.zeroconf = Zeroconf()

    def start(self):
        pass

    def stop(self):
        pass

    def close(self):
        pass

    def run(self):
        pass

    def register(self, name, regtype, port, txtRecord=None, callback=None):
        pass

    def update(self, name, regtype, txtRecord=None):
        pass

    def unregister(self, name, regtype):
        pass

    def callback_on_services(self, regtype, callback, registerOnly=True, domain=None):
        pass
