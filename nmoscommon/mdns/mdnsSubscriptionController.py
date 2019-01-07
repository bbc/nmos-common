from zeroconf_monkey import Zeroconf
from .mdnsSubscription import MDNSSubscription


class MDNSSubscriptionController(object):

    def __init__(self):
        self.zeroconf = Zeroconf()
        self.subscriptions = []

    def addSubscription(self, listener, regtype):
        subscription = MDNSSubscription(self.zeroconf, listener, regtype)
        self.subscriptions.append(subscription)

    def close(self):
        for sub in self.subscriptions:
            sub.close()
        self.subscriptions = []
        self.zeroconf.close()
