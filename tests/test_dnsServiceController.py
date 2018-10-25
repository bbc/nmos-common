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
from nmoscommon.mdns.dnsServiceController import DNSServiceController


class TestDNSServiceController(unittest.TestCase):

    def setUp(self):
        self.callback = MagicMock()
        self.logger = MagicMock()
        self.type = "_test_service_type_.tcp_"
        self.dut = DNSServiceController(self.type, self.callback, self.logger, False)
        self.services = ["service1", "service2", "service3"]

    def helper_setup_utils(self):
        def discoverService(service):
            return {'serviceRecord': service}

        self.utils.checkDNSSDActive.return_value = True
        self.utils.getServiceTypes.return_value = self.services
        self.utils.discoverService = discoverService

    def test_find_dns_service(self):
        with patch('nmoscommon.mdns.dnsServiceController.dnsUtils') as utils:
            self.utils = utils
            self.helper_setup_utils()
            expected = self.services
            actual = self.dut._getDNSServices()
            self.assertEqual(actual, expected)

    def test_no_dnssd(self):
        with patch('nmoscommon.mdns.dnsServiceController.dnsUtils') as utils:
            self.utils = utils
            self.utils.checkDNSSDActive.return_value = False
            self.dut._getDNSServices()
            self.assertTrue(self.dut.logger.writeError.called)

    def test_create_service_instances(self):
        with patch('nmoscommon.mdns.dnsServiceController.DNSListener'):
            with patch('nmoscommon.mdns.dnsServiceController.DNSService') as service:
                self.dut._populateServices(self.services)
                self.assertTrue(service.called)
                for call in service.call_args_list:
                    ptr = call[0][0]
                    self.assertIn(ptr, self.services)

    def test_start(self):
        get = self.dut._getDNSServices = MagicMock()
        populate = self.dut._populateServices = MagicMock()
        expected = ["service1","service2"]
        get.return_value = expected
        self.dut.start()
        actual = populate.call_args[0][0]
        self.assertEqual(actual, expected)

    def test_close(self):
        for i in range(0, 3):
            self.dut.services.append(MagicMock())
        self.dut.close()
        for service in self.dut.services:
            self.assertTrue(service.close.called)


if __name__ == "__main__":
    unittest.main()