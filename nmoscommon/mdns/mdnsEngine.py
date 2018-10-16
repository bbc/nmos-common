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

import zeroconf
from nmoscommon.logger import Logger
from .dnsListener import DNSListener
from .mdnsCallbackHandler import MDNSAdvertisementCallbackHandler
from .mdnsRegistration import MDNSRegistration
from .mdnsExceptions import ServiceAlreadyExistsException
from .mdnsInterfaceController import MDNSInterfaceController
from .mdnsRegistrationController import MDNSRegistrationController
from .mdnsSubscriptionController import MDNSSubscriptionController


class MDNSEngine(object):

    def start(self):
        self.subscriptionController = MDNSSubscriptionController()
        self.registrationController = MDNSRegistrationController()
        self.interfaceController = MDNSInterfaceController()
        self.logger = Logger('mdns-engine')

    def stop(self):
        self.close()

    def close(self):
        self.subscriptionController.close()
        self.registrationController.close()
        self.interfaceController.close()

    def run(self):
        pass

    def register(self, name, regtype, port, txtRecord="", callback=None, interfaceIps=None):
        if not interfaceIps:
            interfaceIps = []
        interfaces = self.interfaceController.getInterfaces(interfaceIps)
        registration = MDNSRegistration(interfaces, name, regtype, port, txtRecord)
        callbackHandler = MDNSAdvertisementCallbackHandler(callback, registration)
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
        else:
            callbackHandler.entryEstablisted()

    def update(self, name, regtype, txtRecord=None):
        self.unregister(name, regtype)
        self.register(name, type, txtRecord=txtRecord)

    def unregister(self, name, regType):
        self.registrationController.removeRegistration(name, regType)

    def callback_on_services(self, regtype, callback, registerOnly=False, domain=None):
        listener = DNSListener(callback, registerOnly)
        self.subscriptionController.addSubscription(listener, regtype)


if __name__ == "__main__":
    __package__ = "nmoscommon.mdns.zeroconfEngine"

    def callback(callbackObject):
        print(callbackObject)
        # pass
    engine = MDNSEngine()
    engine.start()
    engine.callback_on_services("_nmos-node._tcp", callback)
    engine.register(
        "query_http",
        "_nmos-query._tcp",
        8080,
        {
            'pri': '200',
            'api_ver': 'v1.0',
            'api_proto': 'https'
        },
        callback,
        ["172.29.82.49", "172.29.80.118"]
    )
    try:
        input("Press enter to exit...\n\n")
    except Exception:
        pass
    finally:
        engine.close()
        engine.stop()
