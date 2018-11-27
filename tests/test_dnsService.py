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
from nmoscommon.mdns.dnsService import DNSService
from nmoscommon.mdns.mdnsExceptions import DNSRecordNotFound
from mock import MagicMock, patch


class testDNSService(unittest.TestCase):

    def setUp(self):
        self.serviceName = "hostname._nmos-registration._tcp.example.com."
        self.type = "_nmos-registration._tcp.example.com"
        self.port = 80
        self.ttl = 6
        self.addr = "hostname.example.com."
        self.ip = "192.168.0.1"
        self.srvRecord = "0 0 {} {}".format(self.port, self.addr)
        self.txtRecord = '"api_ver=v1.0,v1.1,v1.2" "api_proto=http"'
        self.ptrRecord = self.helper_mock_prtRecord()
        self.listener = MagicMock()
        self.removeCallback = MagicMock()
        self.logger = MagicMock()
        with patch('nmoscommon.mdns.dnsService.dnsUtils') as dns:
            with patch('nmoscommon.mdns.dnsService.socket') as socket:
                self.helper_mock_socket(socket)
                self.helper_mock_dns_utils(dns)
                self.dut = DNSService(
                    self.ptrRecord,
                    self.type,
                    self.listener,
                    self.removeCallback,
                    self.logger
                )

    def tearDown(self):
        self.dut.close()

    def helper_process_txt_record(self):
        return {
            "api_ver": "v1.0,v1.1,v1.2",
            "api_proto": "http"
        }

    def helper_mock_timer(self, timer):
        self.timer = timer
        return timer

    def helper_mock_prtRecord(self):
        record = MagicMock()
        record.to_text.return_value = self.serviceName
        return record

    def helper_mock_socket(self, socket):
        self.socket = socket

        def gethostbyname(name):
            if name == self.addr[:-1]:
                return self.ip

        self.socket.gethostbyname = gethostbyname

    def helper_mock_dns_utils(self, dns):
        self.dns = dns

        def getTXTRecordSet(name):
            txtRecord = MagicMock()
            txtRecord.__getitem__.return_value.to_text.return_value = self.txtRecord
            txtRecord.rrset.ttl = self.ttl
            if name == self.serviceName:
                return txtRecord
            else:
                return None

        dns.getTXTRecord.side_effect = getTXTRecordSet

        def getSRVRecord(name):
            srvRecord = self.srvRecord
            mock = MagicMock()
            mock.to_text.return_value = srvRecord
            if name == self.serviceName:
                return [mock]
            else:
                return None
        dns.getSRVRecord.side_effect = getSRVRecord

    def test_initialise_txt_from_records(self):
        self.assertDictEqual(self.dut.txt, self.helper_process_txt_record())

    def test_initalise_type(self):
        self.assertEqual(self.type, self.dut.type)

    def test_initialise_name(self):
        self.assertEqual(self.serviceName, self.dut.name)

    def test_initalise_port(self):
        self.assertEqual(self.port, self.dut.port)

    def test_initialise_ttl(self):
        self.assertEqual(self.ttl, self.dut.ttl)

    def test_initialise_addr(self):
        self.assertEqual(self.ip, self.dut.address)

    def test_ttl_callback_duration(self):
        with patch('nmoscommon.mdns.dnsService.Timer') as timer:
            self.helper_mock_timer(timer)
            self.dut.start()
            args, _ = self.timer.call_args
            self.assertEqual(args[0], self.ttl)

    def test_ttl_callback_update(self):
        self.port = 9000
        self.srvRecord = "0 0 9000 {}".format("hostname.example.com")
        with patch('nmoscommon.mdns.dnsService.Timer') as timer:
            with patch('nmoscommon.mdns.dnsService.dnsUtils') as dns:
                with patch('nmoscommon.mdns.dnsService.socket') as socket:
                    self.helper_mock_socket(socket)
                    self.helper_mock_dns_utils(dns)
                    self.helper_mock_timer(timer)
                    self.dut.start()
                    args, _ = self.timer.call_args
                    args[1]()
                    self.assertEqual(self.port, self.dut.port)

    def helper_remove_service(self):
        with patch('nmoscommon.mdns.dnsService.dnsUtils') as dns:
            dns.getTXTRecord.side_effect = DNSRecordNotFound
            dns.getSRVRecord.side_effect = DNSRecordNotFound
            with patch('nmoscommon.mdns.dnsService.Timer') as timer:
                self.helper_mock_timer(timer)
                self.dut.start()
                args, _ = self.timer.call_args
                args[1]()

    def test_timer_started(self):
        with patch('nmoscommon.mdns.dnsService.Timer') as timer:
            self.helper_mock_timer(timer)
            instance = MagicMock()
            timer.return_value = instance
            self.dut.start()
            self.assertTrue(instance.start.called)

    def test_remove_service_callback(self):
        self.helper_remove_service()
        self.assertTrue(self.removeCallback.called)

    def test_remove_callback_args(self):
        self.helper_remove_service()
        callbackArgs, _ = self.removeCallback.call_args
        self.assertEqual(callbackArgs[0], self.serviceName)

    def test_stop_timer(self):
        with patch('nmoscommon.mdns.dnsService.Timer') as timer:
            self.helper_mock_timer(timer)
            instance = MagicMock()
            timer.return_value = instance
            self.dut.start()
            self.dut.stop()
            self.assertTrue(instance.cancel.called)

    def test_close_listener_callback(self):
        self.dut.start()
        self.dut.close()
        self.assertTrue(self.dut.dnsListener.removeListener.called)

    def test_close_listener_callback_args(self):
        self.dut.start()
        self.dut.close()
        args, _ = self.dut.dnsListener.removeListener.call_args
        self.assertEqual(args[0], self.dut)

    def test_close_timer(self):
        with patch('nmoscommon.mdns.dnsService.Timer') as timer:
            self.helper_mock_timer(timer)
            instance = MagicMock()
            timer.return_value = instance
            self.dut.start()
            self.dut.close()
            self.assertTrue(instance.cancel.called)

    def test_stop_no_remove_service(self):
        self.dut.start()
        self.dut.stop()
        self.assertFalse(self.dut.removeCallback.called)

    def test_register_listener_on_start(self):
        self.dut.start()
        self.assertTrue(self.dut.dnsListener.addListener.called)

    def test_register_listener_on_start_args(self):
        self.dut.start()
        args, _ = self.dut.dnsListener.addListener.call_args
        self.assertEqual(args[0], self.dut)


if __name__ == "__main__":
    unittest.main()
