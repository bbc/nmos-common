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

import zeroconf_monkey as zeroconf
from nmoscommon.logger import Logger
from nmoscommon.nmoscommonconfig import config
from .dnsServiceController import DNSServiceController
from .mdnsListener import MDNSListener
from .mdnsCallbackHandler import MDNSAdvertisementCallbackHandler
from .mdnsRegistration import MDNSRegistration
from .mdnsExceptions import ServiceAlreadyExistsException, InterfaceNotFoundException, ServiceNotFoundException
from .mdnsInterfaceController import MDNSInterfaceController
from .mdnsRegistrationController import MDNSRegistrationController
from .mdnsSubscriptionController import MDNSSubscriptionController


class MDNSEngine(object):

    def __init__(self):
        self.running = False
        self.dnsServiceControllers = []

    def start(self):
        if not self.running:
            self.logger = Logger('mdns-engine')
            self.subscriptionController = MDNSSubscriptionController()
            self.registrationController = MDNSRegistrationController()
            self.interfaceController = MDNSInterfaceController(self.logger)
            self.running = True

    def stop(self):
        self.close()

    def close(self):
        self.logger.writeDebug("MDNS Engine Closed")
        self.subscriptionController.close()
        self.registrationController.close()
        self.interfaceController.close()
        for controller in self.dnsServiceControllers:
            controller.close()
        self.running = False

    def run(self):
        pass

    def _autostart_if_required(self):
        if not self.running:
            self.start()

    def register(self, name, regtype, port, txtRecord="", callback=None, interfaceIps=None):
        self._autostart_if_required()
        callbackHandler = MDNSAdvertisementCallbackHandler(callback, regtype, name, port, txtRecord)
        if not interfaceIps:
            interfaceIps = []
        try:
            interfaces = self.interfaceController.getInterfaces(interfaceIps)
        except InterfaceNotFoundException:
            callbackHandler.entryFailed()
            return
        registration = MDNSRegistration(interfaces, name, regtype, port, txtRecord)
        self._add_registration_handle_errors(registration, callbackHandler)

    def _add_registration_handle_errors(self, registration, callbackHandler):
        try:
            self.registrationController.addRegistration(registration)
        except zeroconf.NonUniqueNameException:
            callbackHandler.entryCollision()
        except ServiceAlreadyExistsException:
            callbackHandler.entryCollision()
        except zeroconf.Error as e:
            callbackHandler.entryFailed()
            print(str(e))
        else:
            callbackHandler.entryEstablished()

    def update(self, name, regtype, txtRecord=None):
        self._autostart_if_required()
        try:
            registration = self.registrationController.registrations[regtype][name]
        except KeyError:
            self.logger.writeError("Could not update registration type: {} with name {}"
                                   " - registration not found".format(regtype, name))
            raise ServiceNotFoundException
        registration.update(name=name, regtype=regtype, txtRecord=txtRecord)

    def unregister(self, name, regType):
        self._autostart_if_required()
        self.registrationController.removeRegistration(name, regType)

    def callback_on_services(self, regtype, callback, registerOnly=True, domain=None):
        self._autostart_if_required()
        doDNSDiscover = config['dns_discover']
        domDNSDiscover = config['mdns_discover']
        if domDNSDiscover:
            listener = MDNSListener(callback, registerOnly)
            self.subscriptionController.addSubscription(listener, regtype)
        if doDNSDiscover:
            dnsServiceController = DNSServiceController(
                regtype,
                callback,
                self.logger,
                registerOnly,
                domain
            )
            dnsServiceController.start()
            self.dnsServiceControllers.append(dnsServiceController)


if __name__ == "__main__":
    __package__ = "nmoscommon.mdns.zeroconfEngine"

    def callback(callbackObject):
        print("----------------")
        print(callbackObject)
        # pass
    engine = MDNSEngine()
    engine.start()
    engine.callback_on_services("_nmos-node._tcp", callback, domain=None)
    """engine.register(
        "registration_http",
        "_nmos-registration._tcp",
        8080,
        {
            'pri': 200,
            'api_ver': 'v1.0',
            'api_proto': 'https'
        },
        callback,
        ["172.29.82.49", "172.29.80.118", "127.0.0.1"]
    )"""
    try:
        input("Press enter to update registration...\n\n")
    except Exception:
        pass
    finally:
        # engine.update("registration_http", "_nmos-registration._tcp", {"test": "text"})
        try:
            input("Press enter to exit...\n\n")
        except Exception:
            pass
        finally:
            engine.stop()
