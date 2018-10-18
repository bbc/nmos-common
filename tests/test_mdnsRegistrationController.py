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
from mock import MagicMock
from nmoscommon.mdns.mdnsRegistrationController import MDNSRegistrationController
from nmoscommon.mdns.mdnsExceptions import ServiceAlreadyExistsException, ServiceNotFoundException


class TestMDNSRegistrationController(unittest.TestCase):

    def setUp(self):
        self.dut = MDNSRegistrationController()
        self.regName = "name_nmos-test._tcp.local"
        self.regType = "nmos-test._tcp.local"

    def helper_build_registration(self):
        registration = MagicMock()
        registration.name = self.regName
        registration.regtype = self.regType
        registration.register = MagicMock()
        registration.close = MagicMock()
        return registration

    """Test adding registrations to the controller"""
    def test_add_registration(self):
        registration = self.helper_build_registration()
        self.dut.addRegistration(registration)
        self.assertEqual(self.dut.registrations[self.regType][self.regName], registration)
        self.assertTrue(registration.register.called)

    """Test that duplicate registrations cannot be added"""
    def test_add_duplicate_registration(self):
        registration = self.helper_build_registration()
        self.dut.registrations = {self.regType: {self.regName: {}}}
        with self.assertRaises(ServiceAlreadyExistsException):
            self.dut.addRegistration(registration)

    """Test that reigstrations can be removed from the controller"""
    def test_remove_registration(self):
        registration = self.helper_build_registration()
        self.dut.registrations[self.regType] = {}
        self.dut.registrations[self.regType][self.regName] = registration
        self.dut.removeRegistration(self.regName, self.regType)
        self.assertDictEqual(self.dut.registrations, {})
        self.assertTrue(registration.close.called)

    """Controller should raise an exception if asked to remove a non-existant reigstration"""
    def test_bad_remove_not_found_exception(self):
        with self.assertRaises(ServiceNotFoundException):
            self.dut.removeRegistration("not", "here")

    """Test closing down the controller"""
    def test_close(self):
        closeMock = MagicMock()
        closeFunc = MagicMock()
        closeMock.unRegister = closeFunc
        testStructure = {
            "a": {"c": closeMock},
            "b": {"d": closeMock},
            "e": {"e": closeMock}
        }
        self.dut.registrations = testStructure
        self.dut.close()
        self.assertEqual(closeFunc.call_count, 3)


if __name__ == "__main__":
    unittest.main()
