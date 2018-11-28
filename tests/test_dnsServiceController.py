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
from nmoscommon.mdns.mdnsExceptions import DNSRecordNotFound


class TestDNSServiceController(unittest.TestCase):

    def setUp(self):
        self.callback = MagicMock()
        self.logger = MagicMock()
        self.type = "_test_service_type_.tcp_"
        self.dut = DNSServiceController(self.type, self.callback, self.logger, False)
        self.services = {"type1": "service1", "type2": "service2", "type3": "service3"}

    def tearDown(self):
        self.dut.close()

    def helper_setup_utils(self):
        self.utils.checkDNSSDActive.return_value = True
        self.utils.discoverService.return_value = self.services

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

    def helper_check_service_creation(self, call):
        ptr = call[0][0]
        self.assertIn(ptr, self.services)
        type = call[0][1]
        self.assertEqual(type, self.dut.type)
        listener = call[0][2]
        self.assertEqual(listener, self.dut.listener)
        callback = call[0][3]
        self.assertEqual(callback, self.dut._removeServiceCallback)
        logger = call[0][4]
        self.assertEqual(logger, self.dut.logger)

    def test_create_service_instances(self):
        with patch('nmoscommon.mdns.dnsServiceController.DNSListener'):
            with patch('nmoscommon.mdns.dnsServiceController.DNSService') as service:
                instance = service.return_value = MagicMock()
                self.dut._populateServices(self.services)
                self.assertTrue(service.called)
                for call in service.call_args_list:
                    self.helper_check_service_creation(call)
                self.assertTrue(instance.start.called)

    def test_close(self):
        for i in range(0, 3):
            self.dut.services[i] = MagicMock()
        self.dut.close()
        for _, service in self.dut.services.items():
            self.assertTrue(service.close.called)

    def test_remove_service_callback(self):
        self.dut.services = {"type1": MagicMock(), "type2": MagicMock(), "type3": MagicMock()}
        toRemove = self.dut.services["type2"]
        toRemove.name = "type2"
        self.dut._removeServiceCallback(toRemove)
        with self.assertRaises(KeyError):
            self.dut.services["type2"]
        self.assertTrue(toRemove.close.called)

    def test_check_for_service_updates_callback(self):
        with patch('nmoscommon.mdns.dnsServiceController.dnsUtils') as utils:
            with patch('nmoscommon.mdns.dnsServiceController.DNSService') as service:
                returnValues = ["type1", "type2", "type3"]
                mocks = {}
                for value in returnValues:
                    newMock = MagicMock()
                    newMock.name = value
                    mocks[value] = newMock

                service.side_effect = mocks.values()
                self.utils = utils
                self.helper_setup_utils()
                self.dut.services = {"type1": mocks["type1"]}
                self.dut._checkForServiceUpdatesCallback()
                self.assertDictEqual(mocks, self.dut.services)

    def test_find_callback_duration(self):
        mockServices = []
        for i in range(6, 10):
            key = "type{}".format(i)
            mockService = MagicMock()
            mockService.ttl = i
            mockService.type = key
            mockServices.append(mockService)
        with patch('nmoscommon.mdns.dnsServiceController.DNSService') as service:
            with patch('nmoscommon.mdns.dnsServiceController.dnsUtils') as utils:
                self.utils = utils
                self.helper_setup_utils()
                service.side_effect = mockServices
                with patch('nmoscommon.mdns.dnsServiceController.Timer') as timer:
                    self.dut.running = True
                    self.dut._checkForServiceUpdatesCallback()
                    time, _ = timer.call_args[0]
                    self.assertEqual(time, 3)

    def test_no_services(self):
        with patch('nmoscommon.mdns.dnsServiceController.dnsUtils') as utils:
            utils.discoverService.side_effect = DNSRecordNotFound
            with patch('nmoscommon.mdns.dnsServiceController.Timer') as timer:
                self.dut.start()
                time, _ = timer.call_args[0]
                self.assertEqual(time, 1)


if __name__ == "__main__":
    unittest.main()
