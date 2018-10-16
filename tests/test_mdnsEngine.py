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
import zeroconf
from nmoscommon.mdns import MDNSEngine
from nmoscommon.mdns.mdnsExceptions import ServiceAlreadyExistsException
from mock import MagicMock


class TestMDNSEngine(unittest.TestCase):

    def setUp(self):
        self.dut = MDNSEngine()
        self.dut.registrationController = MagicMock()

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
        self.assertTrue(callbackHandler.entryCollision.entryFailed)

    def test_add_registration_handle_errors_ok(self):
        callbackHandler = self._helper_build_callback_handler()
        self.dut._add_registration_handle_errors(MagicMock(), callbackHandler)
        self.assertTrue(callbackHandler.entryCollision.entryEstablished)


if __name__ == "__main__":
    unittest.main()
