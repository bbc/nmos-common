#!/usr/bin/env python
from zeroconf import Zeroconf
import zeroconf
from .dnsListener import DNSListener
from .mdnsSubscription import MDNSSubscription
from .mdnsCallbackHandler import MDNSAdvertisementCallbackHandler
from.mdnsRegistration import MDNSRegistration


class ServiceAlreadyExistsException(Exception):
    pass


class ServiceNotFoundException(Exception):
    pass


class MDNSEngine(object):

    def start(self):
        self.zeroconf = Zeroconf()
        self.subscriptions = []
        self.advertisedServices = {}

    def stop(self):
        self.zeroconf.close()

    def close(self):
        self._close_all_subscriptions()
        self._close_all_services()

    def _close_all_subscriptions(self):
        for sub in self.subscriptions:
            sub.close()
        self.subscriptions = []

    def _close_all_services(self):
        for regType in self.advertisedServices:
            for name in self.advertisedServices[regType]:
                self.advertisedServices[regType][name].unRegister()
        self.advertisedServices = {}

    def run(self):
        pass

    def register(self, name, regtype, port, txtRecord="", callback=None):
        registration = MDNSRegistration(self.zeroconf, name, regtype, port, txtRecord)
        callbackHandler = MDNSAdvertisementCallbackHandler(callback, registration)
        try:
            self._add_registration_to_advertised_services(registration)
            registration.register()
        except zeroconf.NonUniqueNameException:
            callbackHandler.entryColission()
        except ServiceAlreadyExistsException:
            callbackHandler.entryColission()
        except zeroconf.Error:
            callbackHandler.entryFailed()
        else:
            callbackHandler.entryEstablisted()

    def _add_registration_to_advertised_services(self, registration):
        name = registration.name
        regtype = registration.regtype
        if registration.regtype in self.advertisedServices:
            if registration.name in self.advertisedServices[regtype]:
                raise ServiceAlreadyExistsException()
        else:
            self.advertisedServices[regtype] = {}
        self.advertisedServices[regtype][name] = registration

    def update(self, name, regtype, txtRecord=None):
        self.unregister(name, regtype)
        self.register(name, type, txtRecord=txtRecord)

    def unregister(self, name, regType):
        try:
            self.advertisedServices[regType][name].remove()
        except KeyError:
            pass
        else:
            self._remove_registration_from_advertised_services(regType, name)

    def _remove_registration_from_advertised_services(self, regtype, name):
        self.advertisedServices[regtype].pop(name)
        if self.advertisedServices[regtype] == {}:
            self.advertisedServices.pop(regtype)

    def callback_on_services(self, regtype, callback, registerOnly=False, domain=None):
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
