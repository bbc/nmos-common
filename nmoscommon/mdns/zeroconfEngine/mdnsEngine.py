#!/usr/bin/env python
from __future__ import absolute_import

from zeroconf import Zeroconf
from .dnsListener import DNSListener
from .mdnsSubscription import MDNSSubscription


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


if __name__ == "__main__":
    __package__ = "nmoscommon.mdns.zeroconfEngine"

    def callback(callbackObject):
        # print(callbackObject)
        pass
    engine = MDNSEngine()
    engine.start()
    engine.callback_on_services("_nmos-node._tcp", callback)
    try:
        input("Press enter to exit...\n\n")
    except Exception:
        pass
    finally:
        engine.close()
        engine.stop()
