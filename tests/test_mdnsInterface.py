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
import socket
from nmoscommon.mdns.mdnsInterface import MDNSInterface
from nmoscommon.mdns.mdnsExceptions import InterfaceNotFoundException
from mock import patch


class TestMDNSInterface(unittest.TestCase):

    def setUp(self):
        self.address = "192.168.0.1"

    """Test getting a zeroconf instance"""
    def test_init_okay(self):
        with patch('nmoscommon.mdns.mdnsInterface.Zeroconf') as zeroconf:
            zeroconf.return_value = "zeroconf"
            self.dut = MDNSInterface(self.address)
            self.assertEqual(self.dut.zeroconf, "zeroconf")

    """Test error handling a failed zeroconf open"""
    def test_init_fail(self):
        with patch('nmoscommon.mdns.mdnsInterface.Zeroconf') as zeroconf:
            zeroconf.side_effect = socket.error
            with self.assertRaises(InterfaceNotFoundException):
                MDNSInterface(self.address)


if __name__ == "__main__":
    unittest.main()
