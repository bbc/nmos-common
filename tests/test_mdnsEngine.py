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

import unittest
import zeroconf_monkey as zeroconf
from nmoscommon.mdns import MDNSEngine
from nmoscommon.mdns.mdnsExceptions import ServiceAlreadyExistsException, InterfaceNotFoundException
from nmoscommon.mdns.mdnsExceptions import ServiceNotFoundException
from mock import MagicMock, patch


class TestMDNSEngine(unittest.TestCase):

    def setUp(self):
        self.dut = MDNSEngine()
        self.dut.registrationController = MagicMock()
        self.name = "192.168.0.1_nmos-node._tcp.local."
        self.type = "_nmos-node._tcp"
        self.port = 8080

    def _helper_build_callback_handler(self):
        callbackHandler = MagicMock()
        callbackHandler.entryCollision = MagicMock()
        callbackHandler.entryFailed = MagicMock()
        callbackHandler.entryEstablished = MagicMock()
        return callbackHandler

    def test_add_registration_handle_errors_zeroconf_collision(self):
        thrower = self.dut.registrationController.addRegistration = MagicMock()
        thrower.side_effect = zeroconf.NonUniqueNameException
        callbackHandler = self._helper_build_callback_handler()
        self.dut._add_registration_handle_errors(MagicMock(), callbackHandler)
        self.assertTrue(callbackHandler.entryCollision.called)

    def test_add_registration_handle_errors_internal_collision(self):
        thrower = self.dut.registrationController.addRegistration = MagicMock()
        thrower.side_effect = ServiceAlreadyExistsException
        callbackHandler = self._helper_build_callback_handler()
        self.dut._add_registration_handle_errors(MagicMock(), callbackHandler)
        self.assertTrue(callbackHandler.entryCollision.called)

    def test_add_registration_handle_errors_fail(self):
        thrower = self.dut.registrationController.addRegistration = MagicMock()
        thrower.side_effect = zeroconf.Error
        callbackHandler = self._helper_build_callback_handler()
        self.dut._add_registration_handle_errors(MagicMock(), callbackHandler)
        self.assertTrue(callbackHandler.entryFailed.called)

    def test_add_registration_handle_errors_ok(self):
        callbackHandler = self._helper_build_callback_handler()
        self.dut._add_registration_handle_errors(MagicMock(), callbackHandler)
        self.assertTrue(callbackHandler.entryEstablished.called)

    def test_catch_interface_exception(self):
        with patch('nmoscommon.mdns.mdnsEngine.MDNSRegistration'):
            with patch('nmoscommon.mdns.mdnsEngine.MDNSAdvertisementCallbackHandler') as callbackHandler:
                self.dut._autostart_if_required = MagicMock()
                callback = callbackHandler.return_value = MagicMock()
                self.dut._add_registration_handle_errors = MagicMock()
                callback.entryFailed = MagicMock()
                self.dut.interfaceController = MagicMock()
                self.dut.interfaceController.getInterfaces = MagicMock()
                self.dut.interfaceController.getInterfaces.side_effect = InterfaceNotFoundException
                self.dut.register(None, None, None, None)
                self.assertTrue(callback.entryFailed.called)

    """The class should roll with it if not explicitly started before registering"""
    def test_implicit_start_register(self):
        self.dut.register(
            self.name,
            self.type,
            self.port,
            {}
        )

    def test_implicit_start_update(self):
        with patch('nmoscommon.mdns.mdnsEngine.MDNSRegistrationController'):
            self.dut.update(
                self.name,
                self.type,
                txtRecord={}
            )

    def helper_mock_registration_controller(self):
        registration = MagicMock()
        registration.update = MagicMock()
        controller = MagicMock()
        controller.__getitem__.side_effect = TypeError
        controller.registrations = {self.type: {self.name: registration}}
        controller.update = MagicMock()
        return controller

    def test_update_normal(self):
        self.dut.start()
        self.dut.registrationController = self.helper_mock_registration_controller()
        regMock = self.dut.registrationController.registrations[self.type][self.name]
        self.dut.update(self.name, self.type, {})
        self.assertTrue(regMock.update.called)

    def test_update_record_not_found(self):
        self.dut.start()
        with self.assertRaises(ServiceNotFoundException):
            self.dut.update("not", "this")

    def test_disable_mdns_discover(self):
        with patch('nmoscommon.mdns.mdnsEngine.MDNSListener') as listener:
            self.dut.config = {"mdns_discover": False}
            callbackHandler = self._helper_build_callback_handler()
            self.dut._add_registration_handle_errors(MagicMock(), callbackHandler)
            listener.assert_not_called()

    def test_disable_dns_discover(self):
        with patch('nmoscommon.mdns.mdnsEngine.DNSServiceController') as controller:
            self.dut.config = {"dns_discover": False}
            callbackHandler = self._helper_build_callback_handler()
            self.dut._add_registration_handle_errors(MagicMock(), callbackHandler)
            controller.assert_not_called()


if __name__ == "__main__":
    unittest.main()
