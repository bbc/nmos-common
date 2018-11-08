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
from mock import MagicMock, patch
from nmoscommon.mdns.dnsListener import DNSListener


class TestDNSListener(unittest.TestCase):

    def setUp(self):
        self.addr = "192.168.0.1"
        self.port = "8080"
        self.type = "_nmos-registration._tcp"
        self.name = "registration_http_nmos-registration._tcp"
        self.txt = {}
        self.callbackMethod = MagicMock()
        registerOnly = False
        self.dut = DNSListener(self.callbackMethod, registerOnly)

    def helper_generate_service_info(self):
        info = MagicMock()
        info.address = self.addr
        info.port = self.port
        info.name = self.name
        info.type = self.type
        info.txt = self.txt
        return info

    def helper_generate_callback_message(self, action):
        return {
            'action': action,
            'address': self.addr,
            'txt': self.txt,
            'name': self.name,
            'type': self.type,
            'port': self.port
        }

    def test_register_service(self):
        info = self.helper_generate_service_info()
        self.dut.addListener(info)
        self.helper_test_callback("add")

    def test_remove_service(self):
        info = self.helper_generate_service_info()
        self.dut.removeListener(info)
        self.helper_test_callback("remove")

    def helper_test_callback(self, action):
        self.assertTrue(self.callbackMethod.called)
        actual, _ = self.callbackMethod.call_args
        expected = self.helper_generate_callback_message(action)
        self.assertDictEqual(expected, actual[0])

    def test_register_only(self):
        self.dut = DNSListener(self.callbackMethod, True)
        info = self.helper_generate_service_info()
        self.dut.removeListener(info)
        self.assertFalse(self.callbackMethod.called)


if __name__ == "__main__":
    unittest.main()
