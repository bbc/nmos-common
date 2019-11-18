#!/usr/bin/env python
from threading import Timer
from zeroconf_monkey import ServiceBrowser


class MDNSSubscription(object):

    def __init__(self, zeroconf, listener, regtype):
        self.listener = listener
        self.regtype = regtype + ".local."
        self.zeroconf = zeroconf
        self._scheduleCallback()
        self.browser = ServiceBrowser(self.zeroconf, self.regtype, self.listener)

    def _scheduleCallback(self):
        self.timer = Timer(3600, self._garbageCollect)
        self.timer.start()

    def _garbageCollect(self):
        self.listener.garbageCollect(self.zeroconf, self.regtype)
        self._scheduleCallback()

    def close(self):
        if self.timer:
            self.timer.cancel()
        self.browser.cancel()
