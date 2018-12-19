#!/usr/bin/env python
from zeroconf_monkey import ServiceBrowser


class MDNSSubscription(object):

    def __init__(self, zeroconf, listener, regtype):
        self.listener = listener
        self.regtype = regtype + ".local."
        self.zeroconf = zeroconf
        self.browser = ServiceBrowser(self.zeroconf, self.regtype, self.listener)

    def close(self):
        self.browser.cancel()
